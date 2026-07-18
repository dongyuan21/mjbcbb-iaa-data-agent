# Verified SQL: MI ROI360 看板逐行复现 (campaign × country × active_date)

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260616_mi_roi360_campaign_board_recon` |
| 状态 | verified |
| 来源 | `../../raw_exports/最新cam看板.html`（MI ROI360 导出 `chenzhuoran-roi360-2026-06-12.xlsx`）；验证报告 `../../raw_exports/cam看板验证/report.md` |
| 口径真理源 | nexus `backend/boards/internal/service/report/handler/roi/ua/{spend,revenue,retention,field}.go` |
| 适用场景 | 用 ClickHouse 复现 MI ROI360「Campaign 下钻看板」的消耗/注册/展示/点击 + 实际段 ROI + 留存；看板数据反查与校验 |
| 最后验证 | 2026-06-16 |

## 原始问题

> 仅凭 MI ROI360 看板导出，能否反推其依赖的 CK 表与 SQL，并跑数验证逐行一致？

## 口径说明

| 类型 | 内容 |
|---|---|
| 数据源 | 消耗 `shucang_market.tj_ad_spend_active_v2_view`；SDK 回收 `shucang_market.tj_ad_sdk_revenue_view`；留存 `shucang_market.af_cohort_user_acquisition_v2_view` |
| 默认口径 | `forecast_version=v6`、`revenue_source=sdk`（MI ROI360 默认） |
| 时间口径 | 消耗/回收按 `active_date`；留存额外 `dt >= 窗口起始` 且 `date_diff IN (0,N)` |
| 粒度 | `active_date × campaign_name × country`（跨 media_source 聚合） |
| 字段映射 | 看板 `ROI1/ROI3/ROI7` = MI `roi_0/roi_2/roi_6`；看板 `次留/3留/7留` = MI `retention_1/2/6`（date_diff 1/2/6） |
| ROI 口径 | `roi_N = 累计 sdk 回收(date_diff ≤ N) / 折后消耗`；回收 nexus 用 `arrayCumSum(groupArray(...))`，等价 `sumIf(revenue, date_diff<=N)` |
| 折后消耗 | `SUM(cost_zhe / NULLIF(currency,0))`（USD） |
| 限制 | ROI360（roi_359）及导出时未成熟的 ROI 段为 MI 应用层预测，CK 无 campaign 粒度预测值，本 SQL 不复现预测段 |

## SQL

```sql
-- MI ROI360 看板逐行复现; 过滤可用 bundle_id 或 campaign_name IN (...)
WITH
spend AS (
  SELECT active_date, campaign_name, country,
    SUM(cost_zhe/NULLIF(currency,0)) AS cost_zhe_usd,
    SUM(registers) AS registers, SUM(shows) AS shows, SUM(clicks) AS clicks
  FROM shucang_market.tj_ad_spend_active_v2_view
  WHERE active_date BETWEEN '2026-06-07' AND '2026-06-11'
    AND bundle_id = 'com.nebula.mahjongtile'
  GROUP BY active_date, campaign_name, country
),
rev AS (
  SELECT active_date, campaign_name, country,
    sumIf(revenue, date_diff <= 0) AS rev_d0,   -- ROI1 分子
    sumIf(revenue, date_diff <= 2) AS rev_d2,   -- ROI3 分子
    sumIf(revenue, date_diff <= 6) AS rev_d6    -- ROI7 分子
  FROM shucang_market.tj_ad_sdk_revenue_view
  WHERE active_date BETWEEN '2026-06-07' AND '2026-06-11'
    AND bundle_id = 'com.nebula.mahjongtile'
  GROUP BY active_date, campaign_name, country
),
ret AS (
  SELECT active_date, campaign_name, country,
    sumIf(unique_users, date_diff = 0) AS u0,
    sumIf(unique_users, date_diff = 1) AS u1,   -- 次留
    sumIf(unique_users, date_diff = 2) AS u2,   -- 3留
    sumIf(unique_users, date_diff = 6) AS u6    -- 7留
  FROM shucang_market.af_cohort_user_acquisition_v2_view
  WHERE dt >= '2026-06-07' AND active_date BETWEEN '2026-06-07' AND '2026-06-11'
    AND bundle_id = 'com.nebula.mahjongtile' AND date_diff IN (0,1,2,6)
  GROUP BY active_date, campaign_name, country
)
SELECT s.active_date, s.campaign_name, s.country,
  round(s.cost_zhe_usd,2) AS cost_zhe_usd, s.registers, s.shows, s.clicks,
  if(s.registers>0, round(s.cost_zhe_usd/s.registers,3), 0) AS af_cpi,
  if(s.cost_zhe_usd>0, round(r.rev_d0/s.cost_zhe_usd,4), NULL) AS roi1,
  if(s.cost_zhe_usd>0, round(r.rev_d2/s.cost_zhe_usd,4), NULL) AS roi3,
  if(s.cost_zhe_usd>0, round(r.rev_d6/s.cost_zhe_usd,4), NULL) AS roi7,
  if(t.u0>0, round(t.u1/t.u0,4), NULL) AS retention_1,
  if(t.u0>0, round(t.u2/t.u0,4), NULL) AS retention_2,
  if(t.u0>0, round(t.u6/t.u0,4), NULL) AS retention_6
FROM spend AS s
LEFT JOIN rev AS r ON s.active_date=r.active_date AND s.campaign_name=r.campaign_name AND s.country=r.country
LEFT JOIN ret AS t ON s.active_date=t.active_date AND s.campaign_name=t.campaign_name AND s.country=t.country
ORDER BY cost_zhe_usd DESC;
```

## 预期输出

按 `active_date × campaign × country` 输出折后消耗、注册、展示、点击、af_cpi、实际段 ROI1/3/7、留存 1/2/6 留。可直接与 MI ROI360 看板逐行对齐。

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-16 | AI | verified | 对看板 14781 行（5天×126camp×234country）逐行比对：行对齐 100%；注册/次留/3留 100% bit 级一致；折后消耗/展示/点击 99.93%/99.99%/100%（实务容差）；ROI1/ROI3 实际段 98.44%/97.64%。残差经三重证据证明为「看板 06-12 快照 vs CK 当前回填」时间差，非口径错误。 |

## 风险与陷阱

- **country 格式**：CK 为纯代码 `US`，MI/看板展示为 `US-美国`，比对需取 `split("-")[0]`。
- **跨 media 聚合**：看板无 media 维度，须 `SUM` over `media_source`，否则行数与值都对不上。
- **campaign_name 唯一性**：本窗口内 campaign 不跨 bundle；若跨 bundle 复制的同名 campaign 存在，需加 `bundle_id` 限定避免重复累计。
- **快照时间差**：消耗/回收表只存当前值（无历史 `dt` 快照），与历史导出做 bit 级对齐不可达，回收回填使 CK 值偏高（只增不减）。
- **预测段不可复现**：ROI360 及导出时 `date_diff` 未成熟的 ROI/留存为 MI 应用层预测，CK 无 campaign 粒度预测值，勿用本 SQL 充当预测。
- **回收源切换**：AF 口径应改用 `tj_ad_revenue_v2_view`，与 SDK 口径不可混用。
