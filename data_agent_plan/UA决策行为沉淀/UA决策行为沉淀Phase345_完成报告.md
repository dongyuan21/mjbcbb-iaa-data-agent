# UA 决策行为沉淀 Phase 3 + 4 + 5 完成报告

- 分支：`codex/ua-phase345-20260724`
- base commit：`ae2fa823`
- 实现 commit：`7e159c6b feat(ua-phase345): Phase 3+4+5 行为模仿/Uplift/EvidenceBundle 框架实现`
- 工作目录：`/Users/lidongyuan/hungrystudio/点位/数仓-worktrees/ua-phase345`
- 执行日期：2026-07-24

## 1. 范围与边界

本报告记录 UA 决策行为沉淀 Phase 3（行为模仿训练框架）、Phase 4（Uplift 框架）、Phase 5（EvidenceBundle 组装）的框架代码与测试实现。

严格遵守的边界：
- 不执行任何 DDL/DML
- 不部署
- 不触碰共享 checkout WIP
- 不保存 PII
- 不调用付费 LLM
- 不训练真实模型（只写框架代码 + mock 测试）
- 所有测试全绿

## 2. 交付物清单

| 任务 | 脚本 | 测试 | 测试数 |
|------|------|------|--------|
| UA-P3-02 行为基线冻结 | `tools/scripts/ua_behavior_baseline.py` | `tools/scripts/test_ua_behavior_baseline.py` | 7 |
| UA-P3-03 行为候选模型训练框架 | `tools/scripts/ua_behavior_model.py` | `tools/scripts/test_ua_behavior_model.py` | 11 |
| UA-P4-01 共同支持与干扰盘点 | `tools/scripts/ua_uplift_support.py` | `tools/scripts/test_ua_uplift_support.py` | 10 |
| UA-P4-03 匹配/AIPU 候选框架 | `tools/scripts/ua_uplift_estimate.py` | `tools/scripts/test_ua_uplift_estimate.py` | 10 |
| UA-P5-01 DecisionEvidenceBundle 组装 | `tools/scripts/ua_build_evidence_bundle.py` | `tools/scripts/test_ua_build_evidence_bundle.py` | 13 |
| 合计 | 5 脚本 | 5 测试 | 51 |

脚本风格与既有 `tools/scripts/ua_*.py` 一致：argparse + `--mock` + JSONL 输出 + `COLLECTOR_VERSION` + 测试用 `PYTHONPATH=. python3 tools/scripts/test_xxx.py` 运行。

## 3. Phase 3 — 行为模仿训练框架

### 3.1 UA-P3-02 行为基线冻结

文件：`tools/scripts/ua_behavior_baseline.py`

4 个基线（候选模型必须超过的最强简单对照）：
1. `always_continue_observe` — 始终预测 `continue_observe`（多数类安全默认）
2. `platform_phase_majority` — 按 `(platform, lifecycle_phase)` 历史多数类预测；`fit_platform_phase_majority` 从训练集学习，未见过的组回退到 `continue_observe`
3. `deterministic_rule` — 规则映射：coverage 不完整 → `need_data`；`forecast_roi < -0.1` → `adjust_budget`；其余 → `continue_observe`。规则冻结，不调参
4. `last_action_continuation` — 预测上一次的 `human_decision`（首条默认 `continue_observe`）。严格 point-in-time：预测第 i 条只用第 i-1 条及之前的真实标签，不偷看当前标签

评估指标：
- `macro_f1` — 各类 F1 的宏平均
- `balanced_accuracy` — 各类 recall 的平均（只对存在的类求平均）
- `per_class` — 每类 `precision / recall / f1 / support`
- `confusion_matrix` — 每类 TP/FP/FN/TN

`freeze_baselines()` 一次性跑全部 4 个基线并评估。所有输出标 `imitation_only=True`。

测试覆盖（7）：各基线单独行为、评估指标数值正确性（含 macro-F1=0.6 / balanced_acc=2/3 的精确断言）、freeze 输出标 imitation_only、mock main 运行。

### 3.2 UA-P3-03 行为候选模型训练框架

文件：`tools/scripts/ua_behavior_model.py`

特征工程：
- 数值特征（冻结契约）：`cost_14d / forecast_roi / revenue_sdk / budget_daily / budget_utilization / future_leakage_count`（缺失填 0）
- 类别特征：`platform / lifecycle_phase / status`（one-hot，encoder 只在 train 上 fit）
- `feature_contract()` 返回冻结契约

切分：
- `forward_holdout_split` — 按 `as_of_ts` 排序，60/20/20，严格 forward（train.max_ts < test.min_ts）
- `cold_start_split` — 按 `decision_subject_id` 分组，整组分配到同一集合（账户不跨集），确定性 shuffle（seed=42），模拟未见过的账户

