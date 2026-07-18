# 设备 SDK 收入新回流聚合

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_device_sdk_revenue_new_return` |
| 状态 | verified |
| 适用场景 | 查看设备粒度 SDK 收入在新设备 / 回流设备和 AF 媒体上的分布 |
| 依赖表 | `dwd_market_new_return_device_sdk_revenue_di` |
| 最后验证 | 2026-06-13 |

## 口径说明

- `dt`：收入日期分区。
- `af_media_source`：AF 媒体来源。
- `is_new_device`：是否自归因新设备。
- `is_return_device`：是否回访设备。
- `revenue`：广告收入。

## SQL

```sql
SELECT
  dt,
  bundle_id,
  af_media_source,
  is_new_device,
  is_return_device,
  COUNT(1) AS rows,
  SUM(revenue) AS revenue
FROM dwd_market_new_return_device_sdk_revenue_di
WHERE dt = '${dt}'
GROUP BY dt, bundle_id, af_media_source, is_new_device, is_return_device
ORDER BY revenue DESC
LIMIT 100;
```

## 验证记录

2026-06-13 使用 `dt=2026-06-12` 执行成功。示例：

```text
com.kcolbpuzzle.us.ios / organic / is_new_device=null / is_return_device=null
rows=4577400, revenue=260680.6473

com.kcolbpuzzle.us.ios / organic / is_new_device=0 / is_return_device=1
rows=3685971, revenue=219363.3364
```

## 风险与陷阱

- `is_new_device`、`is_return_device` 可能为空，需要解释为未分类或上游缺失，不可直接当 0。
- 该表是设备粒度收入解释层，不等同于 MI ROI 页面最终拼装结果。
- 不输出 `device_id` 明细。
