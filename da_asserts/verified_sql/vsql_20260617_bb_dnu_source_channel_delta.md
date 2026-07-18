# BB DNU source / channel 贡献拆解

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260617_bb_dnu_source_channel_delta` |
| 状态 | verified |
| 适用场景 | BB GP 激活 DNU 按一级渠道、厂商、media_source 拆 WoW 贡献 |
| 数据源 | `h-s.dwd_market_appsflyer_activation_push_data_di`, `h-s.dim_market_channel_mapping_da` |
| 最后验证 | 2026-06-17 |

## 口径说明

- 产品范围：`bundle_id = 'com.kcolb.juggle'`。
- 时间口径：激活日期使用 `SUBSTR(active_time_utc8, 1, 10)`；`dt` 作为 UTC0 分区过滤向前多扫 1 天，避免 UTC8 切日漏数。
- 验证窗口：baseline `2026-06-03` ~ `2026-06-09`，current `2026-06-10` ~ `2026-06-16`。
- DNU：`COUNT(DISTINCT COALESCE(customer_user_id, appsflyer_id))`，仅输出聚合，不输出用户/设备明细。
- 渠道映射：`media_source` 左连接 `dim_market_channel_mapping_da.channel_media_source`；`tiktokglobal_int` 与 `bytedanceglobal_int` 先归一为 `bytedanceglobal_int`。
- 边界：activation DWD 是归因/校准表，非默认安装分母；涉及 official KPI 时仍按 `口径决策记录.md` 输出 all + paid_only 或改用 AF ODS install。

## SQL

```sql
WITH activation AS (
  SELECT
    CASE
      WHEN SUBSTR(CAST(active_time_utc8 AS STRING), 1, 10) BETWEEN '${baseline_start}' AND '${baseline_end}' THEN 'baseline'
      WHEN SUBSTR(CAST(active_time_utc8 AS STRING), 1, 10) BETWEEN '${current_start}' AND '${current_end}' THEN 'current'
    END AS period,
    media_source,
    COUNT(DISTINCT COALESCE(customer_user_id, appsflyer_id)) AS dnu
  FROM h-s.dwd_market_appsflyer_activation_push_data_di
  WHERE dt BETWEEN '${dt_start_utc0}' AND '${current_end}'
    AND SUBSTR(CAST(active_time_utc8 AS STRING), 1, 10) BETWEEN '${baseline_start}' AND '${current_end}'
    AND bundle_id = 'com.kcolb.juggle'
  GROUP BY
    CASE
      WHEN SUBSTR(CAST(active_time_utc8 AS STRING), 1, 10) BETWEEN '${baseline_start}' AND '${baseline_end}' THEN 'baseline'
      WHEN SUBSTR(CAST(active_time_utc8 AS STRING), 1, 10) BETWEEN '${current_start}' AND '${current_end}' THEN 'current'
    END,
    media_source
),
mapped AS (
  SELECT
    a.period,
    COALESCE(m.channel_category, '未映射') AS channel_category,
    COALESCE(m.vendor_name, '未映射') AS vendor_name,
    a.media_source,
    SUM(a.dnu) AS dnu
  FROM activation a
  LEFT JOIN h-s.dim_market_channel_mapping_da m
    ON CASE
         WHEN a.media_source IN ('tiktokglobal_int', 'bytedanceglobal_int') THEN 'bytedanceglobal_int'
         ELSE a.media_source
       END = m.channel_media_source
  WHERE a.period IS NOT NULL
  GROUP BY COALESCE(m.channel_category, '未映射'), COALESCE(m.vendor_name, '未映射'), a.media_source, a.period
),
pivoted AS (
  SELECT
    channel_category,
    vendor_name,
    media_source,
    SUM(CASE WHEN period = 'baseline' THEN dnu ELSE 0 END) AS baseline_dnu,
    SUM(CASE WHEN period = 'current' THEN dnu ELSE 0 END) AS current_dnu
  FROM mapped
  GROUP BY channel_category, vendor_name, media_source
),
with_delta AS (
  SELECT
    channel_category,
    vendor_name,
    media_source,
    baseline_dnu,
    current_dnu,
    current_dnu - baseline_dnu AS dnu_delta,
    SUM(current_dnu - baseline_dnu) OVER () AS total_delta
  FROM pivoted
)
SELECT
  channel_category,
  vendor_name,
  media_source,
  baseline_dnu,
  current_dnu,
  dnu_delta,
  CASE WHEN baseline_dnu <> 0 THEN dnu_delta / baseline_dnu END AS dnu_delta_rate,
  CASE WHEN total_delta <> 0 THEN dnu_delta / total_delta END AS delta_contribution