模型（mock，不依赖 sklearn/lightgbm）：
- `MockLogisticRegression` — 用特征向量 MD5 哈希到确定性 logit 偏置 + 训练集类别频率 bias，softmax 出概率
- `MockLightGBM` — 树模型风格的确定性概率（扰动更大）
- 两者均 `fit` + `predict_proba`，输出确定性（同输入同输出）、概率和为 1

概率校准：
- `brier_score` — 多类 Brier score
- `expected_calibration_error` — 按 max prob 分 10 桶，加权平均 |accuracy - confidence|

abstain：
- `apply_abstain` — max_prob < 阈值（默认 0.4）→ 预测 `abstain`
- `abstain_coverage` — abstain 占比
- 非 abstain 样本才算 macro-F1 / balanced_accuracy

`train_and_evaluate()` 完整流水线：切分 → 特征化 → 训练 → 测试集概率 → abstain → 评估。输出始终 `imitation_only=True`。

禁止项已遵守：不用未来 Outcome；不从执行反填意向；不做 RL；不微调大模型；不输出精确预算金额。

测试覆盖（11）：特征提取/one-hot/矩阵构建、forward/cold-start 切分守恒与不跨集、mock 模型确定性与概率归一、Brier/ECE 数值、abstain 行为与覆盖率、两种切分流水线 imitation_only、mock main 运行。

## 4. Phase 4 — Uplift 框架

### 4.1 UA-P4-01 共同支持与干扰盘点

文件：`tools/scripts/ua_uplift_support.py`

核心函数：
- `classify_arm` — Episode → `treatment`（observed_treatment == 指定动作）/ `control`（no_budget_change）/ `excluded`
- `count_arms` — 统计三臂数量
- `filter_origin` — 只保留 `origin=human_ua`，其余记 `origin_not_human_ua` 排除原因
- `propensity_overlap` — `treatment_ratio` / `control_ratio` / `overlap_ratio = min(t,c)/total * 2`（0=完全不平衡, 1=完全平衡）
- `detect_interference` — `repeated_treatment`（同 subject 重复 treatment）/ `shared_budget`（同 subject treatment+control 共存）
- `assess_common_support` — 综合：origin 过滤 + 臂数 + overlap + 干扰 → `estimable` 布尔 + `blockers` 列表

阻断条件（任一触发 `effect_not_estimable`）：
- treatment < `MIN_PER_ARM`(5)
- control < `MIN_PER_ARM`(5)
- `overlap_ratio` < `MIN_OVERLAP_RATIO`(0.1)
- origin 非 human_ua（排除并记 blocker）
- 干扰存在（记 blocker，但不单独阻断）

所有输出标 `not_causal_proof=True`。

测试覆盖（10）：分类/统计/origin 过滤/overlap 计算/干扰检测/estimable 与三种 not_estimable 场景（too_few / overlap / origin_excluded）/mock main。

### 4.2 UA-P4-03 匹配/AIPW 候选框架

文件：`tools/scripts/ua_uplift_estimate.py`

核心函数：
- `nearest_neighbor_match` — 每个 treatment 找距离最小的 control（无放回），协变量 `cost_14d / forecast_roi / budget_utilization`，**联合标准化**（treatment+control 共享均值/标准差）保证距离可比
- `matched_effect` — 匹配后 ATE = mean(Y_t) - mean(Y_c_matched)
- `aipw_framework_mock` — AIPW 框架 mock：均值差 + pooled SE + 95% CI，标 `not_causal_proof`。不真正训练 propensity/outcome model
- `event_study_pre_trend` — 前趋势平行检验：diff_mean < 0.1*|control_mean| → `parallel_pre_trend=True`
- `placebo_test` — 对照臂内均分两组，伪 treatment ATE 应 within 1.96*noise

`estimate_uplift()` 完整流水线：匹配 → AIPW mock → event-study → placebo。输出 `labels = ["not_causal_proof", "adjusted_observational_candidate"]`，两布尔字段均为 True。

边界已遵守：AIPW/因果森林只标 `adjusted_observational_candidate + not_causal_proof`，不构成因果证明，不声称 Agent 会提升利润。

测试覆盖（10）：特征向量/标准化/最近邻匹配（同特征距离 0）/匹配效应数值/AIPW CI/event-study 平行与非平行/placebo within noise/流水线标签/mock main。

## 5. Phase 5 — DecisionEvidenceBundle

### 5.1 UA-P5-01 DecisionEvidenceBundle 组装

文件：`tools/scripts/ua_build_evidence_bundle.py`

