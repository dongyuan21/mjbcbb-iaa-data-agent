# UA 决策操作分类体系设计

> 日期：2026-07-24
> 状态：design_approved
> 上游：`UA决策行为沉淀与回测方案.md` v0.3 §5.2 (标签体系) + §8.13 (objective_code)
> 本文档定义 UA 操作的 4 层分类体系和 6 类操作类型，作为 v2 pipeline 的 canonical 定义。

## 1. 为什么需要操作分类体系

v1 只做了"加预算 vs 降预算"二分类。但 UA 的实际操作远不止预算调整——从 Google change_event 38 天数据和 MI 备注 8.5 个月数据看，UA 至少做 6 类操作，且经常一次操作里同时做多件事（如"提高goal值+降低预算+排除国家"）。

不做分类的后果：
- 行为模型只学到预算决策，丢失了 80%+ 的操作信息
- Uplift 只能估计预算调整的效应，无法回答"排除某国家后利润变了吗"
- 无法区分"什么都不做的观察"和"做了操作"，两者在 v1 里被混在 control 里

## 2. 4 层分类体系

```
L0: operate / observe                    ← 有没有做操作
L1: budget / bid / status / geo_exclude / creative / compound  ← 操作大类
L2: increase / decrease / pause / enable / exclude / add / change  ← 操作方向
L3: large / small / no_change            ← 操作幅度 (change_pct 分桶, ±30%)
```

### L0：有没有做操作

| 值 | 定义 | 数据来源 |
|----|------|---------|
| `operate` | 该 campaign 在该时间点有至少 1 条 Google change_event UPDATE/CREATE/REMOVE | Google change_event |
| `observe` | 该 campaign 在该时间点有 MI 备注，但无对应 Google 操作 | MI 备注（无 Google 匹配） |

L0 是行为模型最有区分度的任务——UA 大部分时间在"看"，少数时间在"动"。

### L1：操作大类

| 值 | Google resource_type | changed_fields | 38天样本 | before/after 值 | 说明 |
|----|---------------------|---------------|---------|----------------|------|
| `budget` | `CAMPAIGN_BUDGET` | `amountMicros` | 598 | ✅ 精确金额 | 调日预算 |
| `bid` | `CAMPAIGN` | `targetRoas.targetRoas` 或 `targetCpa.targetCpaMicros` | 494 | ✅ 精确出价 | 调 tROAS/tCPA 目标 |
| `status` | `CAMPAIGN` / `AD_GROUP` | `status` | 1014 | ✅ enum 状态 | 开关 campaign/广告组 |
| `geo_exclude` | `CAMPAIGN_CRITERION` | `criterionId,negative` | ~14000 | ⚠️ 需 join 维度表 | 排除/新增国家定向 |
| `creative` | `AD` / `AD_GROUP_AD` | `appAd.headlines/descriptions` | ~400 | ⚠️ 文本 diff | 换标题/描述/素材 |
| `compound` | 多种 | 多种 | — | — | 同一天同 campaign 有 2+ 类操作 |

### L2：操作方向

| L1 类别 | L2 方向 | 判定逻辑 |
|---------|---------|---------|
| budget | `increase` / `decrease` | `new_amount > old_amount` → increase |
| bid (targetRoas) | `increase` / `decrease` | `new_roas > old_roas` → increase（注意：tROAS 提高 = 更激进投放） |
| bid (targetCpa) | `increase` / `decrease` | `new_cpa > old_cpa` → increase（注意：tCPA 提高 = 更宽松） |
| status | `pause` / `enable` / `remove` | `old=ENABLED→new=PAUSED` = pause；反向 = enable；→REMOVED = remove |
| geo_exclude | `exclude` / `add` | `negative=true` + CREATE = exclude；REMOVE negative = 取消排除 |
| creative | `change` | 有文本变更即标 change |

### L3：操作幅度

| 值 | 定义 | 适用类型 |
|----|------|---------|
| `large` | `|change_pct| >= 30%` | budget, bid |
| `small` | `0 < |change_pct| < 30%` | budget, bid |
| `no_change` | `change_pct == 0` | budget, bid（理论上不应出现，防御性处理） |
| `n/a` | 不适用 | status, geo_exclude, creative（非数值变更） |

阈值版本：`action_band_v0.1`（与 Phase0 预算动作分桶报告一致）。

## 3. JSON 解析路径（已验证）

以下路径已通过 MC 在线探测验证（2026-07-24）：

### budget (CAMPAIGN_BUDGET UPDATE)
```json
old: {"campaignBudget": {"amountMicros": "4700000000"}}
new: {"campaignBudget": {"amountMicros": "3900000000"}}
```
- 路径：`$.campaignBudget.amountMicros`
- 单位：micros，÷1e6 转货币
- change_pct = (new - old) / old

### bid - targetRoas (CAMPAIGN UPDATE)
```json
old: {"campaign": {"targetRoas": {"targetRoas": 0.29}}}
new: {"campaign": {"targetRoas": {"targetRoas": 0.27}}}
```
- 路径：`$.campaign.targetRoas.targetRoas`
- 单位：分数（如 0.29 = 29% tROAS），**不÷1e6**
- change_pct = (new - old) / old

### bid - targetCpa (CAMPAIGN UPDATE)
```json
old: {"campaign": {"targetCpa": {"targetCpaMicros": "10000000"}}
new: {"campaign": {"targetCpa": {"targetCpaMicros": "12000000"}}
```
- 路径：`$.campaign.targetCpa.targetCpaMicros`
- 单位：micros，÷1e6 转货币
- change_pct = (new - old) / old

