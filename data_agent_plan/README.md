# data_agent_plan — Data Agent 长远规划

本目录只放 Data Agent 的路线图、POC 就绪度、阶段快照和历史 handoff。日常执行入口已经拆到其他顶层目录，避免规划、知识、待办、工具混在一起。

## 当前职责

| 文件 | 状态 | 用途 |
|---|---|---|
| `DataAgent推进路线图.md` | historical_active | 阶段路线图和设计背景，部分任务已完成 |
| `DataAgent_Runtime架构规划.md` | framework_confirmed | Runtime 架构规划：已确认决策表、工程现状评估、成熟度雷达 |
| `文件系统精简与路由治理计划.md` | active_governance | 文件系统精简、canonical owner、Agent 默认召回与去重治理计划 |
| `TaskRoutes治理说明.md` | active_governance | task_routes 控制面、route 决策解释、误路由复盘、条件协议和验证流程 |
| `知识库三层结构规范.md` | active_governance | 三层结构唯一 canonical 定义（ai_hive / ai_ck / knowledge） |
| `未来DataAgent工作流规划.md` | future_architecture | 自然语言问题进入 DataAgent 后的任务识别、路由、门禁、执行和回写工作流 |
| `多轮对话与上下文压缩工程设计.md` | active_architecture | 多轮状态、上下文预算、L0–L4 压缩、source hash、并发/提交语义与验收门禁的统一工程设计 |
| `Text2SQL保守建设计划.md` | active_plan | Text2SQL 保守建设路线：字段证据、候选表 intake、candidate SQL 和验证边界 |
| `Text2SQL当前能力说明.md` | beginner_guide | 面向小白解释当前 Text2SQL 能力、材料落点、检索流程、数据链路和上下文加载 |
| `SQL写作链蒸馏台账.md` | distillation_complete | sql-writing-chain 蒸馏归属台账 |
| `SQL写作链旁路验证审计.md` | active_sidecar | 源包资产审计、live schema 观察、probe 优先级和门禁看护 |
| `POC01_BB美国UA_DNU拆解路线.md` | route_poc | 第一条只读 DataAgent POC 路线：BB 美国 UA DNU 下滑 media_source 贡献拆解 |
| `POC前置条件检查.md` | snapshot | POC 就绪度快照 |
| `QuickBI_SQL收割计划.md` | plan_pending_execution | Quick BI 看板 SQL 收割→verified 执行计划 |
| `用户增长Topic表缺口报告.md` | snapshot | 用户增长 Topic 表覆盖差距报告 |
| `MJ_DT与P3交接任务.md` | handoff | 历史交接材料，仅按需参考 |
| `claude_工程深度评估与下一步方向_20260702.md` | **archived_snapshot** | Claude 深度评估（07-02）；当前进展已超出本评估，见 `TODO/后续待办.md` |
| `claude_门禁机器级强制方案_20260702.md` | **archived_snapshot** | 门禁机器级强制方案（07-02）；当前门禁以 `tools/scripts/check_*.py` + AGENTS.md 为准 |
| `claude_模型AB评测协议_20260702.md` | **archived_snapshot** | 模型 A/B 评测协议（07-02）；待需要时再启用 |
| `上下文工程与Runtime上下文规划_已完成基线_20260628.md` | **archived_snapshot** | 上下文工程已完成基线（06-28）；当前进展见 `TODO/上下文工程与Runtime下一步规划.md` |
| `PI_Runtime_P0本地实现记录_20260628.md` | **archived_snapshot** | PI Runtime P0 本地实现记录（06-28）；P0-1/P0-3 已进入 test 运营，见 `TODO/PI Agent能力缺口小白说明.md` |
| `语义层已完成资产入口_20260628.md` | **archived_snapshot** | 语义层已完成资产归档入口（06-28）；当前待补项见 `TODO/语义层待补清单.md` |
| `user_growth_topic_schema_probe.json` | snapshot_data | 用户增长 Topic schema 探测快照 |
| `user_growth_topic_gap_precheck.json` | snapshot_data | 用户增长 Topic gap 预检查快照 |
| `kcolb_tsalb_user_label_da_schema_probe_20260616.json` | snapshot_data | BB 用户标签 schema 探测快照 |
| `sql_writing_chain_schema_probe_20260619.json` | snapshot_data | SQL 写作链 schema 探测快照 |

## 已迁出的职责

| 职责 | 新入口 |
|---|---|
| 近期待办、待问 DA/UA、语义层待补、工具待办 | `../TODO/README.md` |
| 已审核业务规则、分析规程、问题分类、周报分析提示 | `../knowledge/README.md` |
| 本地 agent skill | `../skills/README.md` |
| R1-R8 agent 回归 | `../eval/README.md` |
| 脚本和命令手册 | `../tools/README.md` |

## 使用规则

1. 标 `archived_snapshot` 的文件是历史时间点记录，**不代表当前状态**；当前进展以 `TODO/` 下的活文档为准。
2. 标 `snapshot` / `handoff` / `snapshot_data` 的同样不代表最新口径。
3. 新的正式规则优先写入 `knowledge/`，新的待办写入 `TODO/`。
4. 新路线图或架构取舍才写回本目录。
