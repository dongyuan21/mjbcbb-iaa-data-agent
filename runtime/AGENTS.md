# Agent guide · Data Agent Runtime

> 本文件是给 AI agent（Codex / Claude Code）看的代码操作手册，不重复 README。
> 父级规则继承自 `../AGENTS.md`（数仓知识库全局约定），本文件只列 runtime/ 专属硬规则。

## 硬规则

1. **FastAPI 后端代码只放在 `runtime/backend/app/`**，不在 `runtime/` 根目录裸放 `.py`。
2. **PI Agent 每次请求 spawn 新进程**：`pi --mode rpc --no-session`，通过 JSONL stdin/stdout 交互。不要假设进程内状态跨请求保留。
3. **工具调用走 bash → `runtime/tools/data_query.py`**，不回调 FastAPI HTTP。MC/CK 查询必须经过 `data_query.py` 的只读封装。
4. **MySQL 表前缀统一 `data_agent_`**，新表必须走 Alembic 迁移（`cd runtime/backend && alembic revision -m "描述"`）。
5. **Secret 不入仓**：`LLM_GATEWAY_API_KEY`、MySQL 密码、MC/CK 凭证等一律通过环境变量或 `.env.local`（0600、gitignored）注入。
6. **部署前检查**：改 `backend/app/services/` 或 `backend/app/models.py` 后必须跑 `cd runtime/backend && uv run --extra dev pytest -q`。
7. **PI 模型配置在 `runtime/pi/agent/models.json`**，provider 固定 `hs-litellm`，apiKey 从 `LLM_GATEWAY_API_KEY` 环境变量读取。

## 项目结构速查

```
runtime/
├── backend/app/
│   ├── main.py              # FastAPI 入口 + 路由注册
│   ├── models.py            # SQLAlchemy 模型（data_agent_* 表）
│   ├── schemas.py           # Pydantic 请求/响应模型
│   ├── config.py            # 环境变量 → Settings
│   ├── services/            # 业务逻辑（agent / auth / knowledge / persistence / executors …）
│   └── workers/             # PI Worker + Freshness Worker
├── frontend/src/             # React + Vite 对话 UI
├── pi/agent/                 # Node.js PI Agent 框架
├── tools/data_query.py       # MC/CK 只读查询脚本（PI 通过 bash 调用）
└── deploy/k8s/               # K8s 部署模板
```

## 关键约定

- **认证**：`DATA_AGENT_AUTH_MODES` 控制通道（`sso` / `sso,machine`），machine HMAC 仅 test/local 可用。
- **SSE 持久化**：job events 以 MySQL `data_agent_job_events` 为权威，Redis 只做唤醒和传输，不是事件历史。
- **Worker fencing**：PI Worker 通过 `data_agent_job_leases` 做租约互斥，同一 job 只能一个 worker claim 成功。
- **测试**：`cd runtime/backend && uv run --extra dev pytest -q`，覆盖 auth / job / SSE / PI / lease / SLA 等。
