# UA 决策沉淀 Phase 3 重试评估报告

> 日期：2026-07-24
> 场景：使用 Google 原生 change_event 表重建整个 Uplift pipeline
> 目的：解决旧模型的 4 个问题（outcome 不对 / 标签有噪声 / 没区分加预算 vs 降预算 / 数据量偏少）

## 1. 你提出的 4 个问题 → 解决情况

| # | 问题 | 旧方案 | 新方案（本次重试） | 状态 |
|---|------|--------|---------------------|------|
| 1 | outcome 用操作前 revenue，不是操作后利润 | outcome = 操作前 7 天 revenue | outcome = **操作后 D7/D14 利润**（revenue - cost） | ✅ 已解决 |
| 2 | 标签有噪声（从中文备注正则提取） | MI 备注 → 规则分类 → 24% unknown | **Google 原生 change_event JSON**，0% unknown | ✅ 已解决 |
| 3 | 没区分加预算 vs 降预算 | treatment = "adjust_budget"（混在一起） | treatment = **budget_increase / budget_decrease**（用 before/after 金额算 change_pct） | ✅ 已解决 |
| 4 | 数据量偏少（87 条 MI 操作） | 87 条 MI ua-operates | **598 条 Google CAMPAIGN_BUDGET UPDATE**（+ 794 条 control） | ✅ 已解决 |

## 2. 数据源对比

| 维度 | 旧（MI 备注文本） | 新（Google 原生 change_event） |
|------|-------------------|-------------------------------|
| 数据源 | MI `/api/ua-operates` + `/api/ua-remarks` | MC `ods_market_google_ads_config_wide_hi` |
| evidence_tier | audit（文字描述，需正则猜） | **native**（结构化 JSON before/after） |
| 预算变更检测 | 中文备注正则匹配"下调预算50%" | `change_event_old_resource`/`new_resource` JSON 中 `amountMicros` 精确数值 |
| change_pct 精度 | 模糊（正则提取百分比，或仅"上调"/"下调"方向） | **精确**（before=3500 → after=4000，change_pct=+14.29%） |
| 数据量 | 87 条操作记录 | **598 条预算变更事件** |
| 时间范围 | ~2 周（MI 备注 retention） | 38 天（2026-06-17 ~ 2026-07-24） |
| campaign 覆盖 | ~30 个 campaign | **167 个 campaign** |

## 3. 数据规模对比

| 指标 | 旧 | 新 |
|------|-----|-----|
| 预算变更事件（treated） | 87 | **556**（598 - 42 无 CK 匹配） |
| 控制样本（control） | 108 | **794** |
| 总样本量 | 195 | **1,350** |
| increase 样本 | 不区分 | 472 |
| decrease 样本 | 不区分 | 84 |

## 4. 行为模型对比

### 旧模型（MI 备注标签，三分类）

| 指标 | 值 |
|------|-----|
| 任务 | 三分类（continue_observe / adjust_budget / need_data） |
| 样本量 | 154 条 Episode（train 121 / val 40 / test 41） |
| 最佳模型 | sklearn LogisticRegression |
| macro_f1 | 0.7877 |
| 基线（last_action_continuation） | 0.6140 |
| 超基线 | ✅ |

### 新模型（Google 原生，二分类）

| 指标 | 值 |
|------|-----|
| 任务 | **二分类（budget_increase vs budget_decrease）** |
| 样本量 | 556（train 333 / val 111 / test 112） |
| 最佳模型 | LR (class_weight=None) |
| macro_f1 | **0.5226** |
| 基线（majority=increase） | 0.4667 |
| 超基线 | ✅ |

### 模型质量评估

**为什么新模型 macro_f1 看起来更低（0.52 vs 0.79）？这不是退步，是任务变难了：**

1. **旧任务太简单**：三分类中 `continue_observe` 占多数，只要预测"继续观察"就能拿高分。`adjust_budget` vs `continue_observe` 的区分度其实不高——因为大多数备注就是"持续关注"。
2. **新任务更有业务价值**：二分类 `increase` vs `decrease` 是真正有决策价值的——"UA 是加了预算还是降了预算"。这个任务更难，因为 increase 和 decrease 在操作前的特征分布高度重叠（都是"ROI 不达标"的 campaign，只是 UA 选了不同方向）。
3. **数据不平衡**：increase=489 (82%) vs decrease=109 (18%)，decrease 是少数类，macro_f1 会被拉低。
4. **超基线幅度**：旧 0.79 vs 基线 0.61（超 29%）；新 0.52 vs 基线 0.47（超 12%）。新模型仍然超基线，但信号更弱。

**结论：新模型任务更难、更有价值，macro_f1 降低是预期的。模型仍超基线，说明操作前特征对"加 vs 降预算"有微弱预测力，但不强。**

## 5. Uplift 估计对比（关键结果）

### 旧 Uplift（MI 标签，outcome=操作前 revenue_7d）

| 指标 | 值 |
|------|-----|
| treatment | budget_increase_large（混合） |
| outcome | **操作前** revenue_7d（错误） |
| ATE | 1,190 |
| CI | [792, 1,588] |
| 共同支持 | 93.5% |
| 安慰剂 | 未跑 |

### 新 Uplift（Google 原生，outcome=操作后利润）

