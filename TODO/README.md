# TODO — 近期闭环事项

本目录是最近要完成、要问人、要补证据、要拍板事项的唯一入口。这里不是事实库，事项完成后应迁入 `knowledge/`、`da_assets/`、`knowledge/agent_knowledge/semantic_contract/`、`ai_hive/` 或 `ai_ck/`。

## 文件

| 文件 | 用途 |
|---|---|
| `下周给DA的问题.md` | 合并后的 DA 问题清单：会议向问题 + 回归驱动补充问题 |
| `下周给UA的问题.md` | 合并后的 UA 问题清单：会议向问题 + 回归驱动补充问题 |
| `下周给风控与算法owner的问题.md` | 治理阈值补齐：风控黄线(风控)、ROI 下修 buffer(算法)、爬坡优势量化(DA/业务) |
| `语义层待补清单.md` | 语义层待补、已确认口径、待拍板问题 |
| `工具建设待办.md` | Google Ads / Meta 等外部工具建设 TODO，以及分析前主动提问清单 |
| `数据底座维护Harness.md` | 全局数据底座维护 harness 草案；CK/Hive adapter 已就绪，已通过低风险 Hive、CK drift、candidate/verified SQL、knowledge 正/负向召回和 semantic governance 真实变更验证，待 Hive/CK 深卡、join、默认选表或 PII 边界验证后再迁正式 runbook |
| `周报问题积压清单.md` | 周报问题池，按优先级转 SQL / SOP / case |
| `2026-06-19_待人拍板清单.md` | 明天会议用：AI 已整理但需要 DA/UA/风控/算法/产品 owner 拍板的集中清单 |
| `后续待办.md` | 后续自动化和闭环层 TODO，不是当前事实口径 |
| `DataAgent只读Runtime_POC.md` | 只读 DataAgent runtime POC 清单：触发条件已满足，消费现有控制面(路由图 + task_routes + 门禁)，独立排期 |

## 状态规则

- 需要 DA/UA 或用户拍板的问题标 `needs_decision`，不要替人决定。
- 已确认口径迁入 `knowledge/` 或对应表卡，不长期留在 TODO。
- 可复用 SQL 迁入 `da_assets/verified_sql/`，流程迁入 `da_assets/analysis_sop/`，有动作和后验的沉淀到 `da_assets/decision_cases/`。
