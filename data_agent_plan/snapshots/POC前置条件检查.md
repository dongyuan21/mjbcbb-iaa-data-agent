# Agent POC 前置条件检查

> 检查日期：2026-06-14  
> 结论：可以启动**只读 POC**，不建议启动自动决策 / 自动动作。  
> 当前状态以上方自动快照为准；最新阻塞通常来自 freshness gate、DA / UA 人工确认和广告平台操作记录工具尚未接入。

<!-- 自动快照：开始 -->

> 自动快照：2026-07-02；生成脚本：`python3 tools/scripts/refresh_data_agent_snapshots.py`；来源：`eval/agent_regression/Agent回归报告.md`、`knowledge/agent_knowledge/semantic_contract/model.json`、`da_assets/index.yaml`。

| 项 | 当前值 |
|---|---|
| 问答回归 | 通过 — 11/11 cases passed, 0 freshness-blocked, knowledge 7/7 routes 17/17 golden 80/80 (门槛 10 pass_or_blocked) |
| 数据新鲜度门禁 | 正常 |
| 语义模型 | 11 个实体、38 个维度、50 个指标、3 条关联规则；16/16 个语义用例通过 |
| 表卡覆盖 | ai_hive 123 张表；ai_ck 27 张表；CK 精选表画像 55 份 |
| DA 资产 | 已验证 SQL 28 条；候选 SQL 2 条；决策记录 9 个；已闭环 1 个 |
| 北极星覆盖 | 约 16/35 个高频场景，概念覆盖率约 46% |

- 数据新鲜度门禁：正常

试点判定：只读历史窗口和成熟窗口可继续；涉及最新回收、预测或边缘分区时，必须先解除数据新鲜度阻断。

<!-- 自动快照：结束 -->

## 条件检查

| 条件 | 状态 | 说明 |
|---|---|---|
| 用户增长 Topic 表卡补齐 | 通过 | P0/P1/P2/P3 共 52 张缺口表已补入 `ai_hive`，Topic 55 张全覆盖 |
| MC↔CK 对齐 | 通过 | 顶层散文已撤销；当前入口为 `ai_ck/agent_knowledge/metrics/`、`knowledge/agent_knowledge/semantic_contract/model.json`、相关表卡和 verified SQL |
| 至少 10 条 verified SQL | 通过 | 当前数量以上方自动快照为准；`da_assets/index.yaml` 由 SQL 晋升门禁检查 |
| 至少 1 份 DA 报告/SOP 入库 | 通过 | 已沉淀 DA 钉钉文档、HTML、周同步、点位复盘、首日 ARPU、广告展示口径等 raw / SOP |
| draft_knowledge P0 审核 | 通过 | 已新增 `draft_knowledge/审核结论.md` |
| 统一机器可读语义模型 | 通过 | `knowledge/agent_knowledge/semantic_contract/` CK + MaxCompute 双源；实体 / 维度 / 指标 / 回归数以上方自动快照为准，禁止跨源 SQL join |
| 数据新鲜度 / 分区可用性 | 通过 | `ai_ck/engineering_artifacts/freshness_snapshot.json` + `ai_hive/engineering_artifacts/freshness_snapshot.json` 已覆盖 P0 表 |
| 最小回归问题集 | 条件通过 | `eval/agent_regression/run_regression.py` 已覆盖 R1-R8；资产回归通过但可能被 freshness gate 阻断 |
| 命令入口 | 通过 | `tools/runbooks/语义模型回归校验.md`、`tools/runbooks/Agent回归.md`、`tools/runbooks/ClickHouse连通与新鲜度探测.md` |
| DA / UA 人工确认清单 | 通过 | DA 已处理结论见 `knowledge/agent_knowledge/policies/DA问题已处理结论_20260628.md`；UA 待确认项见 `TODO/语义层待补清单.md`（原 `TODO/下周给DA的问题.md` 与 `TODO/下周给UA的问题.md` 已于 2026-07-14 归档） |
| 外部广告平台操作记录工具 | 未开始 | Google Ads / Meta change log 已记录在 `工具建设待办.md`，等待用户后续补代码能力 |
| 端到端 decision case | 部分闭环 | 已闭环 1 个 D7 后验 case；更多 case 仍缺广告平台操作日志、人类动作和后验 |

