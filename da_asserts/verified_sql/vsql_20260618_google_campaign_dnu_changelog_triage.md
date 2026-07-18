# Google campaign DNU 异动与 change log 联查

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260618_google_campaign_dnu_changelog_triage` |
| 状态 | verified |
| 来源 | `../analysis_sop/20260618_GoogleCampaignDNU异动排查SOP.md` |
| 适用场景 | Google DNU / campaign 下滑后，联查同期 Google Ads 预算、状态、定向、广告组、广告素材操作记录 |
| 数据源 | `h-s.dwd_market_appsflyer_activation_push_data_di`, `h-s.ods_market_google_ads_config_wide_hi` |
| 最后验证 | 2026-06-18 |

## 原始问题

> 当 DNU 下滑已经定位到 Google campaign 层时，如何把掉量 campaign 和 Google Ads change log 接起来，判断同期是否存在预算、状态、定向、广告组或广告素材操作记录？

## 口径说明

| 类型 | 内容 |
|---|---|
| DNU 口径 | `COUNT(DISTINCT distinct_id)`，来自 `dwd_market_appsflyer_activation_push_data_di`；只输出 campaign 聚合，不输出用户级明细。 |
| 业务日期 | 使用 `SUBSTR(CAST(install_time AS STRING), 1, 10)` 作为 install / DNU 业务日期。 |
| 分区护栏 | `dt` 扫描窗口必须覆盖业务日期窗口，并向后扫到 latest partition 或至少 anomaly day + 1，避免迟到分区低估。 |
| 媒体范围 | 默认 `media_source = 'googleadwords_int'`；其他媒体不能复用 Google Ads change log。 |
| change log 口径 | 使用 `ods_market_google_ads_config_wide_hi`，按 `campaign_id` 聚合 change_event；必须过滤 `dt` 和 `hour`。 |
| 联查键 | `activation.campaign_id = google_ads_config_wide_hi.campaign_id`；本资产只在 Google Ads 同源 campaign 排查中使用。 |
| 输出边界 | 有命中表示“同期存在配置操作记录”，不能自动判定为 DNU 下滑原因；无命中表示“当前 MC change log 窗口未见记录”，不能证明没人操作。 |

## SQL

### 1. Campaign DNU 下滑与 change log 命中汇总

```sql
WITH daily_campaign AS (
  SELECT
    SUBSTR(CAST(install_time AS STRING), 1, 10) AS biz_date,
    campaign_id,
    MAX(campaign_name) AS campaign_name,
    COUNT(DISTINCT distinct_id) AS dnu
  FROM h-s.dwd_market_appsflyer_activation_push_data_di
  WHERE dt BETWEEN '${dt_scan_start}' AND '${dt_scan_end}'
    AND SUBSTR(CAST(install_time AS STRING), 1, 10) BETWEEN '${baseline_start}' AND '${anomaly_day}'
    AND bundle_id = '${bundle_id}'
    AND country = '${country}'
    AND media_source = 'googleadwords_int'
    AND campaign_id IS NOT NULL
    AND campaign_id != ''
  GROUP BY
    SUBSTR(CAST(install_time AS STRING), 1, 10),
    campaign_id
),
campaign_delta AS (
  SELECT
    campaign_id,
    MAX(campaign_name) AS campaign_name,
    CAST(
      SUM(CASE WHEN biz_date BETWEEN '${baseline_start}' AND '${baseline_end}' THEN dnu ELSE 0 END)
      / ${baseline_days}.0
      AS DECIMAL(18,2)
    ) AS baseline_avg_dnu,
    SUM(CASE WHEN biz_date = '${anomaly_day}' THEN dnu ELSE 0 END) AS anomaly_dnu
  FROM daily_campaign
  GROUP BY campaign_id
),
campaign_delta_ranked AS (
  SELECT
    campaign_id,
    campaign_name,
    baseline_avg_dnu,
    anomaly_dnu,
    CAST(anomaly_dnu - baseline_avg_dnu AS DECIMAL(18,2)) AS dnu_delta,
    CASE
      WHEN baseline_avg_dnu > 0
      THEN CAST((anomaly_dnu - baseline_avg_dnu) / baseline_avg_dnu AS DECIMAL(18,4))
    END AS dnu_delta_rate
  FROM campaign_delta
  WHERE baseline_avg_dnu + anomaly_dnu > 0
),
change_log AS (
  SELECT
    campaign_id,
    COUNT(*) AS change_event_cnt,
    COUNT(DISTINCT event_hash) AS distinct_event_hash,
    MIN(change_event_change_date_time) AS min_change_time,
    MAX(change_event_change_date_time) AS max_change_time,
    SUM(CASE WHEN change_event_change_resource_type = 'CAMPAIGN_BUDGET' THEN 1 ELSE 0 END) AS campaign_budget_event_cnt,
    SUM(
      CASE
        WHEN change_event_change_resource_type = 'CAMPAIGN'
             AND INSTR(LOWER(COALESCE(change_event_changed_fields, '')), 'status') > 0
        THEN 1 ELSE 0
      END
    ) AS campaign_status_change_cnt,
    SUM(CASE WHEN change_event_change_resource_type = 'CAMPAIGN_CRITERION' THEN 1 ELSE 0 END) AS campaign_criterion_event_cnt,
    SUM(CASE WHEN change_event_change_resource_type = 'AD_GROUP' THEN 1 ELSE 0 END) AS ad_group_event_cnt,
    SUM(CASE WHEN change_event_change_resource_type IN ('AD_GROUP_AD', 'AD') THEN 1 ELSE 0 END) AS ad_event_cnt,
    SUM(
      CASE
        WHEN INSTR(LOWER(COALESCE(change_event_changed_fields, '')), 'headline') > 0
          OR INSTR(LOWER(COALESCE(change_event_changed_fields, '')), 'description') > 0
        THEN 1 ELSE 0
      END
    ) AS ad_text_change_cnt
  FROM h-s.ods_market_google_ads_config_wide_hi
  WHERE dt BETWEEN '${change_dt_start}' AND '${change_dt_end}'
    AND hour BETWEEN '${change_hour_start}' AND '${change_hour_end}'
    AND campaign_id IS NOT NULL
    AND campaign_id != ''
  GROUP BY campaign_id
)
SELECT
  d.campaign_id,
  d.campaign_name,
  d.baseline_avg_dnu,
  d.anomaly_dnu,
  d.dnu_delta,
  d.dnu_delta_rate,
  CASE
    WHEN c.campaign_id IS NULL THEN 'no_change_log_hit'
    ELSE 'change_log_hit'
  END AS change_log_hit_status,
  COALESCE(c.change_event_cnt, 0) AS change_event_cnt,
  COALESCE(c.distinct_event_hash, 0) AS distinct_event_hash,
  c.min_change_time,
  c.max_change_time,
  COALESCE(c.campaign_budget_event_cnt, 0) AS campaign_budget_event_cnt,
  COALESCE(c.campaign_status_change_cnt, 0) AS campaign_status_change_cnt,
  COALESCE(c.campaign_criterion_event_cnt, 0) AS campaign_criterion_event_cnt,
  COALESCE(c.ad_group_event_cnt, 0) AS ad_group_event_cnt,
  COALESCE(c.ad_event_cnt, 0) AS ad_event_cnt,
  COALESCE(c.ad_text_change_cnt, 0) AS ad_text_change_cnt
