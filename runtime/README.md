# Data Agent Runtime

> 状态：test_live_validated_readonly_runtime
> 边界：本目录是 Data Agent 的 Web Runtime 源码，不沉淀业务事实；业务知识仍以仓库根目录的 `AGENT_RETRIEVAL_MAP.yaml`、`task_routes/`、`da_assets/`、`ai_hive/`、`ai_ck/` 和 `knowledge/` 为准。

## 目标

`runtime/` 已按 `data_agent_plan/DataAgent_Runtime架构规划.md` 落地并在 test lane 验证中心化只读 Web Runtime：

- 后端：FastAPI + SSE + PI RPC Agent 框架 + Pydantic 数据模型。
- 前端：React + Vite 对话式 UI。
- 持久化：MySQL + SQLAlchemy 2.0 + Alembic。
- 执行器：MaxCompute helper 与 ClickHouse helper 的只读封装（`executors.py` 强制 read-only）。
- 配置：LLM / MySQL / MC / CK 走真实配置；共享 test 使用真实 SSO 或受限 machine auth，mock 仅允许 local/dev。

## Agent 框架：PI

本 Runtime 的 Agent 框架是 **PI**（earendil-works/pi），TypeScript/Node 实现的 agent loop 框架。

- 包名：`@earendil-works/pi-coding-agent`
- 集成方式：Python FastAPI **每次请求 spawn** `pi --mode rpc --no-session`，通过 JSONL stdin/stdout 交互。
- PI 的 RPC 事件（`turn_start/message_update/tool_execution_*`）被 `pi_agent.py` 映射为前端 SSE 事件。

### 集成架构

```
用户问题 → FastAPI POST /api/jobs
  → MySQL 单事务写入完整 request_payload / submitted event / enqueue outbox
  → API best-effort 投递；失败由 Worker outbox reconciler 补投
  → KnowledgeRouter（路由 + verified SQL / 表卡 / 策略内容注入）
  → Redis 任务队列 → PI Worker 原子 claim + lease/heartbeat/fencing
    → spawn PI subprocess（Node.js RPC）
    → bash tool → runtime/tools/data_query.py（独立脚本，不回调 FastAPI）
      ├── MC helper → MaxCompute
      └── CK helper → ClickHouse
    → PI 生成最终回答
  → MySQL 持久化 job / trace / query_records / job_events
  → GET /api/jobs/{job_id}/events?after_seq=...
    → MySQL durable events 权威续传 → SSE（heartbeat + event ID） → 前端
```

持久化任务协议：

- `POST /api/jobs` 创建持久化任务；`GET /api/jobs/{job_id}` 查询当前状态。
- job 的 `message` 字段只作 512 字符标题预览；Worker 只把版本化的完整 `request_payload` 当执行真相源。
- job、首个 `submitted` 事件和 enqueue outbox 在同一 MySQL 事务提交；Redis 临时失败不会丢任务。
- Worker 只执行自己持有的 `(lease_owner, lease_token)`；过期接管递增 token，旧 Worker 的事件、终态和答案写入会 fail-closed。
- 最终消息、trace、query record 回填、job 终态与 `answer/done/error` 事件在同一事务提交；Redis ACK 只发生在完成、已终态或不存在的 poison job。
- `GET /api/jobs/{job_id}/events?after_seq=` 从 MySQL 权威事件日志按最后连续序号续传。
- durable SSE 的 `id:` 与 MySQL event `seq` 一致；未显式传 `after_seq` 时也接受标准 `Last-Event-ID`。
- Redis 只承担任务队列和 SSE 唤醒，不是事件历史真理源，也不直接推进客户端序号。
- React 客户端在 tab 级 `sessionStorage` 保存 active job checkpoint；首次创建结果不明时复用同一 `external_message_id`，得到 `job_id` 后只恢复同一 job，不重复 POST、不重置原始 deadline。
- 为解决首次 POST 结果不明，creating checkpoint 会在当前 tab 临时保存问题正文；确认 `job_id` 后立即移除正文，终态/显式停止/tab 关闭或 SSO principal 变化时清理 checkpoint。
- 客户端要求严格连续 `seq` 和 `answer -> done -> terminal` 闭环；永久序号缺口、身份错配或不完整终态均 fail-closed。

