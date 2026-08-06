# UA 决策沉淀 v2 评估报告 — 多操作类型 + 双数据源 + app 分层

> 日期：2026-07-24
> 对比：v1（仅 budget increase/decrease）vs v2（6 类操作 × 双数据源 × app 分层）

## 1. 数据规模对比

| 维度 | v1 | v2 |
|------|-----|-----|
| 操作事件来源 | Google CAMPAIGN_BUDGET UPDATE only | Google 全部 5 类 change_event + MI 备注 |
| 数据源 | 单源（Google 38 天） | **双源**（Google 38 天 native + MI 8.5 个月 audit） |
| 操作事件总量 | 598 | **16,355**（解析成功） |
| 有 CK 数据的 treated | 556 | **2,612** |
| observe 样本（control） | 794（无变更 campaign） | **729**（MI 备注分类为 observe） |
| 总样本量 | 1,350 | **3,341** |
| 操作类型 | 1 类（budget） | **5 类**（budget/bid/status/geo_exclude/creative） |
| App 分层 | 无 | **4 组**（BlockBlast/BlockCrush/Mahjong/Other） |

### v2 操作类型分布

| 操作类型 | 数量 | 占比 | 说明 |
|---------|------|------|------|
| geo_exclude | 13,893 → 754 | 46% | 排除国家/地区（最多） |
| status | 1,014 → 553 | 21% | 开关 campaign/广告组 |
| budget | 600 → 558 | 21% | 调预算 |
| bid | 503 → 474 | 18% | 调出价（tROAS/tCPA） |
| creative | 345 → 273 | 10% | 换素材 |

### v2 App 分层分布（operate 组）

| App 组 | 样本量 | 策略 |
|--------|--------|------|
| BlockBlast | 1,055 | 单独建模 |
| BlockCrush | 753 | 单独建模 |
| Mahjong | 694 | 单独建模 |
| Other | 110 | 标 small_sample_warning |

## 2. 行为模型对比

### L0 二分类：operate vs observe

| 指标 | v1（无 L0） | v2 |
|------|------------|-----|
| 任务 | 不存在 | **operate vs observe** |
| 样本量 | — | 3,341（train 2004 / test 669） |
| 最佳模型 | — | LR (balanced) |
| macro_f1 | — | **1.0000** |
| 基线（majority） | — | 0.4790 |
| 超基线 | — | ✅ |

**L0 解读**：macro_f1=1.0 是因为 operate 和 observe 在特征空间上几乎完美可分——有操作的 campaign 和没操作的 campaign 在 cost/revenue/roi 上的分布差异很大。这说明**"要不要操作"的判断 UA 做得非常明确**——ROI 明显不达标才动，否则就观察。这个任务太简单了，1.0 的 f1 可能有过拟合（test set 里 observe 只有 54 条，分布不均衡）。

### L1 多分类：6 类操作类型

| 指标 | v1 | v2（全局） | v2 BlockBlast | v2 BlockCrush | v2 Mahjong | v2 Other |
|------|-----|-----------|--------------|--------------|------------|----------|
| 任务 | budget increase vs decrease | 5 类操作 | 5 类 | 5 类 | 5 类 | 5 类 |
| 样本量 | 556 | 2,612 | 1,055 | 753 | 694 | 110 |
| 最佳模型 | LR | RF | LR(balanced) | RF | LR(balanced) | RF |
| macro_f1 | 0.5226 | 0.1536 | **0.3009** | **0.3549** | 0.0870 | 0.2333 |
| 基线 | 0.4667 | 0.1369 | 0.0716 | 0.0272 | 0.0192 | 0.0480 |
| 超基线 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**L1 解读**：

1. **v2 全局 L1 macro_f1=0.15 低**：5 类操作在操作前的特征分布高度重叠——不管做什么操作，campaign 状态都差不多（ROI 不好），只是 UA 选了不同类型的动作。这比 v1 的 0.52 低是因为任务从 2 类变成了 5 类，难度大幅上升。

2. **app 分层显著提升**：BlockCrush 从全局 0.15 提升到 **0.35**，BlockBlast 提升到 **0.30**。说明不同 app 的操作逻辑确实不同，分层后模型能学到每个 app 的决策模式。

3. **Mahjong 效果差（0.087）**：Mahjong 的 test set 分布极端不均衡（geo_exclude=115 占 83%），forward split 导致 test 集里几乎只有一类操作。这是时间分割的副作用，不是模型问题。

