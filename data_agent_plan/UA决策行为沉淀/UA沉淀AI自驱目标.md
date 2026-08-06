# UA 操作沉淀 AI 自驱目标（Goal Mode）

> 日期：`2026-07-23`
>
> 用途：定义 AI 自主驱动 UA 操作沉淀项目的目标、边界和决策权限，减少人工逐步确认的开销

## 1. 终极目标

**让 AI 能够自主完成 Phase 0 剩余任务（P0-06 至 P0-12），产出一份完整的 Phase 0 总验收报告和能力准入候选矩阵，使项目具备进入 Phase 1A（Google Episode 实现）的条件。**

人话：AI 自己把"搞清楚我们有什么数据、能做什么、不能做什么"这件事做完，然后告诉人"可以开始建 Google 的 Episode 了"。

## 2. 当前进度

| 任务 | 状态 | 人工确认 |
|---|---|---|
| P0-00 执行台账 | ✅ INTEGRATED | ✅ |
| P0-01 静态审计 | ✅ INTEGRATED | ✅ |
| P0-02 实时探测 | ✅ INTEGRATED | ✅ |
| P0-03 MI 接口与凭证 | ✅ INTEGRATED | ✅ |
| P0-04 来源覆盖矩阵 | ✅ INTEGRATED | ✅ |
| P0-05 DecisionSubject 映射 | ✅ INTEGRATED | ✅ |
| P0-06 OperationEvent 合同 | 🔲 待执行 | — |
| P0-07 Opportunity 与标签 | 🔲 待执行 | — |
| P0-08 as-of 特征审计 | 🔲 待执行 | — |
| P0-09 预算动作分桶 | 🔲 待执行 | — |
| P0-10 OutcomeEstimand | 🔲 HUMAN_GATE | 需要 |
| P0-11 PII 与安全 | 🔲 待执行 | — |
| P0-12 Phase 0 总验收 | 🔲 待执行 | 需要 |

## 3. AI 可以自主决定的事

以下事项 AI 不需要逐个问人，直接做：

1. **执行 P0-06 至 P0-09、P0-11**：每个任务按任务书要求执行，产出报告，自审，提交 candidate commit
2. **任务间集成**：每完成一个任务且自审通过后，直接 cherry-pick 到集成分支，继续下一个任务（不需要人工确认每个集成）
3. **探测数据库/MI 接口**：用已有的 MC/CK/MI 凭证做有界只读探测（已有 token 不会过期）
4. **修改 P0-01~P0-05 的报告**：如果后续任务发现前面的结论有误，可以直接修正（像 P0-05 修正 P0-01 的 AppLovin 国家预算一样）
5. **冻结设计合同**：P0-06（事件去重、before/after、evidence tier）、P0-07（标签窗口、去重、exclusion reason）、P0-08（available_at 定义、泄漏检测）、P0-09（分桶版本）都可以 AI 自主冻结候选版本

## 4. AI 必须停下来问人的事

以下事项 AI 不能自己决定，必须停下问人：

1. **P0-10 OutcomeEstimand**：利润公式、收入源（SDK/AF）、成本口径、D7/D14 成熟窗口——这些是业务决策，AI 只整理候选和分歧
2. **P0-12 Phase 0 总验收**：最终能力准入矩阵需要人确认
3. **任何 `GO_*` 状态**：AI 只产出 `go_candidate`，正式 GO 须人批准
4. **花钱的事**：调用付费 LLM、创建生产表、部署、执行 DDL/DML
5. **跨团队的事**：需要 MI 后端/DataWorks 管理员配合的（虽然凭证已解决，但后续可能还有）
6. **碰共享 checkout WIP**：`ai_ck/engineering_artifacts/freshness_snapshot.json` 和 `ai_hive/engineering_artifacts/freshness_snapshot.json` 不能碰

## 5. 执行规则

1. **每个任务一个隔离 worktree、一个分支、一个 candidate commit**
2. **每完成 3 个任务打包一次集成**（不用每个都集成，但也不能攒太多）
3. **自审通过就直接推进下一个任务**，不等人工确认；人工确认攒到 P0-12 一次性做
4. **如果遇到 BLOCKED 或 HOLD**：记录 blocker，跳过该任务继续做下一个不依赖它的任务；不要卡住等
5. **探测只用有界只读查询**：`LIMIT` + 分区过滤，不全表扫描
6. **不输出 PII**：操作人邮箱、用户 ID 只统计不落盘
7. **所有结论标注证据等级**：`repo_confirmed` / `live_verified` / `design_required` / `blocked`
8. **遇到前序结论有误直接修正**：在报告里写"修正 P0-xx 第 y 节"，不偷偷改

## 6. Phase 0 完成条件

Phase 0 完成的标志是 P0-12 总验收报告产出，且包含：

1. 三媒体 × DecisionSubject 的能力准入候选矩阵（`go_candidate` / `hold` / `blocked`）
2. 每张拟建表的 grain、分区、Owner、SLA、lineage、PII、freshness 候选
3. Phase 1A/1B/1C 的可启动任务清单和 base commit
4. 所有 blocker 和 TODO 的完整清单

## 7. Phase 0 之后的下一步（不在本次目标内）

Phase 0 验收后，进入 Phase 1A（Google Episode 实现），那是另一个 goal。本次目标到 P0-12 产出为止。

## 8. 成功标准

| 标准 | 衡量方式 |
|---|---|
| P0-06~P0-09、P0-11 全部产出 candidate commit | 5 份报告文件 + 5 个 commit |
| P0-10 产出候选和分歧清单（不需要人做决策） | 1 份决策单草稿 |
| P0-12 产出总验收报告和准入矩阵 | 2 份文件 |
| 无 PII 泄漏 | 所有报告不含操作人邮箱/用户 ID 明文 |
| 共享 checkout WIP 未被触碰 | `git status --short` 始终只有 freshness snapshot |
| 所有结论可回溯 | 每条结论有文件+行号或探测命令引用 |
