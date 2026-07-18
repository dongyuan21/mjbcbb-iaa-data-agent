# Verified SQL: MI ROI360 分媒体导出与 D360 零值排查模板

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260715_roi360_media_export_d360_zero_diagnosis` |
| 状态 | verified |
| promotion_status | verified_sql |
| sql_status | verified |
| 运行来源 | 本文档 `### Canonical SQL` 下唯一的 `sql` fence |
| 关联 SOP | `../analysis_sop/20260702_MI_ROI360分媒体导出与D360零值排查SOP.md` |
| 适用场景 | MI ROI360 分媒体导出 + D360=0 覆盖率诊断 + 高消耗样例行 + 自然量分摊试算 |
| 最后验证 | 2026-07-15 |
| validation_method | manual_small_window |
| owner | Cursor Agent |
| supersedes | [] |
| 源 candidate | `candidate_sql/roi/roi360_media_export_d360_zero_diagnosis.sql`（晋升后已移除） |

## 原始问题

> 对 MI ROI360 分媒体导出做 D360=0 专项排查：哪些媒体/国家 D360 为 0？是 country_group=other 没有预测覆盖，还是高消耗行仍为 0 需要检查 update_at 与预测任务时序？

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | `active_date BETWEEN '${start_date}' AND '${end_date}'` |
| Part A 粒度 | `bundle_id × media_source`（dim_level=bundle_media） |
| Part B1 粒度 | `bundle_id × media_source × country_group`（dim_level=bundle_media_country） |
| Part B2 粒度 | `campaign × country` 行级（dim_level=bundle_media_campaign_country） |
| Part C 粒度 | `bundle_id × media_source × scenario`（ARRAY JOIN 三版试算） |
| 消耗 | 折后 `cost_zhe` |
| 回收 | `sdk_revenue_day1`（D1）和 `sdk_revenue_day360`（D360 预估补全） |
| D360=0 诊断 | `countIf(sdk_revenue_day360=0)` 占比 + `diagnosis_hint` 分层标记 |

## 依赖表

| 表 | 用途 |
|---|---|
| `shucang_market.ads_market_roi_cohort_sdk_multidim` | ROI cohort 多维宽表，消耗+回收+预测+country_group |

## 复用参数

| 参数 | 说明 |
|---|---|
| `${start_date}` | 窗口起始日，如 `2026-07-08` |
| `${end_date}` | 窗口结束日，如 `2026-07-14` |
| `${bundle_ids}` | 包体列表，如 `'com.kcolb.juggle','com.kcolbpuzzle.us.ios'` |
| `${dim_level}` | 推荐 `bundle_media` 或 `bundle_media_country` |

## 风险与陷阱

- 所有查询必须显式过滤单一 `dim_level`，避免跨 rollup 重复统计。
- D360 长周期列是**预估补全口径**；D360=0 不能直接解释为停投或真实 D360 LTV/ROI 为 0。
- 自然量分摊（Part C）是**经营试算**，不是 AF/MMP 真实归因。
- 禁止 SELECT *；占比必须两阶段聚合（media_rollup → totals → 最终 SELECT）。
- D360=0 且 cost_zhe>100 时需检查 `update_at`、`country_group`、forecast 任务时序。
- Part B2 不输出 `campaign_id` / `campaign_name` 原始明细。
- 无 PII；输出为聚合或去标识样例行。

## 验证记录

### 2026-07-15 · ClickHouse 实时探测

探测：`ads_market_roi_cohort_sdk_multidim` max(active_date)=2026-07-14, max(update_at)=2026-07-15 17:48:23。

| 验证批次 | Part | 窗口 | 行数 | 结果摘要 |
|---|---|---|---|---|
| smoke-A | A: 分媒体 ROI360 | 07-08..07-14 | 10+ | Google cost=$1,290,454.65 (45.6%), ROI360=60.19%; Aura $478,188.18 (16.9%), ROI360=78.50% |
| smoke-B1 | B1: D360=0 覆盖率 | 07-08..07-14 | 10+ | country_group=other 全部 D360=0（diagnosis_hint 正确触发）；Top 媒体 google/aura/dt/applovin/vivo 均命中 |
| smoke-B2 | B2: 高消耗样例行 | 07-08..07-14 | 5 | 2026-07-14 aura_int×US cost=$18,337 D360=0; DT×US $10,861 D360=0; google×other $10,098 D360=0 |
| smoke-C | C: 自然量分摊 | 07-08..07-14 | 10+ | scenario=all 原始全渠道口径正常输出，allocated_organic_dnu=0（all 场景下不分摊） |

Part B1 诊断命中示例：

| media_source | country_group | cost_zhe | d360_zero_rate | diagnosis_hint |
|---|---|---|---|---|
| googleadwords_int | other | 417,132.03 | 1.0 | country_group=other，可能没有预测覆盖 |
| aura_int | other | 120,497.26 | 1.0 | country_group=other，可能没有预测覆盖 |
| digitalturbine_int | other | 91,321.45 | 1.0 | country_group=other，可能没有预测覆盖 |

