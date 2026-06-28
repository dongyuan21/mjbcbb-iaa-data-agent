# Data Agent Runtime

> 状态：phase0_scaffold
> 边界：本目录是 Data Agent 的 Web Runtime 源码，不沉淀业务事实；业务知识仍以仓库根目录的 `AGENT_RETRIEVAL_MAP.yaml`、`task_routes/`、`da_assets/`、`ai_hive/`、`ai_ck/` 和 `knowledge/` 为准。

## 目标

`runtime/` 按 `data_agent_plan/DataAgent_Runtime架构规划.md` 落地中心化 Web 服务脚手架：

- 后端：FastAPI + SSE + PI RPC Agent 框架 + Pydantic 数据模型。
- 前端：React + Vite 对话式 UI。
- 持久化：MySQL + SQLAlchemy 2.0 + Alembic。
- 执行器：MaxCompute helper 与 ClickHouse helper 的只读封装（`executors.py` 强制 read-only）。
- 配置：LLM / MySQL 走真实配置；SSO、OSS、钉钉在当前阶段为 mock/no-op。

## Agent 框架：PI

本 Runtime 的 Agent 框架是 **PI**（earendil-works/pi），TypeScript/Node 实现的 agent loop 框架。

- 包名：`@earendil-works/pi-coding-agent`
- 集成方式：Python FastAPI **每次请求 spawn** `pi --mode rpc --no-session`，通过 JSONL stdin/stdout 交互。
- PI 的 RPC 事件（`turn_start/message_update/tool_execution_*`）被 `pi_agent.py` 映射为前端 SSE 事件。

### 集成架构

```
用户问题 → FastAPI
  → KnowledgeRouter（路由 + verified SQL / 表卡 / 策略内容注入）
  → spawn PI subprocess（Node.js RPC）
    → bash tool → runtime/tools/data_query.py（独立脚本，不回调 FastAPI）
      ├── MC helper → MaxCompute
      └── CK helper → ClickHouse
    → PI 生成最终回答
  → FastAPI 解析 PI JSONL events → SSE（含 heartbeat + event ID） → 前端
```

**Phase 0 已知局限**（Phase 1 解决）：

- **进程级隔离**：每请求 spawn 新 PI 进程，无跨轮次上下文保持。Phase 1 计划改为 PI 长驻进程。

### 安装本地 PI CLI

```bash
cd runtime/pi
npm install
npm run check
```

PI 配置位于 `runtime/pi/agent/models.json`：

- provider：`hs-litellm`
- model：`deepseek-reasoner`
- baseUrl：`https://llm-gateway-internal.hs99.vip/v1`
- apiKey：从环境变量 `LLM_GATEWAY_API_KEY` 读取，不写入仓库

## 快速预检

本地启动完整流程见 `runtime/本地启动说明.md`。

本地调试可以复用现有配置源：

```bash
cd runtime/backend
python -m app.preflight
```

默认读取（本地开发路径，生产环境由 K8s Secret 注入）：

- LLM：从 `creative-video-agent/.env` 读取 `LLM_GATEWAY_API_KEY`
- MySQL：从 `pgp-platform/.scratch/mysql` 解析连接信息
- MC helper：`~/.maxcompute-dataworks/bin/maxcompute_sql.py`
- CK helper：`~/.clickhouse-shucang/bin/clickhouse_sql.py`

ClickHouse 优先支持 native 直连；设置以下变量后 Runtime 会绕过本机 CK helper：

```bash
CLICKHOUSE_HOST=...
CLICKHOUSE_PORT=9000
CLICKHOUSE_DATABASE=shucang_market
CLICKHOUSE_USERNAME=...
CLICKHOUSE_PASSWORD=...
CLICKHOUSE_PROTOCOL=native
CLICKHOUSE_TLS=false
```

## 启动

```bash
cd runtime/backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
cd runtime/frontend
npm install
npm run dev
```

## Docker 构建

Dockerfile 位于**数仓仓根** `Dockerfile`（对齐 creative-video-agent / pgp-platform 的 DeployerV2 仓根约定）：

```bash
cd /Users/lidongyuan/hungrystudio/点位/数仓
docker build -t data-agent-runtime:test .
```

镜像内含：Python backend + Node.js PI + 前端 dist + Agent 知识库 + 内置 `runtime/tools/maxcompute_sql.py`。

本地 docker-compose 基建不入仓；见 `.gitignore`。

## AgentProvider

后端入口 `/api/chat` 与 `/api/chat/stream` 保持不变，内部通过 `AgentProvider` 选择执行器：