### status (CAMPAIGN UPDATE)
```json
old: {"campaign": {"status": "PAUSED"}}
new: {"campaign": {"status": "ENABLED"}}
```
- 路径：`$.campaign.status`
- 值：ENABLED / PAUSED / REMOVED
- direction: ENABLED→PAUSED=pause, PAUSED→ENABLED=enable, *→REMOVED=remove

### status (AD_GROUP UPDATE)
```json
old: {"adGroup": {"status": "ENABLED"}}
new: {"adGroup": {"status": "PAUSED"}}
```
- 路径：`$.adGroup.status`（注意 key 是 adGroup 不是 campaign）
- 其余同上

### geo_exclude (CAMPAIGN_CRITERION CREATE/REMOVE)
```json
CREATE new: {"campaignCriterion": {"criterionId": "2124", "negative": true}}
REMOVE old: {"campaignCriterion": {"criterionId": "2158", "negative": false}}
```
- 路径：`$.campaignCriterion.criterionId` + `$.campaignCriterion.negative`
- **注意**：JSON 中**没有 geoName**，只有 criterionId（数字 ID）
- criterionId → 国家名需要 join 维度表 `ods_market_google_campaign_criterion_da`（有 `geo_name` 列）
- direction: CREATE + negative=true → exclude; REMOVE → 取消排除

### creative (AD UPDATE)
```json
old: {"adGroupAd": {"ad": {"appAd": {"headlines": [{"text": "旧标题"}]}}}}
new: {"adGroupAd": {"ad": {"appAd": {"headlines": [{"text": "新标题"}]}}}}
```
- 路径：`$.adGroupAd.ad.appAd.headlines[N].text` + `$.adGroupAd.ad.appAd.descriptions[N].text`
- 不做文本相似度，只标 `change=True` 并记录变更字段列表

## 4. MI 备注意图分类（6 类关键词规则）

MI 备注是纯文本，需要用关键词规则提取操作类型。扩展 v1 分类器（4 类 → 6 类）：

| L1 类别 | 关键词列表（部分） | 置信度 |
|---------|-------------------|--------|
| `budget` | 下调预算/加预算/放量/缩量/降低预算/提高预算/预算未撞线/当前预算 | medium |
| `bid` | 提高goal值/降低目标/调出价/tROAS/tCPA/target/目标ROAS/goal值 | medium |
| `status` | 关停/暂停/开启/恢复/停投/重新开启/重新启用 | medium |
| `geo_exclude` | 排除/移除国家/排除DE/排除低ROI国家/排除捷克/拆分国家/排除广告组 | medium |
| `creative` | 补充素材/换标题/换描述/新素材/补充无wifi方向素材/素材测试 | medium |
| `observe` | 持续关注/暂不调整/继续观察/维稳/未撞线/稳定/无幅度调整 | medium |

复合操作（如"提高goal值+降低预算+排除国家"）标 `compound` 并记录所有命中的类别列表。

MI 备注的 `【】` 前缀标签仍然有用：
- `【有增量空间】` → 可能伴随 budget increase 或 bid increase
- `【向N%+目标优化】` → 可能伴随 bid decrease 或 budget decrease
- `【达标但需维稳】` → observe

## 5. App 分层策略

使用 `knowledge/agent_knowledge/report_knowledge/PACKAGE_BUNDLE_MAP.csv` 映射。

| App 组 | bundle_id 列表 | v1 样本量 | v2 策略 |
|--------|---------------|----------|---------|
| Block Blast (安卓) | `com.block.juggle` | 232 | 单独建模 |
| Block Crush (安卓+iOS) | `com.wood.block.sudoku.puzzle.bm`, `com.blockcrush.travelmaster` | 159 | 合并建模 |
| Mahjong (MJ+DoubleTile+Jade) | `com.nebula.mahjongtile`, `com.hungrystudio.mahjong`, `com.wonderful.mahjong` | 171 | 合并建模 |
| 其他 | Sudoku, Arrows 等 | <30 | 标 `small_sample_warning`，只预警不建模 |

## 6. 双数据源交叉验证规则

| 场景 | Google change_event | MI 备注 | 结论 |
|------|--------------------|---------|------? |
| A | 有 budget decrease | 说"降低预算" | ✅ 高置信 decrease |
| B | 有 geo_exclude | 说"排除DE" | ✅ 高置信 exclude |
| C | 无操作 | 说"持续关注" | ✅ observe |
| D | 有 budget increase | 说"加预算" | ✅ 高置信 increase |
| E | 有 budget decrease | 说"持续关注"（没提预算） | ⚠️ 以 Google 为准（native > audit） |
| F | 无操作 | 说"排除低ROI国家" | ⚠️ MI 有但 Google 无（可能操作在 38 天窗口外，或非 Google 平台操作） |
| G | 有 status pause | 无备注 | ⚠️ Google 有但 MI 无（可能是自动规则或 MI 未记录） |

置信度优先级：`native (Google) > audit (MI) > inferred_only > unknown`

## 7. 与 v1 的关系

- v1 的 `observed_treatment` 6 桶（no_budget_change / budget_decrease_large / ...）对应 v2 的 L1=budget + L3 幅度分桶
- v1 的 `human_decision` 4 类（continue_observe / adjust_budget / need_data / unobserved）对应 v2 的 L0 + 部分 L1
- v2 扩展了 bid/status/geo_exclude/creative 四个新维度，v1 的 budget 维度保留不变
- v2 新增 app 分层，v1 是全局模型

## 8. 版本

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-07-24 | 初版：6 类操作 + 4 层分类 + 双数据源 + app 分层 |
