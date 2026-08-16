# 架构

> 状态：`active_architecture`
> 录入：2026-08-07；重组：2026-08-08
> 归属：[`../README.md`](../README.md)

**Data Agent 架构文档唯一入口。** 路线图在 `data_agent_plan/` 根；UA 等方案专题不在此夹。

## 一句话

**离线生产信任边界；在线只消费已注册可信资产。**

## 整仓总图

| 文件 | 用途 |
|---|---|
| [`DataAgent架构-在线离线.excalidraw`](DataAgent架构-在线离线.excalidraw) | 可编辑源 |
| [`DataAgent架构-在线离线.png`](DataAgent架构-在线离线.png) | 预览；若与 excalidraw 不一致，以 excalidraw 为准并重新导出 |

![Data Agent 架构 · 在线离线](DataAgent架构-在线离线.png)

## 三块分工

```text
架构/                    ← 本目录：总图 + 索引
├── 离线/                信任怎么生产（入库、门禁、维护 OS）
└── 在线/                信任怎么消费（L1–L6、横切面、层设计）
    ├── L2/              用户问题控制、路由预处理
    ├── L3/              知识控制决策口径
    └── 横切面/          多轮、探索型 Agent、Resolver（部分未完全落地）
```

| 子目录 | 职责 | 权威正文 |
|---|---|---|
| [`离线/`](离线/README.md) | 入库、门禁、维护 OS、定时刷新 | [`离线平面职责与冻结边界.md`](离线/离线平面职责与冻结边界.md) |
| [`在线/`](在线/README.md) | 六层主链、横切面、冻结边界 | [`架构分层与冻结边界.md`](在线/架构分层与冻结边界.md) |
| [`在线/L2/`](在线/L2/) | 问题控制、路由方案 | [`用户问题控制与澄清设计.md`](在线/L2/用户问题控制与澄清设计.md) |
| [`在线/L3/`](在线/L3/) | L3 决策与施工口径 | [`重构决策口径.md`](在线/L3/重构决策口径.md) |
| [`在线/横切面/`](在线/横切面/) | 跨层能力规划 | 各方案 md；落地进度以 `TODO/` 为准 |

## 推荐阅读顺序

1. 本页总图 — 建立整仓心智模型
2. 离线 → [`离线/README.md`](离线/README.md)；在线 → [`在线/README.md`](在线/README.md)
3. 按层深入：L2 / L3 / 横切面

## 与兄弟目录

| 目录 | 关系 |
|---|---|
| [`../UA决策行为沉淀/`](../UA决策行为沉淀/README.md) | 离线专题；非 Runtime 主链 |
| [`../snapshots/`](../snapshots/README.md) | 时间点 POC / handoff |
| [`../../knowledge/agent_knowledge/governance/`](../../knowledge/agent_knowledge/governance/README.md) | 现行三层结构、TaskRoutes 治理规范 |
| [`../../da_assets/SQL晋升治理.md`](../../da_assets/SQL晋升治理.md) | SQL 晋升门禁 |
| [`../../术语解释/SQL晋升状态.md`](../../术语解释/SQL晋升状态.md) | 晋升术语速查 |
| [`../../eval/question_control_e1/`](../../eval/question_control_e1/) | E1 评测方案与 Agent 解读 Prompt |

## 硬边界（全架构共用）

- `candidate_sql`：离线持有；L3 不给模型读。
- L4 若用草案：仅代码常量 + SHA 探针，并标 `asset_status`；不进知识面。
- 跑通 ≠ 晋升；晋升只在离线 Gate。
- Runtime 不自动把本轮跑通的 SQL 写回 `verified_sql`。