FROM with_delta
WHERE baseline_dnu + current_dnu > 0
ORDER BY dnu_delta ASC
LIMIT 80;
```

### 一级渠道汇总

```sql
WITH activation AS (
  SELECT
    CASE
      WHEN SUBSTR(CAST(active_time_utc8 AS STRING), 1, 10) BETWEEN '${baseline_start}' AND '${baseline_end}' THEN 'baseline'
      WHEN SUBSTR(CAST(active_time_utc8 AS STRING), 1, 10) BETWEEN '${current_start}' AND '${current_end}' THEN 'current'
    END AS period,
    media_source,
    COUNT(DISTINCT COALESCE(customer_user_id, appsflyer_id)) AS dnu
  FROM h-s.dwd_market_appsflyer_activation_push_data_di
  WHERE dt BETWEEN '${dt_start_utc0}' AND '${current_end}'
    AND SUBSTR(CAST(active_time_utc8 AS STRING), 1, 10) BETWEEN '${baseline_start}' AND '${current_end}'
    AND bundle_id = 'com.kcolb.juggle'
  GROUP BY
    CASE
      WHEN SUBSTR(CAST(active_time_utc8 AS STRING), 1, 10) BETWEEN '${baseline_start}' AND '${baseline_end}' THEN 'baseline'
      WHEN SUBSTR(CAST(active_time_utc8 AS STRING), 1, 10) BETWEEN '${current_start}' AND '${current_end}' THEN 'current'
    END,
    media_source
),
mapped AS (
  SELECT
    a.period,
    COALESCE(m.channel_category, '未映射') AS channel_category,
    SUM(a.dnu) AS dnu
  FROM activation a
  LEFT JOIN h-s.dim_market_channel_mapping_da m
    ON CASE
         WHEN a.media_source IN ('tiktokglobal_int', 'bytedanceglobal_int') THEN 'bytedanceglobal_int'
         ELSE a.media_source
       END = m.channel_media_source
  WHERE a.period IS NOT NULL
  GROUP BY COALESCE(m.channel_category, '未映射'), a.period
),
pivoted AS (
  SELECT
    channel_category,
    SUM(CASE WHEN period = 'baseline' THEN dnu ELSE 0 END) AS baseline_dnu,
    SUM(CASE WHEN period = 'current' THEN dnu ELSE 0 END) AS current_dnu
  FROM mapped
  GROUP BY channel_category
),
with_delta AS (
  SELECT
    channel_category,
    baseline_dnu,
    current_dnu,
    current_dnu - baseline_dnu AS dnu_delta,
    SUM(current_dnu - baseline_dnu) OVER () AS total_delta
  FROM pivoted
)
SELECT
  channel_category,
  baseline_dnu,
  current_dnu,
  dnu_delta,
  CASE WHEN baseline_dnu <> 0 THEN dnu_delta / baseline_dnu END AS dnu_delta_rate,
  CASE WHEN total_delta <> 0 THEN dnu_delta / total_delta END AS delta_contribution
FROM with_delta
ORDER BY dnu_delta ASC;
```

## 验证记录

2026-06-17 使用 MaxCompute helper 真实执行通过。执行前探测：

- `h-s.dwd_market_appsflyer_activation_push_data_di` 最新分区：`2026-06-17`。
- `h-s.dim_market_channel_mapping_da` 当前行数：`415`。
- MC 连接烟测：`SELECT 1` 成功。

验证窗口参数：

```text
baseline_start=2026-06-03
baseline_end=2026-06-09
current_start=2026-06-10
current_end=2026-06-16
dt_start_utc0=2026-06-02
```

一级渠道摘要：

| channel_category | baseline_dnu | current_dnu | delta | delta_rate | contribution |
|---|---:|---:|---:|---:|---:|
| 自然 | 4,778,609 | 4,525,468 | -253,141 | -5.30% | -14.16% |
| 其他 | 586 | 565 | -21 | -3.58% | 0.00% |
| 未映射 | 18 | 44 | 26 | 144.44% | 0.00% |
| Media Buy | 2,612,734 | 2,629,944 | 17,210 | 0.66% | 0.96% |
| 预装 | 5,920,317 | 7,944,104 | 2,023,787 | 34.18% | 113.20% |

media_source 摘要：

| channel_category | vendor_name | media_source | baseline_dnu | current_dnu | delta | delta_rate |
|---|---|---|---:|---:|---:|---:|
| 自然 | 自然 | organic | 4,778,609 | 4,525,468 | -253,141 | -5.30% |
| Media Buy | TikTok | tiktokglobal_int | 192,410 | 141,926 | -50,484 | -26.24% |
| 预装 | DT | digitalturbine_int | 750,681 | 726,080 | -24,601 | -3.28% |
| Media Buy | Google | googleadwords_int | 1,700,559 | 1,738,954 | 38,395 | 2.26% |
| 预装 | OPPO | oppoglobal_int | 432,734 | 1,296,562 | 863,828 | 199.62% |
| 预装 | VIVO | vivoglobal_int | 473,755 | 1,374,017 | 900,262 | 190.03% |

## 风险与陷阱

- 这是 activation DWD 归因拆解，不替代默认安装分母；正式安装 KPI 优先看 AF ODS install。
- `active_time_utc8` 用于业务日期，`dt` 是 UTC0 分区；查询必须保留分区缓冲，避免 UTC8 切日漏数。
- `organic` 是否进入官方 KPI 仍需业务签字；按分析协议默认应同时输出 all 和 paid_only。
- `dim_market_channel_mapping_da` 是小维表但仍为 `partial_verified`，新增 media_source 可能产生 `未映射`，应保留未映射行。
- 当前验证窗口显示 BB GP activation DNU 总体增加主要来自预装 OPPO / VIVO，不能套用旧窗口“UA 下滑”为默认结论。