- `pi`：默认执行器，保留现有 PI RPC、工具 trace、SQL evidence 和 query_records 落库能力。
- `hermes`：远端 Hermes 执行器，默认被硬短路到 `pi`；只有显式设置 `DATA_AGENT_HERMES_PROVIDER_ENABLED=true` 且配置 `DATA_AGENT_HERMES_BRIDGE_URL` 后才可用。支持两种模式：
  - `contract`：DataAgent 自定义 provider contract。
  - `openai`：HermesAgent 官方 API Server 的 `/v1/chat/completions`。

常用配置：

```bash
DATA_AGENT_PROVIDER=pi
DATA_AGENT_PROVIDER_ROUTES=
DATA_AGENT_HERMES_PROVIDER_ENABLED=false
DATA_AGENT_HERMES_BRIDGE_URL=
DATA_AGENT_HERMES_BRIDGE_API_KEY=
DATA_AGENT_HERMES_BRIDGE_MODE=contract
DATA_AGENT_HERMES_MODEL=hermes-agent
DATA_AGENT_HERMES_BRIDGE_TIMEOUT_SEC=900
DATA_AGENT_HERMES_BRIDGE_STREAM=true
```

同实例模式下 `DATA_AGENT_HERMES_BRIDGE_API_KEY` 可以留空；启动脚本会生成一次强随机 key，并同时注入 Hermes API Server 与 DataAgent provider。接独立远端 Hermes API Server 时应显式配置该 key。

`DATA_AGENT_HERMES_BRIDGE_STREAM=true`（默认）时，`openai` 模式走 Hermes **Runs API**（`POST /v1/runs` + `GET /v1/runs/{id}/events`），会等 agent loop 跑完再返回最终答案，并把 `tool.started` / `tool.completed` 转成前端过程日志；`contract` 模式仍是一次性 HTTP 返回。

### 同实例 Hermes MVP

单实例模式会在同一个容器内启动两个进程：

- DataAgent Runtime：`8000`
- HermesAgent API Server：`127.0.0.1:8642`

推荐 test 配置：

```bash
DATA_AGENT_PROVIDER=hermes
DATA_AGENT_HERMES_PROVIDER_ENABLED=true
DATA_AGENT_HERMES_BRIDGE_MODE=openai
DATA_AGENT_HERMES_BRIDGE_URL=http://127.0.0.1:8642
DATA_AGENT_HERMES_MODEL=hermes-agent
DATA_AGENT_EMBEDDED_HERMES_ENABLED=true
DATA_AGENT_EMBEDDED_HERMES_HOST=127.0.0.1
DATA_AGENT_EMBEDDED_HERMES_PORT=8642
DATA_AGENT_HERMES_INFERENCE_MODEL=qwen3.7-max
DATA_AGENT_HERMES_INFERENCE_API_MODE=chat_completions
```

`DATA_AGENT_EMBEDDED_HERMES_TOOLSETS` 默认空，表示 API Server 先不开放 terminal/file/browser 等工具。需要逐步放开时使用逗号分隔，例如 `skills,todo,memory`。

接独立 HermesAgent 官方 API Server 时，只需把 `DATA_AGENT_HERMES_BRIDGE_URL` 指向远端服务并关闭 `DATA_AGENT_EMBEDDED_HERMES_ENABLED`。

`DATA_AGENT_PROVIDER_ROUTES` 支持按路由切换，例如 `roi_or_campaign_analysis:hermes,sql_review:pi`。默认情况下，所有 `hermes` 路由都会短路回 `pi`；只有 `DATA_AGENT_HERMES_PROVIDER_ENABLED=true` 时才真的走 Hermes。Hermes 返回仍需遵守 Data Agent 的只读分析和证据链契约，后端会把 `agent_provider`、`provider_run_id`、`provider_version`、`bridge_mode` 写入 trace。

shai远程部署见 [`runtime/shai部署Checklist.md`](shai部署Checklist.md)。

## 当前 mock 边界

- SSO：`X-Data-Agent-User` 请求头或默认 `local_user`。
- OSS/PVS：报告存储接口保留，当前不写远端对象存储。
- 钉钉：通知接口 no-op，缺配置不阻断查询流程。

这些 mock 都集中在后端服务层，后续接公司基建时替换实现即可。

## MySQL 表名前缀

Runtime 业务表统一使用 `data_agent_` 前缀：

- `data_agent_sessions`
- `data_agent_messages`
- `data_agent_query_records`
- `data_agent_reports`
- `data_agent_traces`
- `data_agent_alembic_version`