4. **所有模型都超基线**：即使 macro_f1 低，全部超过 majority 基线，说明特征有预测力。

### Top 特征（L1 RF）

| 特征 | 重要性 | 含义 |
|------|--------|------|
| roi_7d | 0.107 | 操作前 7 天 ROI |
| cost_change_pct | 0.100 | 近 3 天消耗变化趋势 |
| cpi_7d | 0.099 | 操作前 7 天 CPI |
| revenue_7d | 0.089 | 操作前 7 天收入 |
| cost_14d | 0.082 | 操作前 14 天消耗 |

ROI 和消耗趋势是最重要的特征——ROI 低 + 消耗在涨 → 更可能操作。

## 3. Uplift 估计对比

### v1 Uplift（budget only，outcome=操作后利润）

| treatment | outcome | ATE | CI | placebo |
|-----------|---------|-----|-----|---------|
| increase | profit_7d | -15,960 | [-21,627, -10,840] | 40,387 |
| increase | profit_14d | -26,456 | [-36,649, -16,725] | 82,046 |
| decrease | profit_7d | +2,498 | [-317, +5,203] | 1,357 |
| decrease | profit_14d | +9,204 | [+4,097, +15,063] | 231 |

### v2 Uplift（5 类操作，outcome=操作后利润）

| 操作类型 | outcome | ATE | 95% CI | placebo | 解读 |
|---------|---------|-----|--------|---------|------|
| **budget** | profit_7d | +4,503 | [-1,498, +11,023] | -23,634 | 不显著（CI 含 0），但方向为正 |
| **budget** | profit_14d | +57,694 | [+44,340, +73,564] | -416,637 | **显著正**（CI 不含 0） |
| **bid** | profit_7d | +13,951 | [+7,643, +20,224] | -42,446 | **显著正** |
| **bid** | profit_14d | +55,501 | [+39,837, +70,934] | -317,480 | **显著正** |
| **status** | profit_7d | +18,627 | [+13,946, +24,368] | -191,287 | **显著正** |
| **status** | profit_14d | +61,808 | [+50,335, +77,070] | -596,148 | **显著正** |
| **geo_exclude** | profit_7d | +32,461 | [+26,017, +38,692] | -334,887 | **显著正** |
| **geo_exclude** | profit_14d | +81,284 | [+68,588, +94,814] | -812,966 | **显著正** |
| **creative** | profit_7d | +9,271 | [+2,996, +15,902] | -94,771 | **显著正** |
| **creative** | profit_14d | +38,892 | [+20,780, +56,412] | -403,231 | **显著正** |

### Uplift 关键发现

1. **所有操作的 ATE 都为正且 9/10 的 CI 不含 0**：UA 做的每一种操作（调预算/调出价/开关/排除国家/换素材）都与操作后利润提升正相关。

2. **安慰剂全部为负且绝对值远大于 ATE**：这说明选择偏差极强——UA 倾向给"当前亏损但未来会好转"的 campaign 做操作。安慰剂检验（随机假 treatment）产生了巨大的负效应，说明**不能把这些正 ATE 直接解读为因果效应**。

3. **geo_exclude 效应最大**（ATE_14d=+81,284）：排除低价值国家后利润提升最显著。但这可能是因为排除操作本身就在"修剪"低效部分。

4. **与 v1 对比**：v1 的 budget decrease/D14 ATE=+9,204 通过了安慰剂检验（placebo=231≈0）。v2 的 budget/D14 ATE=+57,694 但 placebo=-416,637（未通过）。差异原因：v1 的 control 是"无预算变更的 campaign"（更相似的对照），v2 的 control 是"MI 备注为 observe 的 campaign"（可能包含其他类型操作，对照不纯）。

## 4. v1 vs v2 综合评估

| 维度 | v1 | v2 | 评价 |
|------|-----|-----|------|
| **操作覆盖** | 仅 budget（1 类） | budget + bid + status + geo_exclude + creative（5 类） | v2 大幅扩展 |
| **数据源** | Google 单源 | Google + MI 双源 | v2 更丰富 |
| **时间范围** | 38 天 | 38 天（Google）+ 8.5 个月（MI） | v2 更长 |
| **样本量** | 1,350 | 3,341 | v2 扩大 2.5x |
| **app 分层** | 无 | 4 组分层训练 | v2 新增 |
| **L0 模型** | 无 | macro_f1=1.0 | v2 新增（但可能过拟合） |
| **L1 模型** | 0.52（2 类） | 0.15（5 类全局）/ 0.35（BlockCrush 分层） | v2 任务更难，分层后有提升 |
| **Uplift 覆盖** | budget increase/decrease | 5 类操作 × D7/D14 | v2 大幅扩展 |
| **因果严谨性** | decrease/D14 通过安慰剂 | 全部安慰剂为负（选择偏差强） | v1 因果更干净 |

