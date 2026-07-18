# AF Cohort 留存按媒体聚合

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_af_cohort_retention_by_media` |
| 状态 | verified |
| 适用场景 | 查看 AF cohort 的 date_diff 留存用户量和事件量 |
| 依赖表 | `ads_market_af_cohort_user_acquisition_v2` |
| 最后验证 | 2026-06-13 |

## 口径说明

- `dt`：日期分区。
- `active_date`：cohort 激活日期。
- `event_date`：事件日期。
- `date_diff`：归因后天数。
- `unique_users`：唯一用户数。
- `event_count`：事件计数。

## SQL

```sql
SELECT
  active_date,
  media_source,
  bundle_id,
  date_diff,
  SUM(unique_users) AS users,
  SUM(event_count) AS events
FROM ads_market_af_cohort_user_acquisition_v2
WHERE dt = '${dt}'
  AND active_date = '${active_date}'
  AND date_diff IN (0, 1, 6, 29)
GROUP BY active_date, media_source, bundle_id, date_diff
ORDER BY users DESC
LIMIT 100;
```

## 验证记录

2026-06-13 查到最新有数据分区为 `dt=2026-06-11`。使用 `active_date=2026-06-11` 执行成功。Top 行：

```text
organic / com.kcolb.juggle / date_diff=0
users=613760, events=2448984
```

## 风险与陷阱

- 留存率不能只看 `date_diff=N`，还需要同 cohort 的 `date_diff=0` 作分母。
- 不同 active_date 的成熟度不同，D29/D30 等长窗口需要等待数据成熟。
