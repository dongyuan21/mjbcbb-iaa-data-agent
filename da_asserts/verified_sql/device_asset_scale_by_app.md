# 设备资产规模按产品聚合

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_device_asset_scale_by_app` |
| 状态 | verified |
| 适用场景 | 查看产品设备资产规模、新设备、AF新设备、回流设备 |
| 依赖表 | `dim_kcolb_tsalb_all_device_da` |
| 最后验证 | 2026-06-13 |

## 口径说明

- `dt`：分区日期。
- `app_name`：产品应用名。
- `is_new_device`：自归因新设备。
- `is_af_new_device`：AF 新设备，当前验证中该字段为空，需要进一步确认。
- `is_return_device`：回流设备。

## SQL

```sql
SELECT
  dt,
  app_name,
  COUNT(1) AS devices,
  SUM(is_new_device) AS new_devices,
  SUM(is_af_new_device) AS af_new_devices,
  SUM(is_return_device) AS return_devices
FROM dim_kcolb_tsalb_all_device_da
WHERE dt = '${dt}'
GROUP BY dt, app_name
ORDER BY devices DESC
LIMIT 20;
```

## 验证记录

2026-06-13 使用 `dt=2026-06-12` 执行成功：

```text
kcolb_tsalb_gp: devices=1448474485, new_devices=1606336, af_new_devices=null, return_devices=1945793
kcolb_tsalb_ios: devices=294542292, new_devices=211416, af_new_devices=null, return_devices=550434
```

## 风险与陷阱

- 不输出设备级 `device_id` 明细。
- `is_af_new_device` 为空，说明该字段当前不可直接用于 AF 新设备统计，需进一步确认。
