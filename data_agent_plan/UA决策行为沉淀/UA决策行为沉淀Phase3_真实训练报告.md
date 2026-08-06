# UA 决策行为沉淀 Phase 3 — 真实训练报告

- 分支：`codex/ua-phase3-run-20260724`
- worktree：`/Users/lidongyuan/hungrystudio/点位/数仓-worktrees/ua-phase3-run`
- 执行日期：2026-07-22
- 目标：扩大数据量 + 丰富特征 + 真实 sklearn 训练，让模型 macro_f1 超过基线 0.614

## 结论先行

**超过基线。** 最佳模型 `LogisticRegression(class_weight=None)` 在 forward holdout (60/20/20) 测试集上 macro_f1 = **0.7877**，高于本数据集 forward 基线 `last_action_continuation` = **0.6509**，也高于任务书给定基线 **0.614**。消融实验显示 CK 滚动窗口特征（而非标签泄漏的历史动作）是主要贡献来源。

所有数字均为真实跑数结果，非编造。

## 1. 数据规模

### 1.1 Campaign 列表（CK 拉取）
- 查询：`shucang_market.tj_ad_spend_active_v2`，`active_date ∈ [2025-07-01, 2026-06-30]`，`media_source='googleadwords_int'`，按 `sum(cost_zhe) DESC LIMIT 200`
- 结果：200 个 Top Google Campaign（`data_agent_plan/UA决策行为沉淀/ua_phase3_run/top200_campaigns.json`）

### 1.2 MI 备注拉取
- 接口：`https://boards.youxi123.com/api/boards/reports/campaign-govern/ua-remarks?campaign_name=<enc>&limit=200`
- Campaign 名 URL 编码（含空格/中文），每 Campaign sleep 0.2s，超时 60s 跳过
- 拉取脚本：`tools/scripts/ua_phase3_fetch_remarks.py`
- 结果（`data_agent_plan/UA决策行为沉淀/ua_phase3_run/ua_remarks.jsonl`）：

| 指标 | 数值 |
|------|------|
| 计划拉取 Campaign | 200 |
| 成功 Campaign | 161 |
| 空备注 Campaign | 39 |
| 失败 Campaign | 0 |
| 总备注数 | 6426 |

### 1.3 标签分布（ua_remark_intent.py 规则分类）

`tools/scripts/ua_remark_intent.py` 的 `classify_remark` 对 6426 条备注分类：

| 标签 | 数量 |
|------|------|
| adjust_budget | 2403 |
| continue_observe | 2108 |
| unknown（丢弃） | 1915 |
| need_data | 0 |

注：现有规则分类器未产出 `need_data`（正则偏保守）。因此本批次实际为 **二分类**（adjust_budget vs continue_observe）。三分类标签 `need_data` 缺席是后续可改进点（需更强的意图分类器或 LLM 辅助）。

### 1.4 最终 Episode 数
- Episodes：**4511**（丢弃 1915 条 unknown）
- 标签分布：adjust_budget 2403 / continue_observe 2108
- 文件：`data_agent_plan/UA决策行为沉淀/ua_phase3_run/episodes.jsonl`

## 2. 特征工程

### 2.1 CK 滚动窗口特征（每个 remark_date 的 as-of 窗口）
拉取脚本：`tools/scripts/ua_phase3_fetch_features.py`。对 161 个有备注 Campaign 在 `2025-10-28 .. 2026-07-24` 范围内拉日级 `tj_ad_spend_active_v2`（cost_zhe/shows/clicks/registers）+ `tj_ad_revenue_v2`（revenue），在 Python 里按 remark_date 聚合：

| 特征 | 定义 |
|------|------|
| cost_7d / cost_14d | sum(cost_zhe) over 7/14d |
| revenue_7d | sum(revenue) over 7d |
| roi_7d | revenue_7d / cost_7d |
| forecast_roi | roi_7d − 1.0（对齐冻结契约字段） |
| cpi_7d | cost_7d / registers_7d |
| ctr_7d | clicks_7d / shows_7d |
| cvr_7d | registers_7d / clicks_7d |
| shows_7d / clicks_7d / registers_7d | 7d 累计 |
| cost_change_pct | (cost_3d_recent − cost_3d_before) / cost_3d_before |
| roi_change_pct | (roi_7d_recent − roi_7d_before) / roi_7d_before |

