# data_agent_plan — Data Agent 长远规划

本目录只放 Data Agent 的路线图、POC 就绪度、阶段快照和历史 handoff。日常执行入口已经拆到其他顶层目录，避免规划、知识、待办、工具混在一起。

## 当前职责

| 文件 | 状态 | 用途 |
|---|---|---|
| `DataAgent推进路线图.md` | historical_active | 阶段路线图和设计背景，部分任务已完成 |
| `文件系统精简与路由治理计划.md` | active_governance | 文件系统精简、canonical owner、Agent 默认召回与去重治理计划 |
| `未来DataAgent工作流规划.md` | future_architecture | 自然语言问题进入 DataAgent 后的任务识别、路由、门禁、执行和回写工作流 |
| `Text2SQL保守建设计划.md` | active_plan | Text2SQL 保守建设路线：字段证据、候选表 intake、candidate SQL 和验证边界 |
| `上下文工程与Runtime上下文规划_已完成基线_20260628.md` | completion_archive | 上下文压缩与 Runtime 上下文工程的阶段性基线、PI 角色边界与已完成压缩清单 |
| `Text2SQL当前能力说明.md` | beginner_guide | 面向小白解释当前 Text2SQL 能力、材料落点、检索流程、数据链路和上下文加载 |
| `POC01_BB美国UA_DNU拆解路线.md` | route_poc | 第一条只读 DataAgent POC 路线：BB 美国 UA DNU 下滑 media_source 贡献拆解 |
| `PI_Runtime_P0本地实现记录_20260628.md` | implementation_record | PI Runtime P0 本地实现与验收记录；test 环境 replay 仍需另行通过 |
| `语义层已完成资产入口_20260628.md` | completion_archive | 语义层已完成资产入口清单与归档指针 |
| `QuickBI_SQL收割计划.md` | plan_pending_execution | Quick BI 看板 SQL 收割→verified 执行计划（2026-06-17 执行） |
| `POC前置条件检查.md` | snapshot | POC 就绪度快照 |
| `用户增长Topic表缺口报告.md` | snapshot | 用户增长 Topic 表覆盖差距报告 |
| `user_growth_topic_schema_probe.json` | snapshot_data | 用户增长 Topic schema 探测快照 |
| `user_growth_topic_gap_precheck.json` | snapshot_data | 用户增长 Topic gap 预检查快照 |
| `MJ_DT与P3交接任务.md` | handoff | 历史交接材料，仅按需参考 |

## 已迁出的职责

| 职责 | 新入口 |
|---|---|
| 近期待办、待问 DA/UA、语义层待补、工具待办 | `../TODO/README.md` |
| 已审核业务规则、分析规程、问题分类、周报分析提示 | `../knowledge/README.md` |
| 本地 agent skill | `../skills/README.md` |
| R1-R8 agent 回归 | `../eval/README.md` |
| 脚本和命令手册 | `../tools/README.md` |

## 使用规则

1. 这里的 `snapshot` / `handoff` 不代表最新口径。
2. 新的正式规则优先写入 `knowledge/`，新的待办写入 `TODO/`。
3. 新路线图或架构取舍才写回本目录。
