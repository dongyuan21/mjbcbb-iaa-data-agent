# AF 归因覆盖按设备聚合

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_af_attribution_coverage_by_device` |
| 状态 | verified |
| 适用场景 | 查看设备级 AF 归因覆盖、media/campaign 覆盖情况 |
| 依赖表 | `dim_market_appsflyer_attribution_by_device_id_da` |
| 最后验证 | 2026-06-13 |

## 口径说明

- `device_id`：设备主键，不输出明细。
- `appsflyer_id`：数组字段，用 `size(appsflyer_id) > 0` 判断是否有 AF ID。
- `campaign_id`：非空表示有 campaign 归因。
- `media_source`：归因媒体。

## SQL

```sql
SELECT
  dt,
  bundle_id,
  media_source,
  COUNT(1) AS rows,
  SUM(CASE WHEN campaign_id IS NOT NULL AND campaign_id <> '' THEN 1 ELSE 0 END) AS campaign_rows,
  SUM(CASE WHEN size(appsflyer_id) > 0 THEN 1 ELSE 0 END) AS afid_rows
FROM dim_market_appsflyer_attribution_by_device_id_da
WHERE dt = '${dt}'
  AND bundle_id IN ('com.kcolb.juggle', 'com.kcolbpuzzle.us.ios')
GROUP BY dt, bundle_id, media_source
ORDER BY rows DESC
LIMIT 100;
```

## 验证记录

2026-06-13 使用 `dt=2026-06-12` 执行成功。示例：

```text
com.kcolb.juggle / organic: rows=271708358, campaign_rows=99972918, afid_rows=271708324
com.kcolb.juggle / googleadwords_int: rows=203682977, campaign_rows=203682977, afid_rows=203682977
com.kcolbpuzzle.us.ios / Apple Search Ads: rows=32723760, campaign_rows=32723760, afid_rows=32723760
```

## 风险与陷阱

- `organic` 也可能有 campaign_rows，需结合归因规则解释。
- `unattributed` campaign_rows 为 0 是预期现象之一。
- 不输出 `device_id`、`distinct_id`、`appsflyer_id` 数组明细。
