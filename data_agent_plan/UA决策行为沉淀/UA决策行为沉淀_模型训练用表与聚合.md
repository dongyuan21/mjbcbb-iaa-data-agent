# UA 决策行为沉淀 — 模型训练用表与聚合方式

> 日期：2026-07-24
> 用途：记录 Phase 3 行为模型 + Phase 4 Uplift 训练中用到的所有表和聚合方式，配合"数据源登记表"形成完整数据全景。

## 1. 模型训练中实际用到的表

### 1.1 标签来源：MI 备注

| 环节 | 表/接口 | 说明 |
|---|---|---|
| 原始数据 | MI `GET /api/boards/reports/campaign-govern/ua-remarks` | 6426 条备注（200 个 Campaign × 12 个月） |
| 标签提取 | `tools/scripts/ua_remark_intent.py`（规则分类器） | 从备注 description 文本提取 human_decision：adjust_budget 2403 条 / continue_observe 2108 条 / unknown 1915 条（丢弃） |
| 落地 MC | `ods_mi_campaign_remark_observation_hi`（hs_market） | 2772 条（dt=2026-06-30）+ 更多条（dt=2026-01-01） |

**标签分类规则**：
- `【有增量空间】` → adjust_budget（高 confidence）
- `【有增量空间但需维稳】` → continue_observe（高 confidence）
- `【向xx%+目标优化】` → adjust_budget（高 confidence）
- 正文含"下调预算"/"放量"/"加预算" → adjust_budget（中 confidence）
- 正文含"持续关注"/"维稳"/"暂不调整" → continue_observe（中 confidence）
- 只有数据描述无动作词 → continue_observe（低 confidence）

### 1.2 特征来源：CK 投放数据

| CK 表 | 用到的字段 | 聚合方式 | 窗口 | 产出的特征 |
|---|---|---|---|---|
| `shucang_market.tj_ad_spend_active_v2` | `cost_zhe` | SUM | 7 天 / 14 天 | `cost_7d`, `cost_14d` |
| 同上 | `currency` | SUM | 7 天 | 配合 cost_zhe 计算美元消耗 |
| 同上 | `registers` | SUM | 7 天 | `registers_7d` |
| 同上 | `shows` | SUM | 7 天 | `shows_7d` |
| 同上 | `clicks` | SUM | 7 天 | `clicks_7d` |
| `shucang_market.tj_ad_revenue_v2` | `revenue` | SUM | 7 天 | `revenue_7d` |

**派生特征**（在 Python 里计算，不是 CK SQL）：
| 派生特征 | 公式 | 来源 |
|---|---|---|
| `roi_7d` | `revenue_7d / cost_7d` | spend + revenue |
| `cpi_7d` | `cost_7d / registers_7d` | spend |
| `ctr_7d` | `clicks_7d / shows_7d` | spend |
| `cvr_7d` | `registers_7d / clicks_7d` | spend |
| `cost_change_pct` | `(cost_3d_recent - cost_3d_before) / cost_3d_before` | spend |
| `roi_change_pct` | `(roi_3d_recent - roi_3d_before) / roi_3d_before` | spend + revenue |

**聚合 SQL 示例**（实际使用的查询结构）：
```sql
-- 7 天消耗聚合
SELECT campaign_name,
  sum(cost_zhe) / nullIf(sum(currency), 0) as cost_7d,
  sum(registers) as registers_7d,
  sum(shows) as shows_7d,
  sum(clicks) as clicks_7d
FROM shucang_market.tj_ad_spend_active_v2
WHERE active_date >= '<remark_date - 7>'
  AND active_date <= '<remark_date>'
  AND media_source = 'googleadwords_int'
GROUP BY campaign_name

-- 7 天收入聚合
SELECT campaign_name, sum(revenue) as revenue_7d
FROM shucang_market.tj_ad_revenue_v2
WHERE active_date >= '<remark_date - 7>'
  AND active_date <= '<remark_date>'
  AND media_source = 'googleadwords_int'
GROUP BY campaign_name
```

**聚合粒度**：`campaign_name`，按备注日期（`remark_date`）作为 as_of_ts。每个备注日期对应一条 feature_snapshot。

### 1.3 没用到的表（缺口）

