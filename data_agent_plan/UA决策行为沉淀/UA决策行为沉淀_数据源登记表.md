# UA 决策行为沉淀 — 数据源登记表

> 日期：2026-07-24
> 用途：记录 UA 沉淀项目所有可用数据源，标注"已用"和"未用"，方便后续拼接完整数据集合。

## 1. 三平台操作记录来源

### 1.1 Google

| 来源 | 类型 | 表/接口 | 在用？ | 说明 |
|---|---|---|---|---|
| Google 原生 change_event 宽表 | MC 表 | `ods_market_google_ads_config_wide_hi` | **❌ 未用** | 有真实 before/after 数值（`change_event_old_resource`/`change_event_new_resource`），精确到秒的操作时间。这是 Google 预算操作的**首选事实源**，当前模型完全没有用到 |
| MI ua-operates（操作日志） | MI 接口 | `GET /api/boards/reports/campaign-govern/ua-operates` | ✅ 已用 | 文字描述操作内容，如"将目标 ROAS 从 0.20 调整为 0.17"，5 个字段。已落地 MC 表 `ods_mi_campaign_operation_observation_hi`（209 条） |
| MI ua-remarks（备注） | MI 接口 | `GET /api/boards/reports/campaign-govern/ua-remarks` | ✅ 已用 | UA 填写的备注判断，用于提取 `human_decision` 标签。已落地 MC 表 `ods_mi_campaign_remark_observation_hi`（2772 条） |
| Google Campaign 配置快照 | MC 表 | `ods_market_google_campaign_da` | ✅ 已用 | 用于构建 DecisionSubject SCD，获取 `budget_id`/`budget_explicitly_shared` |

**关键缺口**：Google change_event 宽表有 `amountMicros` 的真实 before/after，可以精确计算 `change_pct`，而且有 80 条 CAMPAIGN_BUDGET UPDATE 记录。当前模型只用 MI 文字描述，损失了精确的数值信息。

### 1.2 Meta

| 来源 | 类型 | 表/接口 | 在用？ | 说明 |
|---|---|---|---|---|
| MI ua-operates | MI 接口 | 同上 | ✅ 已用 | Meta 操作也通过 MI 记录，但操作来源是 `[XMP-30]`（通过 XMP 工具操作）或 Meta 后台 |
| MI ua-remarks | MI 接口 | 同上 | ✅ 已用 | 备注判断 |
| Meta Campaign 配置快照 | MC 表 | `ods_market_meta_campaign_da` | ✅ 探测过，未用于训练 | 日快照，有 daily_budget/lifetime_budget |
| Meta AdSet 配置快照 | MC 表 | `ods_market_api_adset_facebook_da` | ✅ 探测过，未用于训练 | 有 daily_budget/lifetime_budget |
| Meta CK 投影 | CK 表 | `market_api_campaign_info_facebook_dist` / `market_api_adset_info_facebook_dist` | ✅ 探测过 | 有 `budget_type`（DAILY/LIFETIME/NONE），可区分 CBO/ABO |
| Meta 原生操作记录 | MC 表 | `ods_market_facebook_activity_hi` | ✅ 2026-07-29 探测并准入 | Meta Ads API activities 小时级，2026-06-23 起采集；object_type 历史命名 |
| Meta 操作+配置宽表 | MC 表 | `ods_market_facebook_ads_config_wide_hi` | ✅ 2026-07-29 探测并准入 | activity × Campaign/AdSet/Ad/Creative 拉宽；与 Google config_wide 对等 |
| Meta Creative 快照 | MC 表 | `ods_market_facebook_creative_da` | ✅ 2026-07-29 探测并准入 | 素材标题/正文/图片/视频/CTA 日快照 |

### 1.3 AppLovin

