# ROI 预测准确性快照

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_roi_prediction_accuracy_snapshot` |
| 状态 | verified |
| 适用场景 | 评估 ROI 预测模型在不同 time_range 下的预测与真实 ROI 差异 |
| 依赖表 | `ads_market_roi_pred_accuracy_da` |
| 最后验证 | 2026-06-13 |

## 口径说明

- `dt`：数据写入日期 / end_date。
- `active_date`：花费日期。
- `snapshot_date`：预估快照日期。
- `model_version`：模型版本，如 `xy_v6` / `v6`。
- `time_range`：快照距 active_date 的天数，常见 3/7/15/30/60/90/180。
- `pred_dN`：预测 ROI。
- `real_dN`：真实 ROI。
- 新鲜度：2026-06-18 业务确认该表允许 T-2 分区；latest `dt` 落后当前业务日 2 天以内可视为正常，不作为回归 freshness 阻断。

## SQL

```sql
SELECT
  dt,
  model_version,
  bundle_id,
  media_source,
  time_range,
  COUNT(1) AS rows,
  AVG(pred_d7) AS avg_pred_d7,
  AVG(real_d7) AS avg_real_d7,
  AVG(pred_d30) AS avg_pred_d30,
  AVG(real_d30) AS avg_real_d30,
  SUM(cost) AS cost
FROM ads_market_roi_pred_accuracy_da
WHERE dt = '${dt}'
GROUP BY dt, model_version, bundle_id, media_source, time_range
ORDER BY rows DESC
LIMIT 100;
```

## 验证记录

2026-06-13 先查分区，最新有数据分区为 `2026-06-11`。用该分区执行成功。Top 行：

```text
dt=2026-06-11, model_version=xy_v6, bundle_id=com.kcolb.juggle, media_source=all, time_range=3
rows=36553, avg_pred_d7=0.3030, avg_real_d7=0.2943, avg_pred_d30=0.6181, avg_real_d30=0.5809
```

## 风险与陷阱

- `pred_dN` 在 `time_range < N` 时才有意义。
- `real_dN` 需要 `cur_range >= N` 才有值。
- 该表是模型评估快照，不是 ROI 页面主查询事实表。