| 表 | 为什么没用 | 应该用来做什么 | 优先级 |
|---|---|---|---|
| `ods_market_google_ads_config_wide_hi` | **最大缺口** | 真实 before/after 数值 + 精确时间，替代 MI 文字描述 | 🔴 最高 |
| `ods_market_google_campaign_da` | 探测过但没用 | DecisionSubject 身份映射（campaign_id、shared budget 标识） | 🟡 高 |
| `tj_ad_sdk_revenue` | 用了 AF revenue 替代 | SDK 收入（方案指定默认源） | 🟡 高 |
| `af_cohort_user_acquisition_v2` | 没用 | retention 特征、D7/D14 Outcome 回填 | 🟡 高 |
| `market_roi_prediction_360_v6_da` | 没用 | forecast ROI 特征（需版本冻结） | 🟢 中 |
| `ods_market_meta_campaign_da` | 没用 | Meta Campaign 配置 | 🟢 中 |
| `ods_market_api_adset_facebook_da` | 没用 | Meta AdSet 配置（ABO 场景） | 🟢 中 |

### 1.4 特征工程辅助表（Python 侧）

| 来源 | 说明 |
|---|---|
| `data_agent_plan/UA决策行为沉淀/ua_phase3_run/top200_campaigns.json` | CK 查询出的 Top 200 Google Campaign 列表 |
| `data_agent_plan/UA决策行为沉淀/ua_phase3_run/ua_remarks.jsonl` | MI 拉取的 6426 条备注原文 |
| `data_agent_plan/UA决策行为沉淀/ua_phase3_run/remark_intent.jsonl` | 规则分类后的标签 |
| `data_agent_plan/UA决策行为沉淀/ua_phase3_run/feature_snapshots.jsonl` | 6426 条 feature_snapshot（12 维特征） |
| `data_agent_plan/UA决策行为沉淀/ua_phase3_run/episodes.jsonl` | 4511 条 Episode（标签+特征合并后，弃 unknown） |

## 2. 模型训练的 train/val/test 切分

**切分方式**：forward holdout（按时间顺序，防止未来泄漏）

| 数据集 | 样本量 | 占比 |
|---|---|---|
| train | 2706 | 60% |
| val | 902 | 20% |
| test | 903 | 20% |
| **合计** | **4511** | — |

**标签分布**（二分类，need_data=0）：
| 标签 | train | test |
|---|---|---|
| adjust_budget | ~1442 | ~481 |
| continue_observe | ~1264 | ~422 |

## 3. 数据对齐方式

每条 Episode 通过 `campaign_name + remark_date` 对齐以下三个来源：

```
remark_date: 2026-06-15
campaign_name: "US-035-HK-XH-TachiPer045-横-260602"

1. 备注文本 (MI ua-remarks)
   → "【有增量空间】7日360ROI均值108%..."
   → human_decision = adjust_budget

2. CK 特征 (tj_ad_spend_active_v2 + tj_ad_revenue_v2)
   → active_date ∈ [2026-06-08, 2026-06-15]
   → cost_7d=1484, roi_7d=25.0, cpi_7d=0.11, ...

3. 操作类型 (observed_treatment)
   → 同 Campaign 在 remark_date 附近是否有 MI ua-operates 记录
   → 有 → adjust_budget; 无 → no_budget_change
```

## 4. 完整数据集合拼接路线（下一步）

把当前用到的 MI 数据 + **还没用到的 Google change_event 宽表** + CK 特征拼起来：

```text
Step 1: Google change_event 宽表（ods_market_google_ads_config_wide_hi）
         ↓ 提取 campaign_id, change_event_change_date_time, old_amountMicros, new_amountMicros
         ↓ 计算 change_pct, observed_treatment
         
Step 2: MI ua-remarks
         ↓ 规则分类 → human_decision

Step 3: campaign_name ↔ campaign_id 映射（通过 ods_market_google_campaign_da）

Step 4: CK Spend/Revenue 特征（按 change_event 日期窗口聚合）

Step 5: 拼接 → Episode（有精确 before/after + 标签 + 真实特征）
```

**预期收益**：
- `observed_treatment` 从文字推断变为精确数值（change_pct）
- 可以区分 budget_increase_large/small/decrease（不再笼统 adjust_budget）
- 可以缩小时间窗口到精确操作时间（秒级），而不是天级
