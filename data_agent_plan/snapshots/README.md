# data_agent_plan/snapshots — 历史快照与 handoff 归档

本目录只放**时间点快照**、POC 就绪度与历史 handoff，**不代表当前状态**。

**平面归属**：离线归档层。总入口见 [`../架构/离线/`](../架构/离线/README.md)；活规划见 [`../README.md`](../README.md)。

| 文件 | 类型 | 当前请看 |
|---|---|---|
| `语义层已完成资产入口_20260628.md` | archived_snapshot | `TODO/语义层待补清单.md` |
| `POC01_BB美国UA_DNU拆解路线.md` | route_poc | 历史 POC 路线 |
| `POC前置条件检查.md` | snapshot | 历史就绪度 |
| `MJ_DT与P3交接任务.md` | handoff | 仅按需 |
| `用户增长Topic表缺口报告.md` | snapshot | 历史缺口；现状需 live / catalog |

规则：

1. 不进 Agent 默认召回；按需人工翻历史。
2. 新的阶段性评估快照 / handoff 写入本目录，不要堆回 `data_agent_plan/` 根。
3. 活规划、架构方案进专题子目录；现行治理规范进 `knowledge/agent_knowledge/governance/`。
4. `schema_probe_snapshots/` 正按库迁往各知识库 `engineering_artifacts/`（他窗收口中）；勿与本目录混淆。
