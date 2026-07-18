# SDK 回收 vs AF 回收对比

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_sdk_vs_af_revenue_by_cohort` |
| 状态 | verified |
| 适用场景 | 比较 `revenue_source=sdk` 与 `revenue_source=af` 回收差异 |
| 依赖表 | `ads_market_tj_ad_sdk_revenue_attributed_di`, `ads_market_tj_ad_revenue_v2` |
| 最后验证 | 2026-06-13 |

## 口径说明

- SDK 回收：`ads_market_tj_ad_sdk_revenue_attributed_di`
- AF 回收：`ads_market_tj_ad_revenue_v2`
- 日期：`dt` 分区 + `active_date` cohort。
- `date_diff`：激活日期到变现日期的天数差。
- 新鲜度：业务确认 CK 侧 `shucang_market.tj_ad_sdk_revenue` 与 `shucang_market.tj_ad_revenue_v2` 均允许 T-2 分区；latest `active_date` 落后当前日期 2 天以内不应把 SDK / AF 回收下降直接判断为业务劣化。当前工程规则见 `knowledge/agent_knowledge/policies/ROI360_SDK回收表新鲜度SLA.md` 与 `knowledge/agent_knowledge/policies/ROI360_AF回收表新鲜度SLA.md`。

## SQL

```sql
SELECT
  'sdk' AS source_type,
  active_date,
  media_source,
  bundle_id,
  date_diff,
  COUNT(1) AS rows,
  SUM(revenue) AS revenue,
  SUM(revenue_counts) AS revenue_devices
FROM ads_market_tj_ad_sdk_revenue_attributed_di
WHERE dt = '${bizdate}'
  AND active_date = '${bizdate}'
  AND date_diff IN (0, 1, 6)
GROUP BY active_date, media_source, bundle_id, date_diff

UNION ALL

SELECT
  'af' AS source_type,
  active_date,
  media_source,
  bundle_id,
  date_diff,
  COUNT(1) AS rows,
  SUM(revenue) AS revenue,
  SUM(revenue_counts) AS revenue_devices
FROM ads_market_tj_ad_revenue_v2
WHERE dt = '${bizdate}'
  AND active_date = '${bizdate}'
  AND date_diff IN (0, 1, 6)
GROUP BY active_date, media_source, bundle_id, date_diff
LIMIT 200;
```

## 验证记录

2026-06-13 用 `bizdate=2026-06-12` 执行成功。抽样结果：

```text
SDK: Apple Search Ads / com.kcolbpuzzle.us.ios / date_diff=0
revenue=9904.1386, revenue_devices=64165

AF: googleadwords_int / com.kcolb.juggle / date_diff=0
revenue=9106.0359, revenue_devices=141384
```

## 风险与陷阱

- 不同 source 的 active_date 时区和 attribution 口径可能不同。
- MI 默认 `revenue_source=sdk`，不能默认 AF 回收等于 SDK 回收。
- SDK / AF 回收表均允许 T-2 分区；超过 T-2 或 freshness 状态非 fresh 时，先标 `data_delay_suspected` / `freshness_blocked`。
