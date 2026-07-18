# 新/回流设备 AF 归因聚合验证 SQL

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260620_new_return_device_attribution_aggregation` |
| 状态 | verified |
| 来源 | raw SQL / 人工整理 / 用户 2026-06-20 确认 |
| 原始文件 | `../../raw_exports/knowledge/used_sql.sql` |
| 适用场景 | 新设备/回流设备 AF 归因快照的最新分区、聚合分布和 `device_id` 非严格唯一验证 |
| 负责人 | Codex |
| 最后验证 | 2026-06-20 |

## 原始问题

> 验证 `h-s.dim_market_new_return_device_attribution_da` 是否可作为新设备与回流设备的轻量 AF 归因快照，并确认分区、聚合粒度和 `device_id` 非严格唯一的使用边界。

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | DA 快照表，默认先取 `MAX(dt)` 最新分区，再将聚合验证限制在该分区 |
| 粒度 | `device_id × attribution row × dt`；用户 2026-06-20 确认 `device_id × dt` 非严格唯一属于正常多行形态 |
| 维度 | `bundle_id`, `is_new_device`, `is_return_device` |
| 指标 | `COUNT(*)`, `COUNT(DISTINCT device_id)` |
| 过滤 | 必须过滤 `dt`；常规复跑只查最新分区 |
| 依赖表 | `h-s.dim_market_new_return_device_attribution_da` |
| 与表卡关系 | `../../ai_hive/agent_knowledge/tables/dim_market_new_return_device_attribution_da.yaml` |

本 SQL 只晋升聚合验证部分。设备级样例、`device_id` 明细、`distinct_id` 展开样例不属于 verified 资产，不默认召回。

## SQL

### 1. 取最新分区

```sql
SELECT MAX(dt) AS latest_dt
FROM h-s.dim_market_new_return_device_attribution_da;
```

### 2. 新/回流设备行数分布

```sql
SELECT
    bundle_id,
    is_new_device,
    is_return_device,
    COUNT(*) AS device_cnt
FROM h-s.dim_market_new_return_device_attribution_da
WHERE dt = '${latest_dt}'
GROUP BY bundle_id, is_new_device, is_return_device
ORDER BY bundle_id, is_new_device DESC, is_return_device DESC
LIMIT 100;
```

### 3. 验证同分区 `device_id` 非严格唯一

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT device_id) AS distinct_devices
FROM h-s.dim_market_new_return_device_attribution_da
WHERE dt = '${latest_dt}';
```

## 预期输出

- 最新分区日期。
- 按 `bundle_id × is_new_device × is_return_device` 聚合的行数分布。
- 最新分区 `total_rows` 与 `distinct_devices`，用于判断是否可按 `device_id × dt` 当严格主键。

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-15 | Cursor Agent | partial_validated | `MIN(dt)=2026-03-11`, `MAX(dt)=2026-06-14`；渠道映射表另验证为 415 行 |
| 2026-06-15 | Cursor Agent | key_uniqueness_failed | `dt=2026-06-14` 聚合结果：`total_rows=1,952,166,038`, `distinct_devices=1,948,846,693`；不按 `device_id × dt` 严格主键使用 |
| 2026-06-15 | Cursor Agent | duplicate_scale_checked | 重复 device 约 `3,207,360` 个，额外重复行约 `3,319,345`，单 device 最多 `11` 行；按新/回流标记的精确去重拆分查询过重，已停止 |
| 2026-06-20 | Codex | verified | MC `SELECT 1` 成功；最新分区 `latest_dt=2026-06-20`；聚合分布查询跑通且只输出聚合数；唯一性检查结果 `total_rows=1,969,146,324`, `distinct_devices=1,965,752,398`，额外重复行 `3,393,926`。用户确认这是正常多行形态，可按 `device_id × attribution row × dt` 理解。 |

## 风险与陷阱

- 本 verified SQL 只覆盖聚合验证，不覆盖设备级样例查询。
- 表含 `device_id`、`distinct_id` 等 PII / 用户级标识；不得输出、保存或贴入明细值。
- `device_id × dt` 非严格唯一是已确认的正常多行形态；查询时按业务问题先聚合或去重，不按单设备单行假设。
- `distinct_id` 是 ARRAY；如需展开做 join，只能在临时查询中使用 `LATERAL VIEW EXPLODE`，且不得落明细结果。
- 不要与 `dim_kcolb_tsalb_all_new_or_return_device_da` 混用；后者仅为 kcolb tsalb 双端新/回流设备标签子集，无 AF 归因字段。
