# Verified SQL: IAA 事件点位测试 - 事件渗透率 + ROI/LTV/倍率趋势

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260715_iaa_event_point_roi_ltv_trend` |
| 状态 | verified |
| promotion_status | verified_sql |
| sql_status | verified |
| 运行来源 | 本文档 `### Canonical SQL` 下唯一的 `sql` fence |
| 关联 SOP | `../analysis_sop/202604_IAA事件点位测试分层评估SOP.md` |
| 适用场景 | 评估新事件点位：渗透率是否够模型学习、首日 ROI vs 长线倍率、360 ROI 是否可回本 |
| 最后验证 | 2026-07-15 |
| validation_method | manual_small_window |
| owner | Cursor Agent |
| supersedes | [] |
| 源 candidate | `candidate_sql/iaa_event_point_roi_ltv_trend.sql`（晋升后已移除） |

## 原始问题

> 评估新事件点位是否值得测试：渗透率是否够模型学习、首日 ROI 低但长线倍率高是否可继续、点位是否能支撑 360 ROI，避免只按首日 ROI 或单一 CPI 结论做取舍。

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | `active_date` 按日 |
| 粒度 | `bundle_id × s2s_event × media_source × campaign_name × active_date`（dim_level=bundle_media_campaign） |
| 渗透率 | 该事件 campaign 的 registers / 同包体同日全媒体 registers（不含 organic） |
| LTV_0 | `sdk_revenue_day1 / registers` |
| LTV_7 | `sdk_revenue_day7 / registers` |
| LTV_30 | `sdk_revenue_day30 / registers` |
| 倍率 | `sdk_revenue_day30 / sdk_revenue_day1` |
| ROI_D1 | `sdk_revenue_day1 / cost_zhe * 100` |
| ROI_D360 | `sdk_revenue_day360 / cost_zhe * 100`（预估补全口径） |
| 样本质量 | registers < 100 → small_sample_needs_caution; < 500 → marginal_sample; 否则 sufficient_sample |

## 依赖表

| 表 | 用途 |
|---|---|
| `shucang_market.ads_market_roi_cohort_sdk_multidim` | ROI cohort 多维宽表（dim_level=bundle_media_campaign + bundle_media） |
| `shucang_market.dim_market_campaign_s2s_event_map_da` | S2S 事件映射，campaign → s2s_event 关联 |

## 复用参数

| 参数 | 说明 |
|---|---|
| `${start_date}` | 窗口起始日，如 `2026-07-08` |
| `${end_date}` | 窗口结束日，如 `2026-07-14` |
| `${bundle_ids}` | 包体列表，如 `'com.kcolb.juggle'` |

## 风险与陷阱

- S2S 事件映射按 `campaign_id` 关联，若 campaign 未配置 `s2s_event` 则该 campaign 不出现。
- `sdk_revenue_day360` 为**预估补全**，非真实回收；ROI_D360 仅作参考。
- 渗透率分母用同包体同日全媒体 registers（不含 organic），与 MI 页面口径可能不同。
- 小样本事件（registers < 100）已标记 `small_sample_needs_caution`，不直接用于决策。
- 事件重叠率需额外查询，本 SQL 只做单事件维度评估。
- 不输出用户级明细，无 PII 风险。

## 验证记录

### 2026-07-15 · ClickHouse 实时探测

探测：`ads_market_roi_cohort_sdk_multidim` max(active_date)=2026-07-14；`dim_market_campaign_s2s_event_map_da` 有数据。

| 验证批次 | 窗口 | 行数 | 结果摘要 |
|---|---|---|---|
| smoke-1 | 2026-07-08..2026-07-14 | 10 行 | RevMix_D7_bb × googleadwords_int: registers=545, penetration=0.025%, ltv0=0.0116, ltv30=0.0608, multiplier=5.22, roi_d1=5.26%, roi_d360=69.84% |

样例数据：

| s2s_event | media_source | registers | penetration | ltv0 | ltv30 | multiplier | roi_d360 | sample_quality |
|---|---|---|---|---|---|---|---|---|
| RevMix_D7_bb | googleadwords_int | 545 | 0.025% | 0.0116 | 0.0608 | 5.22 | 69.84% | sufficient_sample |
| RevMix_D7_bb | googleadwords_int | 402 | 0.021% | 0.0070 | 0.0296 | 4.21 | 26.71% | marginal_sample |
| RevMix_D7_bb | googleadwords_int | 495 | 0.020% | 0.0050 | 0.0218 | 4.32 | 34.80% | marginal_sample |

