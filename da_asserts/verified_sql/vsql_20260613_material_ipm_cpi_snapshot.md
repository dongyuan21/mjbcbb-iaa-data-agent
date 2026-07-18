# Verified SQL: 素材 IPM / CPI / CTR / CVR 快照

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260613_material_ipm_cpi_snapshot` |
| 状态 | verified |
| 来源 | 原 `TODO/周报问题积压清单.md`（已归档，现由 `eval/真实问题验收集/` 接替） |
| 适用场景 | 素材冷启动、素材前端转化效率、IPM/CPI/CTR/CVR 复盘 |
| 最后验证 | 2026-06-13 |

## 原始问题

> 素材冷启动和爆款衰减能否从 IPM、CPI、CTR、CVR 等前端指标做初筛？

## 口径说明

| 类型 | 内容 |
|---|---|
| 数据源 | `h-s.ads_market_material_metric_di` |
| 时间口径 | `dt` 分区 + `active_date` 投放日期 |
| 粒度 | `active_date × bundle_id × media_source × material_type × material` |
| 指标 | `shows`、`clicks`、`registers`、`cost_zhe_usd`、CTR、CVR、IPM、CPI |
| 限制 | 当前表无回收字段，不计算 ROI / ROAS |

## SQL

```sql
SELECT
  active_date,
  bundle_id,
  media_source,
  material_type,
  material,
  SUM(shows) AS shows,
  SUM(clicks) AS clicks,
  SUM(registers) AS registers,
  SUM(cost_zhe_usd) AS cost_usd,
  CASE WHEN SUM(shows) > 0 THEN SUM(clicks) / SUM(shows) END AS ctr,
  CASE WHEN SUM(clicks) > 0 THEN SUM(registers) / SUM(clicks) END AS cvr,
  CASE WHEN SUM(shows) > 0 THEN SUM(registers) / SUM(shows) * 1000 END AS ipm,
  CASE WHEN SUM(registers) > 0 THEN SUM(cost_zhe_usd) / SUM(registers) END AS cpi
FROM h-s.ads_market_material_metric_di
WHERE dt BETWEEN '2026-05-24' AND '2026-05-30'
  AND active_date BETWEEN '2026-05-24' AND '2026-05-30'
  AND bundle_id = 'com.kcolb.juggle'
GROUP BY
  active_date,
  bundle_id,
  media_source,
  material_type,
  material
HAVING SUM(shows) >= 1000
ORDER BY active_date DESC, cost_usd DESC
LIMIT 50;
```

## 预期输出

按素材粒度输出曝光、点击、注册、花费，以及 CTR、CVR、IPM、CPI。适合先找高消耗低 IPM / 高 CPI 素材，或筛选冷启动表现较好的素材。

## 风险与陷阱

- 当前 SQL 只覆盖前端投放效率，不包含收入、ROI、ROAS。
- Google / Aura 等部分媒体可能 material 为空或聚合为“其他”，解释素材维度时需注意。
- `cost_zhe_usd` 为折后美元花费，是否用于官方复盘需业务确认。

## 回收扩展（candidate，非默认召回）

- SDK 回收 join 草案见 `../candidate_sql/material_ipm_with_sdk_revenue_join.md`。
- 在 join 验证通过前，Agent 不得把本 SQL 解释成完整 ROI 复盘。

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-13 | AI | verified | MaxCompute 小窗口执行成功，输出素材聚合指标。 |