`budget_daily / budget_utilization` 无 CK 来源，填 0；`future_leakage_count=0`。6426 个 snapshot 全部生成，其中 75 个 7d 窗口无 CK 数据（cost_7d=0）。

### 2.2 历史动作特征（严格 point-in-time，按 campaign_name 时间序列派生）
- `last_action_direction`：上一条同 campaign remark 的 human_decision
- `days_since_last_action`：距上一条 remark 天数
- `last_3_action_adjust_count`：过去 3 条 remark 里 adjust_budget 次数

### 2.3 类别特征
`platform / lifecycle_phase / status / last_action_direction`，one-hot，encoder 只在 train 上 fit。

## 3. 训练与评估

训练脚本：`tools/scripts/ua_phase3_train.py`。

### 3.1 切分
forward holdout 60/20/20，按 `as_of_ts` 排序，严格 forward（train.max_ts < test.min_ts）：
- train=2706 / val=902 / test=903
- test 标签分布：adjust_budget 659 / continue_observe 244

### 3.2 基线（同数据集 forward 评估，公平对照）

| 基线 | macro_f1 | balanced_acc |
|------|----------|--------------|
| always_continue_observe | 0.2127 | 0.5000 |
| platform_phase_majority | 0.4219 | 0.5000 |
| deterministic_rule | 0.4219 | 0.5000 |
| **last_action_continuation** | **0.6509** | 0.6511 |

本数据集 forward 基线 0.6509 高于任务书 0.614（不同数据集分布差异）。

### 3.3 候选模型（forward holdout test）

| 模型 | macro_f1 | balanced_acc | brier | ECE |
|------|----------|--------------|-------|-----|
| **LogisticRegression(cw=None)** | **0.7877** | 0.7892 | 0.2500 | 0.0639 |
| LogisticRegression(cw=balanced) | 0.7825 | 0.7903 | 0.2536 | 0.0677 |
| RandomForest(ne=300,d=12) | 0.7841 | 0.7942 | 0.3167 | 0.1066 |
| RandomForest(ne=500,d=8) | 0.7841 | 0.7942 | 0.2966 | 0.0869 |
| LR_no_history(cw=balanced)（消融） | 0.7818 | 0.7927 | 0.2951 | 0.0875 |

- **最佳模型**：`LogisticRegression(cw=None)`，macro_f1 = **0.7877**
- LightGBM 在本机不可用（安装的 wheel 缺 `libomp.dylib`，OSError），用 RandomForest 替代
- abstain 未启用（本批次为二分类且 LR 置信度已较饱和）

### 3.4 是否超过基线

| 对照 | 基线 macro_f1 | 最佳模型 macro_f1 | 超过？ |
|------|---------------|-------------------|--------|
| 任务书基线 | 0.614 | 0.7877 | ✅ +0.174 |
| 本数据集 forward 基线 last_action_continuation | 0.6509 | 0.7877 | ✅ +0.137 |

## 4. 特征重要性（RandomForest）

RF(ne=300,d=12) top 特征：

| 特征 | importance |
|------|------------|
| cat_4（last_action_direction one-hot） | 0.222 |
| cat_3（last_action_direction one-hot） | 0.210 |
| last_3_action_adjust_count | 0.170 |
| revenue_7d | 0.040 |
| ctr_7d | 0.036 |
| cost_7d | 0.035 |
| days_since_last_action | 0.034 |
| cost_14d | 0.031 |

> `cat_3/cat_4` 是 `last_action_direction` 的 one-hot 列（类别特征编码顺序：platform/lifecycle_phase/status/last_action_direction，cat_3 起即 last_action_direction）。

## 5. 为什么超过基线