| 来源 | 类型 | 表/接口 | 在用？ | 说明 |
|---|---|---|---|---|
| MI ua-operates | MI 接口 | 同上 | ❌ 探测过，无数据 | AppLovin 操作在 MI 里**完全没有记录**（用户确认：手动下载） |
| MI ua-remarks | MI 接口 | 同上 | ❌ 未用于训练 | 有备注但无操作记录，无法形成完整的操作→标签配对 |
| AppLovin Campaign 配置快照 | MC 表 | `ods_market_applovin_campaign_da` | ❌ 未用 | `budget` 字段是 JSON，有 `country_code_to_daily_budget` |
| AppLovin CK 投影 | CK 表 | `market_api_campaigns_v2` | ❌ 未用 | |

## 2. 投放事实数据（消耗/收入/留存）

| 来源 | 类型 | 表 | 在用？ | 说明 |
|---|---|---|---|---|
| 消耗 | CK 表 | `tj_ad_spend_active_v2` | ✅ 用于特征 | 提取 cost_7d/14d, shows, clicks, registers, currency |
| AF 收入 | CK 表 | `tj_ad_revenue_v2` | ✅ 用于特征 | 提取 revenue_7d, roi_7d |
| SDK 收入 | CK 表 | `tj_ad_sdk_revenue` | ❌ 未用 | 方案指定默认收入源，当前用 AF revenue |
| AF cohort 留存 | CK 表 | `af_cohort_user_acquisition_v2` | ❌ 未用 | 可用于 retention 特征和 Outcome 回填 |
| ROI 预测 | CK 表 | `market_roi_prediction_360_v6_da` | ❌ 未用 | 有版本化（同一 active_date 多个 dt），可做 forecast 特征 |

## 3. 特征构建用的 CK 表和字段

当前模型（Phase 3 真实训练）只用到了以下 CK 表：

| CK 表 | 用到的字段 | 聚合方式 | 窗口 |
|---|---|---|---|
| `tj_ad_spend_active_v2` | `cost_zhe, currency, registers, shows, clicks, active_date, campaign_name, media_source` | SUM | 7 天 / 14 天 |
| `tj_ad_revenue_v2` | `revenue, active_date, campaign_name, media_source` | SUM | 7 天 |

## 4. 当前模型实际用到的数据全景

```
                    ┌─────────────────────────┐
                    │  Google change_event 宽表  │  ← ❌ 未用（最大缺口）
                    │  ods_market_google_        │
                    │  ads_config_wide_hi        │
                    │  有真实 before/after       │
                    └─────────────────────────┘
                    
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│  MI ua-operates    │    │  MI ua-remarks     │    │  CK Spend/Revenue  │
│  （操作日志）       │    │  （备注判断）       │    │  （投放事实）       │
│  ✅ 已用            │    │  ✅ 已用            │    │  ✅ 已用            │
│  209条 → MC        │    │  2772条 → MC       │    │  7天/14天 聚合     │
└─────────┬─────────┘    └─────────┬─────────┘    └──────────┬────────┘
          │                        │                         │
          ▼                        ▼                         ▼
    操作记录                  备注文本 → 规则分类         特征提取
   (observed_              (human_decision:           (cost_7d, roi_7d,
    treatment)              adjust_budget /            cpi_7d, ctr_7d,
                            continue_observe)          cvr_7d 等 12 维)
          │                        │                         │
          └────────────────────────┼─────────────────────────┘
                                   │
                                   ▼
                          4511 条 Episode
                          (2403 adjust + 2108 observe)
                                   │
                                   ▼
                         Phase 3 行为模型训练
                         macro_f1 = 0.79
                                   │
                                   ▼
                         Phase 4 Uplift 估计
                         AIPW ATE = 1190
```

## 5. 建议下一步拼接的完整数据集合

把以下三部分拼在一起，形成**完整数据集合**：

1. **操作事实**（从 Google change_event 宽表）：before/after 数值、精确时间、操作类型
2. **决策意图**（从 MI ua-remarks + 规则分类）：human_decision 标签
3. **投放特征**（从 CK spend/revenue）：消耗/ROI/CPI/CTR/CVR 滚动窗口

```
change_event 宽表 (before/after) 
    ↔ campaign_name ↔ 
MI ua-remarks (human_decision) 
    ↔ campaign_name + date ↔ 
CK spend/revenue (特征)
```