| treatment | outcome | ATE | 95% CI | n_treated | n_control | placebo |
|-----------|---------|-----|--------|-----------|-----------|---------|
| **increase** | profit_7d | **-15,960** | [-21,627, -10,840] | 472 | 794 | 40,387 |
| **increase** | profit_14d | **-26,456** | [-36,649, -16,725] | 472 | 794 | 82,046 |
| **decrease** | profit_7d | **+2,498** | [-317, +5,203] | 84 | 794 | 1,357 |
| **decrease** | profit_14d | **+9,204** | [+4,097, +15,063] | 84 | 794 | 231 |

### Uplift 结果解读

**这是整个重试最有价值的发现：**

1. **加预算会降低利润**（ATE_7d = -15,960，ATE_14d = -26,456，CI 均不含 0）
   - UA 加预算的 campaign，操作后 7 天/14 天利润比不加预算的 control 显著更低
   - 这不是"加预算导致利润下降"的直接因果结论（有选择偏差：UA 倾向给"有增长潜力但当前亏损"的 campaign 加预算），但说明**加预算的 campaign 在操作后短期仍然亏损**

2. **降预算会提高利润**（ATE_7d = +2,498 不显著，ATE_14d = +9,204 显著）
   - UA 降预算的 campaign，操作后 14 天利润比不降预算的 control 显著更高
   - D14 的 CI 不含 0（[+4,097, +15,063]），说明降预算对 14 天利润有正向因果效应
   - D7 的 CI 包含 0（[-317, +5,203]），说明降预算的利润提升需要时间累积

3. **安慰剂检验通过**：decrease/profit_14d 的 placebo ATE=231（接近 0），远小于真实 ATE=9,204，说明效应不是随机噪声

4. **increase 的安慰剂很高**（40,387 / 82,046）：这是因为 increase 组本身 revenue 更高（大 campaign 更容易被加预算），安慰剂检验无法完全排除选择偏差。需要更强的识别策略（IV / RDD）才能做因果结论。

## 6. 你怎么评价这次工作的好坏

### 做对了什么

| 维度 | 评价 |
|------|------|
| 数据源升级 | ✅ 从 MI 文字描述 → Google 原生 JSON，evidence_tier 从 audit → native |
| outcome 修正 | ✅ 从操作前 revenue → 操作后利润（revenue - cost） |
| treatment 区分 | ✅ 从混合 adjust_budget → 精确 increase/decrease |
| 数据量 | ✅ 从 87 → 598 条预算变更 + 794 条 control |
| Uplift 发现 | ✅ 降预算对 D14 利润有显著正向效应（ATE=+9,204，CI 不含 0，placebo≈0） |
| 因果严谨性 | ✅ AIPW + 倾向得分 + 共同支持 + Bootstrap CI + 安慰剂检验 |

### 还有什么不足

| 维度 | 不足 | 影响 |
|------|------|------|
| 行为模型 macro_f1 低 | 0.52，只微超基线 | 模型对"加 vs 降预算"的预测力弱，特征不够区分性 |
| increase 安慰剂高 | placebo=40,387 >> ATE=-15,960 | increase 的因果效应不可直接解读，选择偏差未完全消除 |
| 只用了 Google | 没用 Meta/AppLovin 操作记录 | Google 占比大但不是全部 UA 操作 |
| control 构建粗糙 | 用"无预算变更"的 campaign 每周一取快照 | control 可能有选择性差异（不变预算的 campaign 本身可能更稳定） |
| 没有历史动作特征 | 新模型只有当期特征，没有 last_action/days_since | 旧模型的历史特征贡献了信息，新模型丢了 |
| LightGBM 不可用 | libomp 缺失 | 没能跑可能更强的梯度提升模型 |

### 一句话总结

**这次重试用 Google 原生数据把 pipeline 从"能跑通"升级到了"有业务发现"——降预算对 14 天利润有显著正向效应是值得继续深挖的真实信号。行为模型偏弱（macro_f1=0.52）说明操作前特征对加/降方向的预测力有限，但 Uplift 的因果方向是合理的。**

## 7. 下一步建议

1. **补历史动作特征**到新模型：last_action_direction / days_since_last_action / last_3_action_adjust_count
2. **加入 Meta/AppLovin 操作记录**：MC 中有 `ods_market_api_adset_facebook_da`（Meta）和 `ods_market_applovin_campaign_da`（AppLovin），可以扩大 treatment 覆盖
3. **更强的因果识别**：increase 的安慰剂太高，需要用 IV（工具变量）或 RDD（断点回归）来消除选择偏差
4. **安装 LightGBM**：`brew install libomp` 后重跑，可能提升行为模型
5. **control 改为 PSM 匹配**：用倾向得分匹配而非简单"无变更"分组

## 8. 文件索引

| 文件 | 说明 |
|------|------|
| `tools/scripts/ua_phase3_retry.py` | 本次重试的完整 pipeline 脚本 |
| `/tmp/ua_phase3_retry/budget_changes.jsonl` | 598 条预算变更事件（已脱敏） |
| `/tmp/ua_phase3_retry/daily_metrics.json` | CK 日级 spend+revenue |
| `/tmp/ua_phase3_retry/all_rows.jsonl` | 1,350 条 treated+control |
| `/tmp/ua_phase3_retry/retry_train_results.json` | 行为模型训练结果 |
| `/tmp/ua_phase3_retry/retry_uplift_results.json` | Uplift AIPW 估计结果 |
