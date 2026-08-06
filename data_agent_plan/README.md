# data_agent_plan — Data Agent 长远规划

本目录只放 Data Agent 的路线图、POC 就绪度、阶段快照和历史 handoff。日常执行入口已经拆到其他顶层目录，避免规划、知识、待办、工具混在一起。

## 子目录（专题归档）

| 目录 | 用途 |
|---|---|
| [`UA决策行为沉淀/`](UA决策行为沉淀/README.md) | UA 决策行为沉淀方案、任务书、阶段报告、台账；Phase3 数据见 `ua_phase3_v2_data/` |
| [`Runtime控制面架构/`](Runtime控制面架构/README.md) | 当前 Runtime 六层主链、两类横切面、控制权和冻结边界 |
| [`schema_probe_snapshots/`](schema_probe_snapshots/README.md) | 历史 schema / gap probe JSON 快照（不进默认召回） |
| [`snapshots/`](snapshots/README.md) | 工程评估 / 已完成基线等 **archived_snapshot**（不代表当前状态） |

## 当前职责

| 文件 | 状态 | 用途 |
|---|---|---|
| `DataAgent推进路线图.md` | historical_active | 阶段路线图和设计背景，部分任务已完成 |
| `探索型异步Agent架构方案.md` | active_architecture / implementation_complete_ab_pending | 探索型异步 Agent：控制面与工具实现已落地，真实 off/on A/B 和灰度见 `TODO/探索型异步Agent实施.md` |
| `文件系统精简与路由治理计划.md` | active_governance | 文件系统精简、canonical owner、Agent 默认召回与去重治理计划 |
| `TaskRoutes治理说明.md` | active_governance | task_routes 控制面、route 决策解释、误路由复盘、条件协议和验证流程 |
| `知识库三层结构规范.md` | active_governance | 三层结构唯一 canonical 定义（ai_hive / ai_ck / knowledge） |
| `未来DataAgent工作流规划.md` | future_architecture | 自然语言问题进入 DataAgent 后的任务识别、路由、门禁、执行和回写工作流 |
| `多轮对话与上下文压缩工程设计.md` | active_architecture | 多轮状态、上下文预算、L0–L4 压缩、source hash、并发/提交语义与验收门禁的统一工程设计 |
| `Text2SQL保守建设计划.md` | active_plan | Text2SQL 保守建设路线：字段证据、候选表 intake、candidate SQL 和验证边界 |
| `低置信度Fallback与路由监控方案.md` | active_plan | 路由低置信度 fallback 通道、search_catalog 工具、route 命中率监控与长尾治理 |
| `多问题拆分与跨路由组合方案.md` | active_plan | 多问题捆绑拆分（Question Decomposition）和复杂单问题跨路由知识组合（Primary + Secondary Read） |
| `输入形态全景与路由预处理方案.md` | active_plan | 10+ 种用户输入形态全景图、Layer 0-4 预处理流水线、模糊澄清/元问题/What-if/大段前缀/写操作拦截 |
| `路由监控数据驱动迭代方案.md` | active_plan | 基于 trace 数据的路由质量聚合、低分 case 回收、诊断决策树、修复 SOP 和 answer quality 反向关联 |
| `路由修复标准操作流程.md` | active | 路由周报发现异常后的标准修复 SOP：诊断决策树、4 类修复操作（trigger/signal/booster/new route）、answer quality 矩阵修复方向、验证清单 |
| `路由增强灰度配置与阈值校准方案.md` | active | 路由增强功能灰度策略（4 阶段）、监控数据收集、阈值校准流程、回滚方案 |
| `分层人工评测与质量晋级计划.md` | planned | 六层人工评测、双审仲裁、评测题集、质量晋级门和修复回流计划 |
| `Text2SQL当前能力说明.md` | beginner_guide | 面向小白解释当前 Text2SQL 能力、材料落点、检索流程、数据链路和上下文加载 |
| `SQL写作链沉淀台账.md` | distillation_complete | sql-writing-chain 沉淀归属台账 |
| `SQL写作链旁路验证审计.md` | active_sidecar | 源包资产审计、live schema 观察、probe 优先级和门禁看护 |
| `POC01_BB美国UA_DNU拆解路线.md` | route_poc | 第一条只读 DataAgent POC 路线：BB 美国 UA DNU 下滑 media_source 贡献拆解 |
| `POC前置条件检查.md` | snapshot | POC 就绪度快照 |
| `QuickBI_SQL收割计划.md` | plan_pending_execution | Quick BI 看板 SQL 收割→verified 执行计划 |
| `用户增长Topic表缺口报告.md` | snapshot | 用户增长 Topic 表覆盖差距报告 |
| `MJ_DT与P3交接任务.md` | handoff | 历史交接材料，仅按需参考 |
| `P1-3模型Resolver工程计划.md` | active_plan | 模型 Resolver 工程计划 |

## 已迁出的职责

| 职责 | 新入口 |
|---|---|
| UA 决策行为沉淀全套文档与 run 产物 | [`UA决策行为沉淀/`](UA决策行为沉淀/README.md) |
| schema / gap probe JSON 快照 | [`schema_probe_snapshots/`](schema_probe_snapshots/README.md) |
| archived_snapshot（评估快照 / 已完成基线） | [`snapshots/`](snapshots/README.md) |
| 近期待办、待问 DA/UA、语义层待补、工具待办 | `../TODO/README.md` |
| 已审核业务规则、分析规程、问题分类、周报分析提示 | `../knowledge/README.md` |
| 本地 agent skill | `../skills/README.md` |
| R1-R8 agent 回归 | `../eval/README.md` |
| 脚本和命令手册 | `../tools/README.md` |

## 使用规则

1. 标 `archived_snapshot` 的文件是历史时间点记录，**不代表当前状态**；当前进展以 `TODO/` 下的活文档为准。
2. 标 `snapshot` / `handoff` / `snapshot_data` 的同样不代表最新口径。
3. 新的正式规则优先写入 `knowledge/`，新的待办写入 `TODO/`。
4. 新路线图或架构取舍才写回本目录根下；UA 沉淀专题写到 `UA决策行为沉淀/`，probe JSON 写到 `schema_probe_snapshots/`，阶段性评估快照写到 `snapshots/`。
