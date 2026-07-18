# Verified SQL: BB GP Latest 7 天分媒体 ROI360 分布

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260715_bb_gp_latest_7d_media_roi360_distribution` |
| 状态 | verified |
| promotion_status | verified_sql |
| sql_status | verified |
| 运行来源 | 本文档 `### Canonical SQL` 下唯一的 `sql` fence |
| 适用场景 | kcolb tsalb GP (com.kcolb.juggle) 最近 7 个 active_date 的分媒体 ROI360 / LTV0 / LTV360 / 消耗占比分布 |
| 最后验证 | 2026-07-15 |
| validation_method | manual_small_window |
| owner | Cursor Agent |
| supersedes | [] |
| 源 candidate | `candidate_sql/roi/bb_gp_latest_7d_media_roi360_distribution.sql`（晋升后已移除） |

## 原始问题

> 对 BB GP 最新 7 天 ROI360 做分媒体拆解，输出消耗、LTV0、LTV360、ROI360、消耗占比和 D360=0 行占比。

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | `active_date` 最近 7 个完整日 |
| 粒度 | `bundle_id × media_source`（dim_level=bundle_media） |
| 消耗 | 折后 `cost_zhe`（人民币口径） |
| 回收 | `sdk_revenue_day1`（D1）和 `sdk_revenue_day360`（D360 预估补全） |
| LTV0 | `sdk_revenue_day1 / registers` |
| LTV360 | `sdk_revenue_day360 / registers` |
| ROI360 | `sdk_revenue_day360 / cost_zhe * 100` |
| 消耗占比 | `媒体消耗 / 全媒体消耗`（两阶段聚合） |
| D360=0 行占比 | `countIf(sdk_revenue_day360=0) / count()` |

## 依赖表

| 表 | 用途 |
|---|---|
| `shucang_market.ads_market_roi_cohort_sdk_multidim` | ROI cohort 多维宽表，消耗+回收+预测 |

## 复用参数

| 参数 | 说明 |
|---|---|
| `${start_date}` | 窗口起始日，如 `2026-07-08` |
| `${end_date}` | 窗口结束日，如 `2026-07-14` |

## 风险与陷阱

- `sdk_revenue_day360` 包含预估补全，`actual_roi_days` 最大值表明当前成熟度，**不是真实 D360 回收**。
- `d360_zero_rows` / `d360_zero_rate` 仅表示 D360 列值为 0 的行数占比，不能直接解释为停投或真实 D360 LTV/ROI 为 0。
- `os_system = 'Android'` 固定过滤，不覆盖 iOS。
- `media_source NOT IN ('all', '')` 排除 rollup 行和空媒体。
- 无 PII；输出为聚合粒度。

## 验证记录

### 2026-07-15 · ClickHouse 实时探测

探测：`ads_market_roi_cohort_sdk_multidim` max(active_date)=2026-07-14, max(update_at)=2026-07-15 17:48:23。

| 验证批次 | 窗口 | 行数 | 结果摘要 |
|---|---|---|---|
| smoke-1 | 2026-07-08..2026-07-14 | 61 行 | Google 消耗 $1,290,454.65 (45.6% share), ROI360=60.19%; Aura $478,188.18 (16.9%), ROI360=78.50%; DT $336,185.46 (11.9%), ROI360=75.78% |

Top 5 媒体示例：

| media_source | cost_zhe | registers | ltv0 | ltv360 | roi360_pct | cost_share | d360_zero_rate |
|---|---|---|---|---|---|---|---|
| googleadwords_int | 1,290,454.65 | 1,990,246 | 0.0475 | 0.3903 | 60.19 | 0.4555 | 0.2857 |
| aura_int | 478,188.18 | 475,353 | 0.1070 | 0.7897 | 78.50 | 0.1688 | 0.2857 |
| digitalturbine_int | 336,185.46 | 670,219 | 0.0589 | 0.3801 | 75.78 | 0.1187 | 0.2857 |
| applovin_int | 201,449.67 | 379,332 | 0.0255 | 0.2824 | 53.17 | 0.0711 | 0.2857 |
| moloco_int | 123,193.44 | 67,136 | 0.1177 | 1.0345 | 56.37 | 0.0435 | 0.2857 |

## SQL

### Canonical SQL

```sql
/* BB_GP_LATEST_7D_MEDIA_ROI360_DISTRIBUTION */
WITH
    media_rollup AS (
        SELECT
            bundle_id,
            any(pag_name) AS pag_name,
            any(os_system) AS product_os,
            media_source,
            sum(toFloat64(cost_zhe)) AS total_cost_zhe,
            sum(toFloat64(registers)) AS total_registers,
            sum(toFloat64(media_installs)) AS total_media_installs,
            sum(toFloat64(sdk_revenue_day1)) AS sdk_revenue_d1,
            sum(toFloat64(sdk_revenue_day360)) AS sdk_revenue_d360,
            min(actual_roi_days) AS min_actual_roi_days,
            max(actual_roi_days) AS max_actual_roi_days,
            max(update_at) AS latest_update_at,
            count() AS source_rows,
            countIf(toFloat64(sdk_revenue_day360) = 0) AS d360_zero_rows
        FROM shucang_market.ads_market_roi_cohort_sdk_multidim
        WHERE active_date BETWEEN '${start_date}' AND '${end_date}'
          AND dim_level = 'bundle_media'
          AND bundle_id = 'com.kcolb.juggle'
          AND os_system = 'Android'
          AND media_source NOT IN ('all', '')
        GROUP BY
            bundle_id,
            media_source
    ),
    totals AS (
        SELECT
            sum(total_cost_zhe) AS all_cost_zhe,
            sum(sdk_revenue_d1) AS all_sdk_revenue_d1,
            sum(sdk_revenue_d360) AS all_sdk_revenue_d360
        FROM media_rollup
    )
SELECT
    m.bundle_id,
    m.pag_name,
    m.product_os AS os_system,
    m.media_source,
    m.total_cost_zhe,
    m.total_registers,
    m.total_media_installs,
    m.sdk_revenue_d1,
    m.sdk_revenue_d360,
    round(m.sdk_revenue_d1 / nullIf(m.total_registers, 0), 6) AS ltv0,
    round(m.sdk_revenue_d360 / nullIf(m.total_registers, 0), 6) AS ltv360,
    round(m.sdk_revenue_d1 / nullIf(m.total_cost_zhe, 0) * 100, 4) AS roi1_pct,
    round(m.sdk_revenue_d360 / nullIf(m.total_cost_zhe, 0) * 100, 4) AS roi360_pct,
    round(m.total_cost_zhe / nullIf(t.all_cost_zhe, 0), 6) AS cost_zhe_share,
    round(m.sdk_revenue_d1 / nullIf(t.all_sdk_revenue_d1, 0), 6) AS ltv0_distribution_share,
    round(m.sdk_revenue_d360 / nullIf(t.all_sdk_revenue_d360, 0), 6) AS ltv360_distribution_share,
    m.min_actual_roi_days,
    m.max_actual_roi_days,
    m.latest_update_at,
    m.source_rows,
    m.d360_zero_rows,
    round(m.d360_zero_rows / nullIf(m.source_rows, 0), 6) AS d360_zero_rate
FROM media_rollup AS m
INNER JOIN totals AS t ON 1 = 1
ORDER BY
    m.total_cost_zhe DESC,
    m.media_source
LIMIT 200;
```