FROM campaign_delta_ranked d
LEFT JOIN change_log c
  ON d.campaign_id = c.campaign_id
WHERE d.dnu_delta < 0
ORDER BY d.dnu_delta ASC
LIMIT 100;
```

### 2. 命中 campaign 的字段级安全摘要

用于在汇总命中后查看操作方向。该 SQL 只输出库内解析后的字段摘要，不输出操作人邮箱和 raw resource JSON。

```sql
SELECT
  dt,
  hour,
  campaign_id,
  campaign_name,
  ad_group_id,
  ad_group_name,
  change_event_change_date_time,
  change_event_change_resource_type,
  change_event_resource_change_operation,
  change_event_changed_fields,
  change_event_change_summary,
  change_event_change_detail,
  COALESCE(
    get_json_object(change_event_old_resource, '$.campaign.targetRoas.targetRoas'),
    get_json_object(change_event_old_resource, '$.campaign.target_roas.target_roas')
  ) AS old_target_roas,
  COALESCE(
    get_json_object(change_event_new_resource, '$.campaign.targetRoas.targetRoas'),
    get_json_object(change_event_new_resource, '$.campaign.target_roas.target_roas')
  ) AS new_target_roas
FROM h-s.ods_market_google_ads_config_wide_hi
WHERE dt BETWEEN '${change_dt_start}' AND '${change_dt_end}'
  AND hour BETWEEN '${change_hour_start}' AND '${change_hour_end}'
  AND campaign_id IN (${campaign_id_list})
ORDER BY
  change_event_change_date_time,
  campaign_id,
  ad_group_id
LIMIT 200;
```

## 预期输出

按 Google campaign 输出：

- baseline 日均 DNU、异常日 DNU、DNU delta、delta rate。
- 同窗口 Google Ads change log 是否命中。
- 命中的 change_event 数、去重 event 数、变更时间范围。
- 预算、campaign status、定向、ad group、ad/ad text 变更计数。
- 命中 campaign 的字段级安全摘要可输出 `change_event_change_detail` 与解析后的 target ROAS 数值；仍不得输出 raw JSON。

## 风险与陷阱

- 这条 SQL 是“异动辅助排查”，不是因果判定器。有 change log 命中只能说同期存在配置操作证据。
- 无命中不能证明无人操作，只能说明当前 MaxCompute change log 窗口未发现该 campaign 记录。
- `dt_scan_end` 必须扫到 activation 表 latest partition 或至少 anomaly day + 1；否则可能低估异常日 DNU。
- `baseline_days` 必须等于 baseline 日期数；例如 7 天 baseline 填 `7`。
- 本 SQL 只覆盖 Google Ads。AppLovin、Meta、TikTok 等媒体需要各自平台 change log 或 owner 记录。
- 禁止输出 `change_event_user_email`、`change_event_old_resource`、`change_event_new_resource`；本 SQL 只输出聚合计数。

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-18 | Codex | verified | MaxCompute 小窗口执行成功。参数：`bundle_id='com.kcolb.juggle'`、`country='US'`、baseline `2026-06-10~2026-06-16`、anomaly day `2026-06-17`、activation `dt` 扫到 `2026-06-18`、change log 扫 `2026-06-17/hour 00~23`。汇总 SQL 返回 `通用词` DNU delta `-612.57` 且命中 1 条 budget 事件；`品类APP` delta `-418.71` 且命中 2 条 change event；`游戏大词` delta `-337.14` 且命中 1 条 campaign status 变更；`体育专项` delta `-225.86` 且当前窗口未命中。安全明细 SQL 确认：`通用词` 预算 `21000000000 -> 25500000000`，`品类APP` target ROAS `0.23 -> 0.25` 且 ad group status `ENABLED -> PAUSED`，`游戏大词` campaign status `ENABLED -> PAUSED`。未输出 PII 或 raw JSON。 |
