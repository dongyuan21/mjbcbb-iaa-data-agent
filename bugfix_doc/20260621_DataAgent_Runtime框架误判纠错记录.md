# 20260621 DataAgent Runtime 框架误判纠错记录

> 记录日期：2026-06-21
> 范围：Data Agent Runtime 的 Agent 框架选型与文档口径
> 状态：已闭环（corrected）

## 一、问题

此前文档和实现中曾把 Agent 框架写成旧 Python Agent 方案。该判断已废弃：Runtime 的 Agent 框架主线是 **PI Framework**（TypeScript / Node Agent toolkit，提供 agent loop、RPC/SDK、TUI 和事件流），不是旧 Python Agent 方案。

Python FastAPI 只承担：Web API、SSE 事件桥接、MySQL 持久化、公司配置和凭据加载、MC/CK helper 适配。Runtime 接入方式是 Python FastAPI 通过 `pi --mode rpc --no-session` 的 JSONL RPC 调用 PI。

## 二、解决方案

已执行修正：

- `data_agent_plan/DataAgent_Runtime架构规划.md`、`runtime/README.md`、`runtime/本地启动说明.md` 改为 PI Framework 主线。
- `runtime/backend` 删除旧 Python Agent 适配和旧 loop 主线；`runtime/pi/` 加入本地 PI 包依赖。

## 三、后续要求

1. 后续所有 Runtime 文档必须把 PI 作为唯一 Agent 框架主线。
2. 如需 Python 数据模型，可继续使用 Pydantic BaseModel，但不得称为 Agent 框架。
3. PI 接公司 LiteLLM 网关需通过 PI 的 `models.json` / `auth.json` / SDK override 完成，不得误用 OpenAI 官方默认 baseUrl。
4. 未完成 PI 网关配置前，不得声称 PI E2E 已真实接通公司模型。

## 四、方法论沉淀

1. **Agent 框架与 Web 框架职责分离**：PI 负责 agent loop 和工具调用，FastAPI 负责 Web/持久化/凭据适配，不混为一谈。
2. **文档口径要随选型定稿同步**：选型一旦定稿，所有规划/README/启动说明必须同步，不能留旧方案描述误导后续开发。
