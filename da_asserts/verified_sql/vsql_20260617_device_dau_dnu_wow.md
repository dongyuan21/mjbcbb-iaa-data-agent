# 大盘 DAU / DNU WoW 周均拆解

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260617_device_dau_dnu_wow` |
| 状态 | verified |
| 适用场景 | 各产品 / 包体 / OS 的大盘 DAU、DNU 周均 WoW 通晒 |
| 数据源 | `h-s.ads_market_device_dau_behavior_di` |
| 最后验证 | 2026-06-17 |

## 口径说明

- 时间口径：`dt` 是活跃日期；验证窗口为 baseline `2026-06-03` ~ `2026-06-09`，current `2026-06-10` ~ `2026-06-16`。
- 粒度：`project × bundle_id × os_system`。
- DAU：`SUM(dau)`。
- DNU：`SUM(CASE WHEN age_bucket = 'D0' THEN dau ELSE 0 END)`。
- 周均：窗口内 7 日合计除以 `7.0`。
- 边界：这是设备口径大盘表，不等于 AF install / activation 分母；不要把 `age_bucket` 作为输出维度再汇总 DNU。

## SQL

```sql
WITH daily AS (
  SELECT
    CASE
      WHEN dt BETWEEN '${baseline_start}' AND '${baseline_end}' THEN 'baseline'
      WHEN dt BETWEEN '${current_start}' AND '${current_end}' THEN 'current'
    END AS period,
    project,
    bundle_id,
    os_system,
    SUM(dau) AS dau,
    SUM(CASE WHEN age_bucket = 'D0' THEN dau ELSE 0 END) AS dnu
  FROM h-s.ads_market_device_dau_behavior_di
  WHERE dt BETWEEN '${baseline_start}' AND '${current_end}'
  GROUP BY
    CASE
      WHEN dt BETWEEN '${baseline_start}' AND '${baseline_end}' THEN 'baseline'
      WHEN dt BETWEEN '${current_start}' AND '${current_end}' THEN 'current'
    END,
    project,
    bundle_id,
    os_system
),
pivoted AS (
  SELECT
    project,
    bundle_id,
    os_system,
    SUM(CASE WHEN period = 'baseline' THEN dau ELSE 0 END) / 7.0 AS baseline_avg_dau,
    SUM(CASE WHEN period = 'current' THEN dau ELSE 0 END) / 7.0 AS current_avg_dau,
    SUM(CASE WHEN period = 'baseline' THEN dnu ELSE 0 END) / 7.0 AS baseline_avg_dnu,
    SUM(CASE WHEN period = 'current' THEN dnu ELSE 0 END) / 7.0 AS current_avg_dnu
  FROM daily
  WHERE period IS NOT NULL
  GROUP BY project, bundle_id, os_system
)
SELECT
  project,
  bundle_id,
  os_system,
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
- CK 连接烟测：`SELECT 1` 成功；`shucang_market.tj_ad_spend_active_v2` 最新 `active_date=2026-06-16`。

验证窗口参数：

```text
baseline_start=2026-06-03
baseline_end=2026-06-09
current_start=2026-06-10
current_end=2026-06-16
```

Top 输出摘要：

| project | bundle_id | os_system | baseline_avg_dau | current_avg_dau | dau_delta | dau_wow_rate | baseline_avg_dnu | current_avg_dnu | dnu_delta | dnu_wow_rate |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BB | com.kcolb.juggle | Android | 52,534,564 | 47,657,958 | -4,876,606 | -9.28% | 1,629,758 | 1,725,363 | 95,606 | 5.87% |
| BB | com.kcolbpuzzle.us.ios | iOS | 23,049,280 | 22,255,107 | -794,173 | -3.45% | 238,311 | 235,222 | -3,089 | -1.30% |
| MJ2 | com.nebula.mahjongtile | Android | 4,001,652 | 3,707,173 | -294,479 | -7.36% | 397,355 | 375,539 | -21,816 | -5.49% |
| BC | com.wood.kcolb.sudoku.puzzle.bm | Android | 2,299,712 | 2,076,136 | -223,575 | -9.72% | 142,663 | 122,470 | -20,193 | -14.15% |

## 风险与陷阱

- 该 SQL 是大盘设备口径，不替代 AF ODS install 或 activation 分母。
- DNU 必须用 `age_bucket='D0'` 条件聚合，不要按 `age_bucket` 分组后再手工相加。
- 当前验证窗口显示 BB Android DAU 下降但 DNU 上升；解释时需要结合 source/channel 拆解，不要只看 DAU。
- 若用于周报复刻，必须替换为报告对应的两个完整 7 日窗口。