验证确认：S2S 事件关联正确，渗透率/LTV/倍率/ROI/样本质量标记全部正常输出。

## SQL

### Canonical SQL

```sql
/* IAA_EVENT_POINT_ROI_LTV_TREND */
WITH
    event_mapped AS (
        SELECT
            bundle_id,
            media_source,
            campaign_id,
            campaign_name,
            s2s_event
        FROM shucang_market.dim_market_campaign_s2s_event_map_da
        WHERE s2s_event IS NOT NULL
          AND s2s_event <> ''
          AND bundle_id IN (${bundle_ids})
    ),
    roi_data AS (
        SELECT
            bundle_id,
            media_source,
            campaign_id,
            campaign_name,
            active_date,
            actual_roi_days,
            sum(toFloat64(cost_zhe)) AS total_cost_zhe,
            sum(toFloat64(registers)) AS total_registers,
            sum(toFloat64(sdk_revenue_day1)) AS sdk_rev_d1,
            sum(toFloat64(sdk_revenue_day7)) AS sdk_rev_d7,
            sum(toFloat64(sdk_revenue_day30)) AS sdk_rev_d30,
            sum(toFloat64(sdk_revenue_day360)) AS sdk_rev_d360
        FROM shucang_market.ads_market_roi_cohort_sdk_multidim
        WHERE active_date BETWEEN '${start_date}' AND '${end_date}'
          AND dim_level = 'bundle_media_campaign'
          AND bundle_id IN (${bundle_ids})
          AND media_source NOT IN ('all', '')
        GROUP BY
            bundle_id,
            media_source,
            campaign_id,
            campaign_name,
            active_date,
            actual_roi_days
    ),
    total_registers AS (
        SELECT
            bundle_id,
            active_date,
            sum(toFloat64(registers)) AS all_registers
        FROM shucang_market.ads_market_roi_cohort_sdk_multidim
        WHERE active_date BETWEEN '${start_date}' AND '${end_date}'
          AND dim_level = 'bundle_media'
          AND bundle_id IN (${bundle_ids})
          AND media_source NOT IN ('all', '')
        GROUP BY
            bundle_id,
            active_date
    )
SELECT
    r.bundle_id,
    e.s2s_event,
    r.media_source,
    r.campaign_name,
    r.active_date,
    r.actual_roi_days,
    r.total_cost_zhe,
    r.total_registers,
    round(r.total_registers / nullIf(t.all_registers, 0), 6) AS penetration_rate,
    round(r.sdk_rev_d1 / nullIf(r.total_registers, 0), 6) AS ltv0,
    round(r.sdk_rev_d7 / nullIf(r.total_registers, 0), 6) AS ltv7,
    round(r.sdk_rev_d30 / nullIf(r.total_registers, 0), 6) AS ltv30,
    round(r.sdk_rev_d30 / nullIf(r.sdk_rev_d1, 0), 4) AS multiplier_d30_over_d1,
    round(r.sdk_rev_d1 / nullIf(r.total_cost_zhe, 0) * 100, 4) AS roi_d1_pct,
    round(r.sdk_rev_d30 / nullIf(r.total_cost_zhe, 0) * 100, 4) AS roi_d30_pct,
    round(r.sdk_rev_d360 / nullIf(r.total_cost_zhe, 0) * 100, 4) AS roi_d360_pct,
    multiIf(
        r.total_registers < 100, 'small_sample_needs_caution',
        r.total_registers < 500, 'marginal_sample',
        'sufficient_sample'
    ) AS sample_quality
FROM roi_data AS r
INNER JOIN event_mapped AS e
    ON r.bundle_id = e.bundle_id
   AND r.media_source = e.media_source
   AND r.campaign_id = e.campaign_id
LEFT JOIN total_registers AS t
    ON r.bundle_id = t.bundle_id
   AND r.active_date = t.active_date
ORDER BY
    r.bundle_id,
    e.s2s_event,
    r.active_date,
    r.total_cost_zhe DESC
LIMIT 500
```
