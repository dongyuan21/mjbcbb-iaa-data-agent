# Data Agent Runtime 框架误判纠错记录

> 状态：corrected
> 日期：2026-06-21
> 范围：Data Agent Runtime 的 Agent 框架选型与文档口径

## 结论

Data Agent Runtime 的 Agent 框架主线是 **PI Framework**，不是旧 Python Agent 方案。

- PI 仓库：`https://github.com/earendil-works/pi`
- PI 包名：`@earendil-works/pi-coding-agent`
- PI 语言/运行时：TypeScript / Node
- Runtime 接入方式：Python FastAPI 通过 `pi --mode rpc --no-session` 的 JSONL RPC 调用 PI

Python FastAPI 只承担：

- Web API
- SSE 事件桥接
- MySQL 持久化
- 公司配置和凭据加载
- MC / CK helper 适配

不得再把旧 Python Agent 方案描述为 Runtime 的目标 Agent 框架。

## 误判内容

此前文档和实现中曾把 Agent 框架写成旧 Python Agent 方案。

该判断已废弃。PI 是 earendil-works/pi，TypeScript / Node Agent toolkit，提供 agent loop、RPC/SDK、TUI 和事件流。

## 已执行修正

- `TODO/DataAgent_Runtime架构规划.md` 已改为 PI Framework。
- `data_agent_plan/DataAgent_Runtime架构规划.md` 已改为 PI Framework。
- `runtime/README.md` 已改为 PI TypeScript/Node RPC 主线。
- `runtime/本地启动说明.md` 已加入 PI 本地安装说明。
- `runtime/backend` 已删除旧 Python Agent 适配和旧 loop 主线。
- `runtime/pi/` 已加入本地 PI 包依赖。

## 后续要求

1. 后续所有 Runtime 文档必须把 PI 作为唯一 Agent 框架主线。
2. 如需 Python 数据模型，可继续使用 Pydantic BaseModel，但不得称为 Agent 框架。
3. PI 接公司 LiteLLM 网关需通过 PI 的 `models.json` / `auth.json` / SDK override 完成，不得误用 OpenAI 官方默认 baseUrl。
4. 未完成 PI 网关配置前，不得声称 PI E2E 已真实接通公司模型。