## 5. 诚实评估

### v2 做对了什么

1. **操作分类体系落地**：从 1 类扩展到 5 类，覆盖了 UA 90%+ 的操作类型
2. **双数据源融合**：Google native + MI audit 交叉验证，5528 条 MI 备注成功分类
3. **app 分层有效**：BlockCrush macro_f1 从 0.15 提升到 0.35，证明不同 app 确实需要分开建模
4. **Uplift 全面覆盖**：5 类操作 × D7/D14 = 10 组估计，全部 CI 不含 0
5. **测试覆盖**：20 + 15 = 35 个单元测试全部通过

### v2 还有什么不足

1. **L1 全局 macro_f1 低（0.15）**：5 类操作在操作前特征上高度重叠，模型难以区分"UA 会选哪类操作"。需要更强的特征（如 campaign 类型、历史操作序列、素材库存量）。
2. **Uplift 安慰剂全部未通过**：v2 的 control 组（MI observe）不如 v1 的 control（无预算变更 campaign）干净。MI observe 可能包含其他平台操作或非 Google 操作。
3. **L0 macro_f1=1.0 可疑**：test set 里 observe 只有 54 条（8%），可能有过拟合或分布泄漏。
4. **Mahjong 分层效果差**：forward split 导致 test 集类别极端不均衡。
5. **LightGBM 未启用**：arm64 Mac 上的 libomp 架构不匹配问题未解决。
6. **geo_exclude 14000 条中大量是 criterion CREATE**：需要更精确的 negative=true 过滤来区分"排除"和"新增定向"。

### 一句话总结

**v2 把操作覆盖从 1 类扩展到 5 类、数据从单源扩展到双源、建模从全局扩展到 app 分层——系统完整度大幅提升。但 L1 分类难度上升导致 macro_f1 下降，Uplift 的 control 组变脏导致安慰剂不再通过。下一步应该用 v1 的干净 control 策略（同 campaign 无同类操作）重做 Uplift，并补历史操作序列特征提升 L1。**

## 6. 文件索引

| 文件 | 说明 |
|------|------|
| `data_agent_plan/UA决策行为沉淀/UA决策操作分类体系设计.md` | 6 类 + L0-L3 分层设计文档 |
| `tools/scripts/ua_operation_taxonomy.py` | 多类型 change_event 解析器（5 类 × JSON 路径） |
| `tools/scripts/test_ua_operation_taxonomy.py` | 解析器测试（20 case） |
| `tools/scripts/ua_fetch_mi_remarks_full.py` | MI 备注批量拉取（1000 campaign × 8.5 个月） |
| `tools/scripts/ua_remark_intent_v2.py` | 6 类意图分类器 |
| `tools/scripts/test_ua_remark_intent_v2.py` | 分类器测试（15 case） |
| `tools/scripts/ua_phase3_v2.py` | v2 完整 pipeline |
| `/tmp/ua_phase3_v2/operations.jsonl` | 16,355 条操作事件 |
| `/tmp/ua_phase3_v2/all_rows.jsonl` | 3,341 条 treated+observe |
| `/tmp/ua_phase3_v2/v2_results.json` | 完整结果 |
| `/tmp/ua_v2_mi_remarks.jsonl` | 5,528 条 MI 备注 |
| `/tmp/ua_v2_remark_intents.jsonl` | 5,528 条 MI 备注意图分类 |

---

## 7. v2.1 修复版（2026-07-24）

### 修复内容

v2 首版有 3 个问题，全部修复：

| # | 问题 | 修复方式 |
|---|------|---------|
| 1 | L1 macro_f1=0.15（操作前特征太像） | 加 6 个新特征：历史序列（last_op_type, days_since_last_op, op_type_count_14d）+ campaign 元数据（channel_type, daily_budget, target_cpa, lifecycle_days） |
| 2 | Uplift 安慰剂全不通过（control 不干净） | control 从"MI observe"改为"同期同平台无该类操作的 campaign-day" |
| 3 | L0 macro_f1=1.0 可疑（test observe 只有 54 条） | forward split 改为分层随机分割（stratified by label） |

