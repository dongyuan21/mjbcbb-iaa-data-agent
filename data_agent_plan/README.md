# data_agent_plan — Data Agent 长远规划

> 更新：2026-08-08（架构目录彻底重组）

本目录只放 **架构取舍、路线图、阶段快照 / handoff**。
不是现行规范真理源、不是运维 SOP、不是评测实现仓、不是 probe / 训练数据仓。

## 只留什么

| 留 | 不留（迁出或他窗） |
|---|---|
| [`架构/`](架构/README.md)（离线 / 在线 / 层设计） | 现行 canonical 规范 → `knowledge/agent_knowledge/governance/` |
| 总路线图与仍属方案级的设计 | 运维 SOP → `tools/runbooks/` |
| `UA决策行为沉淀/`（暂留，抬顶层未拍板） | 评测设计 / Agent Prompt → `eval/` |
| `snapshots/`（archived_snapshot / POC / handoff） | 建设台账 / 待执行计划 → `TODO/` 或 `da_assets/` |
| `ua_phase3_v2_data/`（数据挂 UA 旁，不当正文） | 对人能力说明 → `showoff/` |
| | schema probe JSON → `raw_exports/schema_probe_snapshots/`（本地、不入库） |

## 子目录

### 架构（先看）

| 目录 | 用途 |
|---|---|
| [`架构/`](架构/README.md) | **架构唯一入口**：总图 + [`离线/`](架构/离线/README.md) + [`在线/`](架构/在线/README.md) |
| [`架构/在线/L2/路由与预处理/`](架构/在线/L2/路由与预处理/README.md) | 输入形态、低置信度 fallback、多问题拆分、监控方案（SOP 在 runbooks） |

### 方案专题（仍属规划）

| 目录 | 用途 |
|---|---|
| [`UA决策行为沉淀/`](UA决策行为沉淀/README.md) | UA 决策方案 / 台账 / 阶段报告（**抬顶层：`needs_decision`，默认不迁**） |
| [`ua_phase3_v2_data/`](ua_phase3_v2_data/) | UA Phase3 v2 样本数据（否默认召回；是否随 UA 抬顶层同拍） |
| [`snapshots/`](snapshots/README.md) | archived_snapshot、POC 就绪度、历史 handoff |

schema probe 历史 JSON 在 `raw_exports/schema_probe_snapshots/`（本地归档、不入库；表卡可标 `raw_ref`）。

## 根目录保留的路线图

| 文件 | 用途 |
|---|---|
| [`DataAgent推进路线图.md`](DataAgent推进路线图.md) | 阶段路线图与设计背景 |
| [`未来DataAgent工作流规划.md`](未来DataAgent工作流规划.md) | 任务识别 → 路由 → 门禁 → 执行 → 回写 |

## 已迁出的职责

| 职责 | 新入口 |
|---|---|
| 知识库三层 / TaskRoutes / 文件系统精简治理 | [`../knowledge/agent_knowledge/governance/`](../knowledge/agent_knowledge/governance/README.md) |
| 路由修复 SOP | [`../tools/runbooks/路由修复标准操作流程.md`](../tools/runbooks/路由修复标准操作流程.md) |
| 分层人工评测计划 | [`../eval/layered_human_eval/分层人工评测与质量晋级计划.md`](../eval/layered_human_eval/分层人工评测与质量晋级计划.md) |
| E1 评测方案与 Agent Prompt | [`../eval/question_control_e1/`](../eval/question_control_e1/) |
| L3/E2 审计 Prompt | [`../eval/给Agent的L3架构与E2评测讨论Prompt.md`](../eval/给Agent的L3架构与E2评测讨论Prompt.md) |
| SQL 写作链台账 / 旁路审计 | [`../da_assets/`](../da_assets/) |
| Text2SQL 保守建设 / QuickBI 收割 | [`../TODO/`](../TODO/README.md) |
| Text2SQL 当前能力说明（对人） | [`../showoff/`](../showoff/) |
| 近期待办 | `../TODO/README.md` |
| 业务规则 / policy | `../knowledge/README.md` |
| 回归与评测实现 | `../eval/README.md` |
| 脚本与 runbook | `../tools/README.md` |

## 使用规则

1. `archived_snapshot` / `snapshot` / `handoff` **不代表当前状态**；活进展看 `TODO/`。
2. 新正式规则写 `knowledge/`；新待办写 `TODO/`；新架构取舍写回 [`架构/`](架构/README.md)。
3. 禁止在仓库根新建顶层 `engineering_artifacts/`（各知识库内层）。
