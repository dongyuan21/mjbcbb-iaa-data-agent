# MC vs CK Spend 对账

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_mc_ck_spend_reconciliation` |
| 状态 | verified |
| 适用场景 | 对齐 MaxCompute ADS spend 表与 ClickHouse spend 表的核心指标 |
| MC 表 | `h-s.ads_market_tj_ad_spend_active_v2` |
| CK 表 | `shucang_market.tj_ad_spend_active_v2` |
| 最后验证 | 2026-06-13 |

## 口径说明

- 对账对象：MaxCompute `h-s.ads_market_tj_ad_spend_active_v2` 与 ClickHouse `shucang_market.tj_ad_spend_active_v2`。
- 时间口径：`active_date = ${bizdate}`；MaxCompute 侧还必须带 `dt = ${bizdate}` 分区过滤。
- 粒度：`active_date × media_source × bundle_id`。
- 指标：折后消耗 `cost_zhe`、AF 安装 `registers`、媒体安装 `media_installs`。

## SQL

### MC SQL

```sql
SELECT
  active_date,
  media_source,
  bundle_id,
  SUM(cost_zhe) AS cost_zhe,
  SUM(registers) AS af_installs,
  SUM(media_installs) AS media_installs
FROM ads_market_tj_ad_spend_active_v2
WHERE dt = '${bizdate}'
  AND active_date = '${bizdate}'
GROUP BY active_date, media_source, bundle_id
ORDER BY cost_zhe DESC
LIMIT 100;
```

### CK SQL

```sql
SELECT
  active_date,
  media_source,
  bundle_id,
  sum(cost_zhe) AS cost_zhe,
  sum(registers) AS af_installs,
  sum(media_installs) AS media_installs
FROM tj_ad_spend_active_v2
WHERE active_date = '${bizdate}'
GROUP BY active_date, media_source, bundle_id
ORDER BY cost_zhe DESC
LIMIT 100
SETTINGS max_execution_time = 20,
         max_result_rows = 100,
         max_rows_to_read = 500000000,
         timeout_before_checking_execution_speed = 0;
```

## 验证记录

2026-06-13 使用 `bizdate=2026-06-12` 分别执行 MC 和 CK 查询。Top 20 结果数值一致，示例：

```text
googleadwords_int / com.kcolb.juggle
MC cost_zhe=751971.4600000001, af_installs=230880, media_installs=674988
CK cost_zhe=751971.4599999717, af_installs=230880, media_installs=674988
```

## 结论

在 `2026-06-12` 的 `active_date × media_source × bundle_id` 聚合粒度上，MC ADS 表与 CK spend 表核心指标一致。后续可以用该 SQL 做日常同步/口径 sanity check。

## 风险与陷阱

- 这里只验证 spend 主表，不代表 revenue / retention 也完全一致。
- CK 查询要加复杂度限制，避免无界扫描。
- MC 与 CK 可能存在同步延迟，建议对账时避开当天实时未完成分区。