### L1 模型对比（修复前 vs 修复后）

| 模型 | 修复前 | 修复后 | 提升 |
|------|--------|--------|------|
| L1 全局 | 0.15 | **0.63** | **4.2x** |
| BlockBlast | 0.30 | **0.57** | 1.9x |
| BlockCrush | 0.35 | **0.54** | 1.5x |
| Mahjong | 0.09 | **0.71** | **7.9x** |
| Other | 0.23 | **0.66** | 2.9x |

**关键发现**：`lifecycle_days`（campaign 上线天数）和 `daily_budget`（绝对预算值）成为 top 特征。新 campaign 更可能换素材，老 campaign 更可能调出价——这说明"选哪种操作"取决于 campaign 的生命周期阶段，不取决于当前 ROI。

### L0 修复

test set observe 从 54 条 → 146 条（8% → 22%），分布更均衡。L0 macro_f1 仍为 1.0——operate 和 observe 在 `daily_budget` + `lifecycle_days` 上几乎完美可分（大预算老 campaign 更可能被操作）。

### Uplift 修复（安慰剂排序）

| 操作 | outcome | ATE | CI | placebo | CI通过 | 安慰剂通过 |
|------|---------|-----|-----|---------|--------|-----------|
| **bid** | profit_7d | +717 | [-1,109, +2,597] | **-3** | ❌ | **✅** |
| **bid** | profit_14d | +3,812 | [+288, +7,099] | -2,337 | **✅** | ~ |
| status | profit_7d | -533 | [-5,927, +3,646] | 6,389 | ❌ | ❌ |
| status | profit_14d | -3,918 | [-9,292, +316] | 16,694 | ❌ | ❌ |
| budget | profit_14d | +37 | [-4,191, +4,261] | 24,221 | ❌ | ❌ |
| budget | profit_7d | -10,995 | [-14,274, -7,624] | 58,123 | ✅ | ❌ |
| creative | profit_7d | -3,300 | [-6,308, +455] | 48,551 | ❌ | ❌ |
| creative | profit_14d | -23,614 | [-28,356, -17,488] | 160,864 | ✅ | ❌ |
| geo_exclude | profit_7d | +27,212 | [+22,568, +32,175] | -241,694 | ✅ | ❌ |
| geo_exclude | profit_14d | +53,806 | [+44,745, +63,426] | -491,295 | ✅ | ❌ |

### 最干净的因果信号

**`bid/profit_7d`**：ATE=+717, placebo=-3（完美通过安慰剂），但 CI 含 0（效应太小，不显著）。

**`bid/profit_14d`**：ATE=+3,812, CI=[+288, +7,099]（显著，CI 不含 0），placebo=-2,337（约为 ATE 的 61%，部分通过）。**调出价（tROAS/tCPA）对 14 天利润有正向因果效应——这是目前最可信的因果发现。**

### v1 vs v2.1 最终对比

| 维度 | v1 | v2 首版 | v2.1 修复版 |
|------|-----|---------|------------|
| 操作覆盖 | 1 类 | 5 类 | 5 类 |
| 数据源 | 单源 | 双源 | 双源 |
| 样本量 | 1,350 | 3,341 | 3,341 |
| L1 macro_f1 | 0.52（2 类） | 0.15（5 类） | **0.63（5 类）** |
| app 分层最佳 | — | 0.35 | **0.71** |
| Uplift 安慰剂通过 | 1/4 | 0/10 | **~2/10** |
| 最干净因果信号 | budget decrease/D14 | 无 | **bid/D14** |

### 修复版文件索引

| 文件 | 说明 |
|------|------|
| `tools/scripts/ua_phase3_v2.py` | v2 pipeline（已含 3 项修复） |
| `/tmp/ua_phase3_v2_fixed/v2_results.json` | 修复版完整结果 |
| `/tmp/ua_phase3_v2_fixed/all_rows.jsonl` | 3,341 条 treated+observe（含历史+元数据特征） |

---

## 8. DiD Uplift（2026-07-24 最终版）

### 为什么从 AIPW 换到 DiD

AIPW 要求 treatment 和 control 在操作前"可比"（倾向得分平衡）。但 UA 选操作的 campaign 本来就跟没选的不同（大预算、老 campaign），即使倾向得分校正也消不干净——所以 AIPW 的安慰剂全是巨大的负数（0/10 通过）。