Part B2 高消耗 D360=0 样例行示例：

| active_date | media_source | country_group | cost_zhe | sdk_rev_d1 | sdk_rev_d360 | actual_roi_days |
|---|---|---|---|---|---|---|
| 2026-07-14 | aura_int | US | 18,337.35 | 2,159.31 | 0.0 | 1 |
| 2026-07-14 | digitalturbine_int | US | 10,860.94 | 1,347.06 | 0.0 | 1 |
| 2026-07-14 | googleadwords_int | other | 10,097.52 | 799.35 | 0.0 | 1 |

## SQL

### Canonical SQL

> 四段查询分别执行。参数替换后按 A → B1 → B2 → C 顺序运行。

```sql
/* A) 分产品 × 分媒体 ROI360 / LTV0 / LTV360 / 分布占比 */
WITH
    media_rollup AS (
        SELECT
            bundle_id,
            any(pag_name) AS pag_name,
            any(os_system) AS os_system,
            media_source,
            sum(toFloat64(cost_zhe)) AS total_cost_zhe,
            sum(toFloat64(registers)) AS total_registers,
            sum(toFloat64(media_installs)) AS total_media_installs,
            sum(toFloat64(sdk_revenue_day1)) AS sdk_revenue_d1,
            sum(toFloat64(sdk_revenue_day360)) AS sdk_revenue_d360,
            max(actual_roi_days) AS max_actual_roi_days,
            max(update_at) AS latest_update_at,
            count() AS source_rows,
            countIf(toFloat64(sdk_revenue_day360) = 0) AS d360_zero_rows
        FROM shucang_market.ads_market_roi_cohort_sdk_multidim
        WHERE active_date BETWEEN '${start_date}' AND '${end_date}'
          AND dim_level = '${dim_level}'
          AND bundle_id IN (${bundle_ids})
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
    m.os_system,
    m.media_source,
    m.total_cost_zhe,
    m.total_registers,
    m.total_media_installs,
    round(m.sdk_revenue_d1 / nullIf(m.total_registers, 0), 6) AS ltv0,
    round(m.sdk_revenue_d360 / nullIf(m.total_registers, 0), 6) AS ltv360,
    round(m.sdk_revenue_d360 / nullIf(m.total_cost_zhe, 0) * 100, 4) AS roi360_pct,
    round(m.total_cost_zhe / nullIf(t.all_cost_zhe, 0), 6) AS cost_zhe_share,
    round(m.sdk_revenue_d1 / nullIf(t.all_sdk_revenue_d1, 0), 6) AS ltv0_distribution_share,
    round(m.sdk_revenue_d360 / nullIf(t.all_sdk_revenue_d360, 0), 6) AS ltv360_distribution_share,
    m.max_actual_roi_days,
    m.latest_update_at,
    m.source_rows,
    m.d360_zero_rows,
    round(m.d360_zero_rows / nullIf(m.source_rows, 0), 6) AS d360_zero_rate
FROM media_rollup AS m
INNER JOIN totals AS t ON 1 = 1
ORDER BY
    m.bundle_id,
    m.total_cost_zhe DESC;

/* B1) D360=0 覆盖率: Top 国家 / other / 高消耗行诊断 */
WITH
    coverage AS (
        SELECT
            bundle_id,
            any(pag_name) AS pag_name,
            any(os_system) AS os_system,
            media_source,
            country_group,
            sum(toFloat64(cost_zhe)) AS total_cost_zhe,
            sum(toFloat64(registers)) AS total_registers,
            sum(toFloat64(sdk_revenue_day360)) AS sdk_revenue_d360,
            max(actual_roi_days) AS max_actual_roi_days,
            max(update_at) AS latest_update_at,
            count() AS source_rows,
            countIf(toFloat64(cost_zhe) > 100) AS cost_gt_100_rows,
            countIf(toFloat64(cost_zhe) > 100 AND toFloat64(sdk_revenue_day360) = 0) AS cost_gt_100_d360_zero_rows,
            countIf(toFloat64(sdk_revenue_day360) = 0) AS d360_zero_rows
        FROM shucang_market.ads_market_roi_cohort_sdk_multidim
        WHERE active_date BETWEEN '${start_date}' AND '${end_date}'
          AND dim_level = 'bundle_media_country'
          AND bundle_id IN (${bundle_ids})
          AND media_source NOT IN ('all', '')
        GROUP BY
            bundle_id,
            media_source,
            country_group
    )
SELECT
    bundle_id,
    pag_name,
    os_system,
    media_source,
    country_group,
    total_cost_zhe,
    total_registers,
    sdk_revenue_d360,
    max_actual_roi_days,
    latest_update_at,
    source_rows,
    cost_gt_100_rows,
    cost_gt_100_d360_zero_rows,
    d360_zero_rows,
    round(d360_zero_rows / nullIf(source_rows, 0), 6) AS d360_zero_rate,
    multiIf(
        country_group = 'other', 'country_group=other，可能没有预测覆盖',
        cost_gt_100_d360_zero_rows > 0, 'Top国家/高消耗行仍为0，继续检查 update_at 与预测任务时序',
        d360_zero_rows > 0, '存在低消耗或部分维度 D360=0，需抽样明细',
        'D360 覆盖正常'
    ) AS diagnosis_hint
FROM coverage
ORDER BY
    cost_gt_100_d360_zero_rows DESC,
    total_cost_zhe DESC;

/* B2) D360=0 高消耗样例行 */
SELECT
    active_date,
    dim_level,
    bundle_id,
    pag_name,
    os_system,
    media_source,
    country_group,
    toFloat64(cost_zhe) AS cost_zhe,
    toFloat64(registers) AS registers,
    toFloat64(sdk_revenue_day1) AS sdk_revenue_d1,
    toFloat64(sdk_revenue_day360) AS sdk_revenue_d360,
    toFloat64(sdk_roi_day360) AS sdk_roi_d360,
    actual_roi_days,
    update_at,
    1 AS source_rows
FROM shucang_market.ads_market_roi_cohort_sdk_multidim
WHERE active_date BETWEEN '${start_date}' AND '${end_date}'
  AND dim_level = 'bundle_media_campaign_country'
  AND bundle_id IN (${bundle_ids})
  AND media_source NOT IN ('all', '')
  AND toFloat64(cost_zhe) > 100
  AND toFloat64(sdk_revenue_day360) = 0
ORDER BY
    update_at DESC,
    cost_zhe DESC
LIMIT 200;

/* C) 自然量分摊 UA 渠道经营试算 */
WITH
    base AS (
        SELECT
            bundle_id,
            any(pag_name) AS pag_name,
            media_source,
            sum(toFloat64(cost_zhe)) AS total_cost_zhe,
            sum(toFloat64(registers)) AS dnu,
            sum(toFloat64(sdk_revenue_day1)) AS sdk_revenue_d1,
            sum(toFloat64(sdk_revenue_day360)) AS sdk_revenue_d360,
            max(update_at) AS latest_update_at,
            count() AS source_rows
        FROM shucang_market.ads_market_roi_cohort_sdk_multidim
        WHERE active_date BETWEEN '${start_date}' AND '${end_date}'
          AND dim_level = 'bundle_media'
          AND bundle_id IN (${bundle_ids})
          AND media_source NOT IN ('all', '')
        GROUP BY
            bundle_id,
            media_source
    ),
    totals AS (
        SELECT
            bundle_id,
            sumIf(dnu, media_source = 'organic') AS organic_dnu,
            sumIf(sdk_revenue_d1, media_source = 'organic') AS organic_revenue_d1,
            sumIf(sdk_revenue_d360, media_source = 'organic') AS organic_revenue_d360,
            sumIf(dnu, media_source != 'organic') AS total_paid_dnu
        FROM base
        GROUP BY bundle_id
    )
SELECT
    scenario,
    b.bundle_id,
    b.pag_name,
    b.media_source,
    b.total_cost_zhe AS cost_zhe,
    b.dnu AS reported_dnu,
    if(
        scenario = 'allocated_organic',
        t.organic_dnu * b.dnu / nullIf(t.total_paid_dnu, 0),
        0
    ) AS allocated_organic_dnu,
    b.dnu + allocated_organic_dnu AS adjusted_dnu,
    round(
        (
            b.sdk_revenue_d1
            + if(
                scenario = 'allocated_organic',
                t.organic_revenue_d1 * b.dnu / nullIf(t.total_paid_dnu, 0),
                0
            )
        ) / nullIf(adjusted_dnu, 0),
        6
    ) AS ltv0,
    round(
        (
            b.sdk_revenue_d360
            + if(
                scenario = 'allocated_organic',
                t.organic_revenue_d360 * b.dnu / nullIf(t.total_paid_dnu, 0),
                0
            )
        ) / nullIf(adjusted_dnu, 0),
        6
    ) AS ltv360,
    multiIf(
        scenario = 'all', '原始全渠道口径，包含 organic；非 AF/MMP 真实归因重分配',
        scenario = 'paid_only', '仅 UA 付费渠道，不分摊自然量；非 AF/MMP 真实归因',
        '按 paid_dnu 权重分摊 organic 的经营试算；非 AF/MMP 真实归因'
    ) AS attribution_note,
    b.latest_update_at,
    b.source_rows
FROM base AS b
INNER JOIN totals AS t ON b.bundle_id = t.bundle_id
ARRAY JOIN ['all', 'paid_only', 'allocated_organic'] AS scenario
WHERE scenario = 'all' OR b.media_source != 'organic'
ORDER BY
    b.bundle_id,
    scenario,
    b.total_cost_zhe DESC;
```