**当前已知局限**：

- **进程级隔离**：每个 job 仍 spawn 新 PI 进程，无跨 job 的原生模型上下文保持；多轮历史压缩与 PI 长驻进程仍是后续独立实验。
- **首次迁移边界**：从不具备 durable request/lease 的旧版本升级到 `0011_job_execution_lease` 时仍须停流、排空并停止旧 Worker；完成该一次性切换后，新 Worker 才具备多副本原子 claim 与过期接管能力。
- **数据库验证边界**：SQLite 双连接离线门禁已覆盖 claim/fencing/崩溃回滚；部署前仍须在 test MySQL 用两个真实连接复跑原子 claim，不能把 SQLite 锁语义当作 MySQL 证明。
- **浏览器人工证据**：浏览器续接状态机已有离线自动化门禁；实际浏览器刷新/网络切换的 UI 证据仍需独立手工报告，不能从机器 N=3 或纯状态机单测推断。

## Test live 稳定性证据（2026-07-15）

行为提交 `54df4d8fccaa608fac94c04aaeef495ff43f92eb` 已完成 Worker env `862`、API env `811`、Freshness env `874` 三服务同提交部署和 machine-auth smoke。最终 14 条 live replay case 严格串行 N=3 共 42 次：39 PASS、3 个预期黄色 WARN、0 FAIL、0 blocked、0 flaky；114 条 query records 的 raw/effective failed 均为 0。历史失败基线保留在 `eval/pi_replay_regression/stability_baseline.yaml`，复现边界见 `TODO/PIReplay_N连跑稳定性说明.md`。

### 安装本地 PI CLI

```bash
cd runtime/pi
npm install
npm run check
```

PI 配置位于 `runtime/pi/agent/models.json`：

- provider：`hs-litellm`
- model：由 Runtime 设置从 `models.json` 的受支持列表选择；2026-07-15 最终 live N=3 实际为 `claude-sonnet-5`
- baseUrl：`https://stargate.example.com/v1`
- apiKey：从环境变量 `LLM_GATEWAY_API_KEY` 读取，不写入仓库

## 快速预检

本地启动完整流程见 `runtime/本地启动说明.md`。

Runtime 可观测证据入口为 ops-only 端点 `GET /api/runtime/sla`，它仅从 MySQL 汇总 durable job / outbox / lease / event 与 Freshness scheduled-run 元数据，不返回问题、SQL、答案或结果行。test/staging 使用 machine HMAC，local/dev 允许本机 mock；普通 SSO 不具备全局运行态权限。当前数值型 SLO 尚未由 owner 确认；详见 [`Runtime SLA证据通道.md`](Runtime%20SLA证据通道.md)。

本地调试可以复用现有配置源：

```bash
cd runtime/backend
python -m app.preflight
```

默认读取（本地开发路径，生产环境由 K8s Secret 注入）：

- LLM：从 `runtime/backend/.env` 读取 `LLM_GATEWAY_BASE_URL` / `LLM_GATEWAY_API_KEY`
- MySQL：从 `sibling-platform/.scratch/mysql` 解析连接信息
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

Dockerfile 位于**数仓仓根** `Dockerfile`（对齐 sibling-video-agent / sibling-platform 的 DeployerV2 仓根约定）：

```bash
cd /Users/<dev>/HS/点位/数仓
export DATA_AGENT_BUILD_COMMIT="$(git rev-parse HEAD)"
docker build --build-arg DATA_AGENT_BUILD_COMMIT="$DATA_AGENT_BUILD_COMMIT" -t data-agent-runtime:test .
python3 runtime/tools/verify_image_revision.py \
  --image data-agent-runtime:test --expected-commit "$DATA_AGENT_BUILD_COMMIT"
```

本机构建必须显式注入并校验完整提交。山海当前不会把任务的 resolved commit 注入 Docker
build arg，因此该构建入口保留显式 `unknown`，避免伪造 revision；山海验收以 `task detail`
中的 `git_commit` / `clone_commit` 和最终镜像 tag 为准。若平台后续支持注入，仍按上述完整
提交校验，非 `unknown` 的非法值会在镜像构建阶段失败。

