# BB 国家 DAU / DNU WoW 拆解

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260617_bb_country_dau_dnu_wow` |
| 状态 | verified |
| 适用场景 | kcolb tsalb GP Android 按国家拆 DAU / DNU 周均 WoW |
| 数据源 | `h-s.ads_market_device_dau_behavior_di` |
| 最后验证 | 2026-06-17 |

## 口径说明

- 产品范围：`bundle_id = 'com.kcolb.juggle'`。
- 时间口径：`dt` 是活跃日期；验证窗口为 baseline `2026-06-03` ~ `2026-06-09`，current `2026-06-10` ~ `2026-06-16`。
- 粒度：`country`。
- DAU：`SUM(dau)`。
- DNU：`SUM(CASE WHEN age_bucket = 'D0' THEN dau ELSE 0 END)`。
- 周均：窗口内 7 日合计除以 `7.0`。
- 边界：这是设备口径国家拆解；国家编码沿用表内 `country`，其中 `unknown` 不得静默丢弃。

## SQL

```sql
WITH daily AS (
  SELECT
    CASE
      WHEN dt BETWEEN '${baseline_start}' AND '${baseline_end}' THEN 'baseline'
      WHEN dt BETWEEN '${current_start}' AND '${current_end}' THEN 'current'
    END AS period,
    country,
    SUM(dau) AS dau,
    SUM(CASE WHEN age_bucket = 'D0' THEN dau ELSE 0 END) AS dnu
  FROM h-s.ads_market_device_dau_behavior_di
  WHERE dt BETWEEN '${baseline_start}' AND '${current_end}'
    AND bundle_id = 'com.kcolb.juggle'
  GROUP BY
    CASE
      WHEN dt BETWEEN '${baseline_start}' AND '${baseline_end}' THEN 'baseline'
      WHEN dt BETWEEN '${current_start}' AND '${current_end}' THEN 'current'
    END,
    country
),
pivoted AS (
  SELECT
    country,
    SUM(CASE WHEN period = 'baseline' THEN dau ELSE 0 END) / 7.0 AS baseline_avg_dau,
    SUM(CASE WHEN period = 'current' THEN dau ELSE 0 END) / 7.0 AS current_avg_dau,
    SUM(CASE WHEN period = 'baseline' THEN dnu ELSE 0 END) / 7.0 AS baseline_avg_dnu,
    SUM(CASE WHEN period = 'current' THEN dnu ELSE 0 END) / 7.0 AS current_avg_dnu
  FROM daily
  WHERE period IS NOT NULL
  GROUP BY country
)
SELECT
  country,
  baseline_avg_dau,
  current_avg_dau,
  current_avg_dau - baseline_avg_dau AS dau_delta,
  CASE WHEN baseline_avg_dau <> 0 THEN (current_avg_dau - baseline_avg_dau) / baseline_avg_dau END AS dau_wow_rate,
  baseline_avg_dnu,
  current_avg_dnu,
  current_avg_dnu - baseline_avg_dnu AS dnu_delta,
  CASE WHEN baseline_avg_dnu <> 0 THEN (current_avg_dnu - baseline_avg_dnu) / baseline_avg_dnu END AS dnu_wow_rate
FROM pivoted
WHERE baseline_avg_dau + current_avg_dau + baseline_avg_dnu + current_avg_dnu > 0
ORDER BY ABS(current_avg_dau - baseline_avg_dau) DESC
LIMIT 50;
```

## 验证记录

2026-06-17 使用 MaxCompute helper 真实执行通过。执行前探测：

- `h-s.ads_market_device_dau_behavior_di` 最新分区：`2026-06-16`。
- MC 连接烟测：`SELECT 1` 成功。

验证窗口参数：

```text
baseline_start=2026-06-03
baseline_end=2026-06-09
current_start=2026-06-10
current_end=2026-06-16
```

Top 输出摘要：

| country | baseline_avg_dau | current_avg_dau | dau_delta | dau_wow_rate | baseline_avg_dnu | current_avg_dnu | dnu_delta | dnu_wow_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ID | 7,899,270 | 7,137,633 | -761,637 | -9.64% | 133,643 | 134,445 | 802 | 0.60% |
| PH | 2,938,079 | 2,413,200 | -524,879 | -17.86% | 51,798 | 44,859 | -6,939 | -13.40% |
| IN | 8,130,864 | 7,853,932 | -276,932 | -3.41% | 291,881 | 421,354 | 129,473 | 44.36% |
| unknown | 2,791,187 | 2,536,347 | -254,840 | -9.13% | 317,409 | 365,532 | 48,123 | 15.16% |
| US | 1,820,559 | 1,767,131 | -53,428 | -2.93% | 63,877 | 62,219 | -1,658 | -2.60% |

## 风险与陷阱

- 该 SQL 按 `country` 原值输出；`unknown` 可能是真实数据质量/映射缺口，不应默认过滤。
- 国家口径若用于周报印度/美国叙事，需确认报告使用的是单包、双端还是全 BB 家族。
- DNU 是设备日龄 D0，不等于 AF install。
- 国家 DAU 下降不必然代表 DNU 同向下降；当前窗口中 IN 的 DAU 下降但 DNU 明显上升。