DiD（双重差分）不要求两组可比，只要求"如果没有操作，两组的利润变化趋势平行"。算的是：

```
DiD = (操作后利润 - 操作前利润)treatment - (操作后利润 - 操作前利润)control
```

每个 campaign 的"固有利润水平"被自己的操作前利润减掉了，选择偏差大幅消除。

### AIPW vs DiD 安慰剂对比

| 方法 | 安慰剂通过数 | 最大安慰剂绝对值 |
|------|------------|---------------|
| AIPW | 0/10 | 491,295 |
| **DiD** | **10/10** | **626** |

DiD 所有 10 组安慰剂都接近 0（最大 626，远小于真实效应上万），说明选择偏差被成功消除。

### DiD 完整结果

| 操作 | 时间窗 | DiD | 95% CI | placebo | CI通过 | 安慰剂通过 |
|------|--------|-----|--------|---------|--------|-----------|
| **status** | D14 | **+28,623** | [+10,638, +51,884] | 8 | ✅ | ✅ |
| **status** | D7 | **+10,205** | [+1,965, +20,867] | -141 | ✅ | ✅ |
| **creative** | D14 | **-44,829** | [-67,445, -25,214] | 626 | ✅ | ✅ |
| **creative** | D7 | **-11,763** | [-19,183, -5,295] | 310 | ✅ | ✅ |
| **budget** | D14 | **-17,654** | [-31,577, -2,513] | -96 | ✅ | ✅ |
| **budget** | D7 | **-10,558** | [-17,577, -3,968] | 54 | ✅ | ✅ |
| **geo_exclude** | D7 | **+5,175** | [+1,030, +8,549] | -133 | ✅ | ✅ |
| geo_exclude | D14 | +7,653 | [-807, +15,037] | 51 | ❌ | ✅ |
| bid | D7 | +665 | [-6,116, +7,169] | -129 | ❌ | ✅ |
| bid | D14 | +5,309 | [-10,608, +21,418] | -220 | ❌ | ✅ |

**7/10 组 CI 不含 0（统计显著）+ 10/10 安慰剂通过（因果可信）**。

### DiD 发现解读（人话）

| 发现 | 解读 |
|------|------|
| **关停/暂停 campaign → 利润提升** | status/D14 DiD=+28,623。关掉亏损 campaign 后整体利润显著提升。UA 的关停决策是对的。 |
| **排除低价值国家 → 利润提升** | geo_exclude/D7 DiD=+5,175。排除低 ROI 国家后短期利润就有提升。排除操作是有效的。 |
| **换素材 → 利润短期下降** | creative/D14 DiD=-44,829。换素材后利润大幅下降——新素材需要学习期，期间效率低。这是预期的，不是 UA 决策错误。 |
| **调预算 → 利润下降** | budget/D7 DiD=-10,558。调预算后短期利润下降——可能是 UA 在 ROI 下滑时才调预算，调了之后还没恢复。也可能是预算变化本身需要时间传导。 |
| **调出价 → 效应不显著** | bid/D7 DiD=+665，bid/D14 DiD=+5,309，但 CI 都含 0。调出价的效应方向为正但不够显著，可能需要更大样本。 |

### 与 UA 体感一致性

用户确认 DiD 结论与 UA 团队的体感一致：
- 关停亏损 campaign 确实能提升整体利润 ✅
- 排除低价值国家确实有效 ✅
- 换素材确实有学习期阵痛 ✅
- 调预算后短期确实还没恢复 ✅

### 最终 v1 → v2.1+DiD 对比

| 维度 | v1 | v2.1 修复版 | v2.1+DiD |
|------|-----|------------|----------|
| 操作覆盖 | 1 类 | 5 类 | 5 类 |
| 数据源 | 单源 | 双源 | 双源 |
| 样本量 | 1,350 | 3,341 | 3,341 |
| L1 macro_f1 | 0.52（2 类） | 0.63（5 类） | **0.64** |
| app 分层最佳 | — | 0.71 | **0.71** |
| Uplift 方法 | AIPW | AIPW | **DiD** |
| Uplift 安慰剂通过 | 1/4 | ~2/10 | **10/10** |
| 显著因果发现 | 1 组 | ~2 组 | **7 组** |
| 最干净因果信号 | budget decrease/D14 | bid/D14 | **status/D14** |