## 已具备能力

- 可问表：`ai_hive` 表卡数量以上方自动快照为准。
- 可问 CK：`ai_ck` 已覆盖全库 metadata、业务样例、ROI360 指标语义。
- 可跑 SQL：`maxcompute-dataworks` 和 CK native 均已验证。
- 可引用 reference SQL：verified SQL 数量以上方自动快照和 `eval/sql_promotion/SQL晋升指标报告.md` 为准。
- 可引用分析流程：已沉淀首日 ARPU 异动、MJ/DT 点位复盘、广告展示口径、LTV 倍率下降、IAA 点位测试等 SOP / raw。
- 可跑语义模型回归：`python3 knowledge/engineering_artifacts/semantic_contract/build_model.py && python3 knowledge/engineering_artifacts/semantic_contract/eval/compose_sql.py`，当前状态以上方自动快照为准。
- 可跑 R1-R8 agent 回归：`python3 eval/agent_regression/run_regression.py`，会把 delayed / stale freshness 提升为 `BLOCKED`。
- 可检查 freshness：`python3 tools/scripts/probe_freshness.py`，覆盖 CK + MaxCompute P0 表。
- 可输出只读复盘：事实、SQL、口径、freshness、风险、待确认项。

## 主要缺口

1. **freshness blocker 需要优先处理**：delayed / stale 表会阻断最新窗口结论。
2. **闭环 case 样本仍少**：已有 1 个 D7 后验闭环，但缺更多带人类动作和平台操作日志的 case。
3. **业务动作阈值仍需 UA / owner 拍板**：放量、降预算、停投、观察、数据量小样本等不能由 agent 自行决定。
4. **DA 口径仍需确认**：ROI 预测偏差成本加权、`time_range/cur_range` 过滤、素材 ROI join、点位复盘扩窗策略。
5. **广告平台操作记录工具未接入**：当前能判断“DNU 缺口来自哪个 media_source”，但不能自动判断是否由 Google Ads / Meta campaign 操作导致。

## 当前 POC 边界

### 可以开始

- 只读问答。
- 复用 verified SQL / SOP。
- 生成 SQL 草案或小窗口 SQL。
- 检查 freshness 后再解释结果。
- 输出事实、拆解、风险、候选列表、待确认项。
- 给出 `needs_decision`、`data_delay_suspected`、`missing_threshold` 等状态。

### 不可以开始

- 自动停投、放量、降预算。
- 自动修改广告平台预算 / bid / campaign 状态。
- 把 `draft` / `pending` case 当作已验证规则。
- 在阈值未结构化时输出“必须停投 / 必须放量”。
- 把 delayed / unknown 分区的数据异常直接判为真实劣化。

## 建议

可以启动只读 POC。下一步优先：

1. 用 R1 / R2 / R7 各做一次端到端只读演练。
2. 拿 `knowledge/agent_knowledge/policies/DA问题已处理结论_20260628.md`（DA 已处理结论）和 `TODO/语义层待补清单.md`（UA 待确认项）做人工确认。原 `TODO/下周给DA的问题.md` 和 `TODO/下周给UA的问题.md` 已归档。
3. 选择 2 个新 case 补齐人类动作、操作日志和 D+1/D+3/D+7 后验，扩大闭环样本。
4. 等用户补 Google Ads API 代码能力后，再启动 `工具建设待办.md` 中的 Google Ads change log 工具。
5. 如果只读 POC 在 freshness gate 下仍稳定，下一步进入自研开源 DataAgent runtime 的最小闭环实现，不再评估外部承载路线。