镜像内含：Python backend + Node.js PI + 前端 dist + Agent 知识库 + 内置
`runtime/tools/maxcompute_sql.py` 及其 `pyodps` 运行依赖。

推荐用 [`docker-compose.local.example.yml`](docker-compose.local.example.yml) 建立本机拓扑：

```bash
cp runtime/docker-compose.local.example.yml runtime/docker-compose.yml
# 将获准使用的 LLM / MySQL / MC / CK 配置写入 ignored 且权限为 0600 的
# runtime/backend/.env.local；不要把 secret 写进 compose 或提交到 git。
# compose 使用 shell 中显式导出的完整 HEAD；不得在 .env.local 设置该变量。
export DATA_AGENT_BUILD_COMMIT="$(git rev-parse HEAD)"
docker compose -f runtime/docker-compose.yml build api
python3 runtime/tools/verify_image_revision.py \
  --image data-agent-runtime:local --expected-commit "$DATA_AGENT_BUILD_COMMIT"
docker compose -f runtime/docker-compose.yml up -d redis api worker
```

本机 API 仅绑定 `127.0.0.1:18000`，使用 `DATA_AGENT_ENV=local` 与 SSO mock；浏览器和
Codex 无需公司 SSO。允许在获授权后复用 shared test 的 LLM / MySQL / MC / CK 配置，但
Redis 必须使用 compose 内的本机隔离实例，禁止让本机 Worker 连接 shared test Redis，避免
误消费共享队列。Freshness 为一次性 profile，默认只 dry-run：

```bash
docker compose -f runtime/docker-compose.yml --profile freshness run --rm freshness
```

实际 `runtime/docker-compose.yml` 与 `.env.local` 均为机器私有文件、不入仓；见 `.gitignore`。

## AgentProvider

后端入口 `/api/chat` 与 `/api/chat/stream` 保持不变，内部通过 `AgentProvider` 选择执行器：

- `pi`：默认执行器，保留现有 PI RPC、工具 trace、SQL evidence 和 query_records 落库能力。

常用配置：

```bash
DATA_AGENT_PROVIDER=pi
DATA_AGENT_PROVIDER_ROUTES=
```

`DATA_AGENT_PROVIDER_ROUTES` 支持按路由切换，例如：

- `roi_or_campaign_analysis:pi`
- `sql_review:pi`

山海远程部署见 [`runtime/山海部署Checklist.md`](山海部署Checklist.md)。

## mock 与认证边界

- 仅 local/dev 可显式启用 SSO mock；共享 test lane 的人类用户必须走真实 SSO。DingTalk mock
  仍可按 test 配置显式开启；mock 登录仍须提供
  `DATA_AGENT_SSO_SESSION_SECRET` 来签名 cookie。
- `DATA_AGENT_AUTH_MODES` 默认 `sso`；test 的 Codex/定时任务可显式设为
  `sso,machine`，使用短时 HMAC 调用 `/api/me` 与 `/api/chat/stream`，但人类请求仍只走 SSO。
- shared test 与 prod 必须关闭 SSO/callback mock（outbound DingTalk mock 可按 test 配置显式开启），`/readyz` 与 `/api/preflight` 会检查 SSO、
  callback 和可选出站 webhook 的配置完整性。
- `/api/dingtalk/callback` 接受内部签名 bridge，不是原生 DingTalk 直连；完整配置、
  HMAC 规范和 test 模板见
  [`deploy/认证与钉钉回调配置合同.md`](deploy/认证与钉钉回调配置合同.md)。
- OSS/PVS：报告存储接口保留，当前不写远端对象存储。

这些 mock 都集中在后端服务层，后续接公司基建时替换实现即可。

## MySQL 表名前缀

Runtime 业务表统一使用 `data_agent_` 前缀：

- `data_agent_sessions`
- `data_agent_messages`
- `data_agent_query_records`
- `data_agent_reports`
- `data_agent_traces`
- `data_agent_alembic_version`