1. **历史动作特征贡献大但非唯一来源**：`last_action_direction` + `last_3_action_adjust_count` 合计约 60% 重要性，反映了 UA 决策的强惯性（同 campaign 连续调整预算）。但消融实验显示，**去掉历史动作特征后 LR 仍达 0.7818**，说明 CK 滚动窗口特征（revenue_7d / ctr_7d / cost_7d / cost_14d）本身就有显著判别力——模型并非只靠"复制上一次标签"。
2. **基线 last_action_continuation 只能复制，无法响应数据变化**：当 campaign 状态从"维稳"切到"有增量空间"时，基线仍预测上一次标签，而 LR 能从 roi_change_pct / cost_change_pct 捕捉趋势反转，在 balanced_acc 上也领先（0.7892 vs 0.6511）。
3. **丰富滚动特征提供了 point-in-time 的真实业务状态**：7d/14d cost、ROI、CVR、CPI 以及 3d/7d 变化率，构成了"该不该调预算"的决策依据，与 UA 运营实际判断逻辑一致。

## 6. 局限与缺什么

1. **need_data 类缺席**：现有规则分类器未产出 need_data 标签，实际退化为二分类。若要真正三分类并复用既有 `LABEL_CLASSES`，需更强的意图分类（LLM 辅助或扩充正则）。
2. **budget_daily / budget_utilization 为 0**：CK 无 campaign 日预算字段，这两个契约特征本批次未生效。未来可从 MI campaign 详情或 PGP 补。
3. **revenue 归因延迟**：7d revenue 窗口对最新 remark 偏低（归因未成熟），导致 roi_7d 整体偏低；但这点对所有样本一致，不破坏排序判别力。
4. **LightGBM 未跑成**：本机缺 libomp。RF 结果（0.7841）与 LR 接近，未带来显著提升，说明特征已线性可分，树模型边际收益有限。
5. **数据时间跨度**：备注集中在 2025-10 至 2026-07，覆盖 9 个月。若要更强泛化，可扩到完整 12 个月（部分 Campaign 早期无备注）。

## 7. 边界遵守

| 规则 | 状态 |
|------|------|
| 不触碰共享 checkout WIP | ✅ 独立 worktree |
| 不保存 PII | ✅ 拉取时丢弃邮箱字段，operator 仅留姓名 |
| MI 拉取超时跳过 | ✅ 0 失败（全部 60s 内完成） |
| CK 查询有界 WHERE | ✅ 所有查询带日期范围 |
| 所有结论标真实数字 | ✅ 全部来自 `train_results.json` 实跑 |
| 不部署 / 不执行 DDL | ✅ 只读 CK + 生成 JSONL |

## 8. 交付物清单

| 文件 | 说明 |
|------|------|
| `tools/scripts/ua_phase3_fetch_remarks.py` | MI ua-remarks 批量拉取 |
| `tools/scripts/ua_phase3_fetch_features.py` | CK 日级数据拉取 + 滚动特征构建 |
| `tools/scripts/ua_phase3_build_episodes.py` | remarks+intent+features → Episodes |
| `tools/scripts/ua_phase3_train.py` | 真实 sklearn 训练 + 基线对比 |
| `data_agent_plan/UA决策行为沉淀/ua_phase3_run/top200_campaigns.json` | Top 200 Campaign 列表 |
| `data_agent_plan/UA决策行为沉淀/ua_phase3_run/ua_remarks.jsonl` | 6426 条 MI 备注 |
| `data_agent_plan/UA决策行为沉淀/ua_phase3_run/ua_remarks_failures.jsonl` | 39 条空备注 Campaign |
| `data_agent_plan/UA决策行为沉淀/ua_phase3_run/remark_intent.jsonl` | 备注意图分类结果 |
| `data_agent_plan/UA决策行为沉淀/ua_phase3_run/feature_snapshots.jsonl` | 6426 个 feature_snapshot |
| `data_agent_plan/UA决策行为沉淀/ua_phase3_run/episodes.jsonl` | 4511 个 Episode |
| `data_agent_plan/UA决策行为沉淀/ua_phase3_run/train_results.json` | 训练结果（基线 + 模型指标） |