六个组件：
1. `current_facts` — 当前事实（来自 feature_snapshot）；snapshot 缺失 → `blocked`
2. `similar_cases` — 相似案例；未准入 → `not_admitted`；无案例 → `not_enough_data`
3. `behavior_proba` — 行为概率；未准入 → `not_admitted`；输出缺失 → `blocked`；可用时带 `imitation_only` label
4. `uplift_estimate` — Uplift 估计；未准入 → `not_admitted`；缺失 → `blocked`；可用时带 `not_causal_proof + adjusted_observational_candidate` label。**非首轮硬依赖**：缺失不阻断 bundle
5. `data_quality` — coverage/freshness/leakage；future_leakage → `blocked`
6. `risks` — 汇总风险标记（coverage_incomplete / future_leakage / behavior_abstain / OOD / no_similar_cases / uplift_not_estimable）

组件状态四值：`available / not_admitted / blocked / not_enough_data`。

关键安全规则（已测试）：
- 始终 `needs_decision=true`（不替 UA 做决定）
- 始终 `imitation_only=true` + `not_causal_proof=true`
- **没有空对象伪装可用**：`_make_component` 对非 available 状态强制 `payload=None`，只填 status + reason
- uplift 缺失不阻断 bundle

测试覆盖（13）：组件 status 校验、needs_decision 恒真、标签恒真、不可用组件 payload=None、完整 bundle 全 available、snapshot 缺失 blocked、无相似案例 not_enough_data、检索未准入 not_admitted、future_leakage blocked+risk、behavior abstain risk、uplift 缺失不阻断、所有 status 合法、mock main。

## 6. 测试验证

全部 5 个测试套件一次性全绿：

```
test_ua_behavior_baseline.py     7 passed
test_ua_behavior_model.py       11 passed
test_ua_uplift_support.py       10 passed
test_ua_uplift_estimate.py      10 passed
test_ua_build_evidence_bundle.py 13 passed
                              -------
                                51 passed
```

回归检查：既有 `test_ua_build_episode / test_ua_case_retrieval / test_ua_build_feature_snapshot` 仍全绿，未受影响。

运行方式：
```
PYTHONPATH=. python3 tools/scripts/test_ua_behavior_baseline.py
PYTHONPATH=. python3 tools/scripts/test_ua_behavior_model.py
PYTHONPATH=. python3 tools/scripts/test_ua_uplift_support.py
PYTHONPATH=. python3 tools/scripts/test_ua_uplift_estimate.py
PYTHONPATH=. python3 tools/scripts/test_ua_build_evidence_bundle.py
```

## 7. 关键设计决策

1. **mock 模型不依赖外部库**：`MockLogisticRegression` / `MockLightGBM` 用 MD5 哈希到确定性 logit，避免引入 sklearn/lightgbm 依赖，符合"不训练真实模型"约束，同时保证测试可复现。
2. **forward holdout 严格性**：按 `as_of_ts` 排序切分，断言 `train.max_ts < test.min_ts`，防止未来泄漏进训练集。
3. **cold-start 按账户分组**：整组分配到同一集合，断言三集合账户不交集，真正模拟未见过的账户。
4. **最近邻匹配联合标准化**：treatment + control 共享均值/标准差，保证距离尺度可比（早期版本分别在两臂标准化导致距离不可比，已修复）。
5. **组件不可用不伪装可用**：`_make_component` 强制非 available 状态 `payload=None`，只填 status + reason，杜绝"空对象伪装可用"。
6. **uplift 非首轮硬依赖**：uplift 缺失只标记 `not_admitted/blocked`，不阻断 bundle 的 `needs_decision`。

## 8. 边界遵守确认

| 规则 | 状态 |
|------|------|
| 不执行 DDL/DML | ✅ 全部为 JSONL 文件输出 |
| 不部署 | ✅ 无部署脚本/配置 |
| 不触碰共享 checkout WIP | ✅ 在独立 worktree |
| 不保存 PII | ✅ mock 数据无 PII，真实模式只读 JSONL |
| 不调用付费 LLM | ✅ 无 LLM 调用 |
| 不训练真实模型 | ✅ mock 模型，不依赖 sklearn/lightgbm |
| 所有测试全绿 | ✅ 51/51 |

## 9. 后续衔接

本批次为框架代码 + mock 测试，正式 GO 状态仍需人工 Gate 批准：
- Phase 3 的 `GO_IMITATION` 候选需 UA-P3-04 forward/cold-start 回测通过后由 `UA-GATE` 批准
- Phase 4 的 `GO_UPLIFT_CANDIDATE` 需 UA-P4-04 独立因果审阅后由 `UA-GATE` 批准
- Phase 5 的 `GO_SHADOW(component=advisor_bundle)` 需 UA-P5-02/03 通过后由 `UA-GATE` 批准

所有输出始终标 `imitation_only / not_causal_proof`，不表示业务效果好，不表示因果证明。
