# Verified SQL: LTV 倍率下降归因 - LTV 三线趋势 + 留存 vs ARPDAU 拆解

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260715_ltv_multiplier_drop_diagnosis` |
| 状态 | verified |
| promotion_status | verified_sql |
| sql_status | verified |
| 运行来源 | 本文档 `### Canonical SQL` 下唯一的 `sql` fence |
| 关联 SOP | `../analysis_sop/20260423_LTV倍率下降归因SOP.md` |
| 适用场景 | LTV 倍率（LTV_N/LTV_0）下降时，拆解 D0 抬升/长期塌方/两者叠加，并拆成留存和 ARPDAU 贡献定位主因 |
| 最后验证 | 2026-07-15 |
| validation_method | manual_small_window |
| owner | Cursor Agent |
| supersedes | [] |
| 源 candidate | `candidate_sql/ltv_multiplier_drop_diagnosis.sql`（晋升后已移除） |

## 原始问题

> 当 LTV 倍率下降时，需要拆成可验证的分子分母问题，先定位变化属于入水口抬升、长期塌方还是两者叠加，再用留存和 ARPDAU 拆解主因。

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | `active_date` 按日，cohort 成熟度由 `actual_roi_days` 决定 |
| 粒度 | `bundle_id × media_source × active_date`（dim_level=bundle_media） |
| LTV_0 | `sdk_revenue_day1 / registers`（首日回收 LTV） |
| LTV_7 | `sdk_revenue_day7 / registers` |
| LTV_30 | `sdk_revenue_day30 / registers` |
| 倍率 D7/D1 | `sdk_revenue_day7 / sdk_revenue_day1` |
| 倍率 D30/D1 | `sdk_revenue_day30 / sdk_revenue_day1` |
| D7 留存率 | `sdk_retention_day7 / registers` |
| ARPDAU_7 估算 | `sdk_revenue_day7 / sdk_retention_day7`（D7 回收 / D7 活跃用户） |

## 依赖表

| 表 | 用途 |
|---|---|
| `shucang_market.ads_market_roi_cohort_sdk_multidim` | ROI cohort 多维宽表，消耗+回收+预测+留存 |

## 复用参数

| 参数 | 说明 |
|---|---|
| `${start_date}` | 窗口起始日，如 `2026-07-08` |
| `${end_date}` | 窗口结束日，如 `2026-07-14` |
| `${bundle_ids}` | 包体列表，如 `'com.kcolb.juggle'` |

## 风险与陷阱

- `sdk_revenue_dayN` 在超过 `actual_roi_days` 后为**预估补全**，非真实回收；判断倍率变化时需确认 cohort 成熟度。
- `sdk_retention_day7` 在 cohort 太新（actual_roi_days < 7）时为 0，ARPDAU 估算会返回 NULL，这是正常行为，不是数据缺失。
- 倍率下降判断需**同 weekday WoW** 比较，单日波动不能直接归因。
- `dim_level` 必须固定为 `bundle_media`，避免跨 rollup 重复统计。
- 输出为聚合诊断，不输出用户级明细，无 PII 风险。

## 验证记录

### 2026-07-15 · ClickHouse 实时探测

探测：`ads_market_roi_cohort_sdk_multidim` max(active_date)=2026-07-14, max(update_at)=2026-07-15 17:48:23。

| 验证批次 | 窗口 | 行数 | 结果摘要 |
|---|---|---|---|
| smoke-1 | 2026-07-08..2026-07-14 | 20 行 | Google ltv0=0.0433, ltv7=0.1164, ltv30=0.2032, multiplier_d7=2.69, multiplier_d30=4.69; Aura ltv0=0.1033, ltv7=0.2177, ltv30=0.3800, multiplier_d7=2.11, multiplier_d30=3.68 |

Top 3 媒体示例（2026-07-08）：

| media_source | ltv0 | ltv7 | ltv30 | mult_d7 | mult_d30 | d7_retention | arpdau_d7 |
|---|---|---|---|---|---|---|---|
| googleadwords_int | 0.0433 | 0.1164 | 0.2032 | 2.69 | 4.69 | 0.0 | NULL |
| aura_int | 0.1033 | 0.2177 | 0.3800 | 2.11 | 3.68 | 0.0 | NULL |
| digitalturbine_int | 0.0613 | 0.1196 | 0.2072 | 1.95 | 3.38 | 0.0 | NULL |

注：`actual_roi_days=6`，cohort 未到 D7，所以 `sdk_retention_day7=0` 且 `arpdau_d7_est=NULL`，符合预期。

## SQL

### Canonical SQL

```sql
/* LTV_MULTIPLIER_DROP_DIAGNOSIS */
SELECT
    bundle_id,
    media_source,
    active_date,
    actual_roi_days,
    sum(toFloat64(registers)) AS total_registers,
    sum(toFloat64(cost_zhe)) AS total_cost_zhe,
    sum(toFloat64(sdk_revenue_day1)) AS sdk_rev_d1,
    sum(toFloat64(sdk_revenue_day7)) AS sdk_rev_d7,
    sum(toFloat64(sdk_revenue_day30)) AS sdk_rev_d30,
    sum(toFloat64(sdk_retention_day7)) AS retain_users_d7,
    -- LTV 三线
    round(sum(toFloat64(sdk_revenue_day1)) / nullIf(sum(toFloat64(registers)), 0), 6) AS ltv0,
    round(sum(toFloat64(sdk_revenue_day7)) / nullIf(sum(toFloat64(registers)), 0), 6) AS ltv7,
    round(sum(toFloat64(sdk_revenue_day30)) / nullIf(sum(toFloat64(registers)), 0), 6) AS ltv30,
    -- 倍率
    round(sum(toFloat64(sdk_revenue_day7)) / nullIf(sum(toFloat64(sdk_revenue_day1)), 0), 4) AS multiplier_d7_over_d1,
    round(sum(toFloat64(sdk_revenue_day30)) / nullIf(sum(toFloat64(sdk_revenue_day1)), 0), 4) AS multiplier_d30_over_d1,
    -- D7 留存率
    round(sum(toFloat64(sdk_retention_day7)) / nullIf(sum(toFloat64(registers)), 0), 6) AS d7_retention_rate,
    -- ARPDAU_7 估算（D7 回收 / D7 活跃用户）
    round(sum(toFloat64(sdk_revenue_day7)) / nullIf(sum(toFloat64(sdk_retention_day7)), 0), 6) AS arpdau_d7_est
FROM shucang_market.ads_market_roi_cohort_sdk_multidim
WHERE active_date BETWEEN '${start_date}' AND '${end_date}'
  AND dim_level = 'bundle_media'
  AND bundle_id IN (${bundle_ids})
  AND media_source NOT IN ('all', '')
GROUP BY
    bundle_id,
    media_source,
    active_date,
    actual_roi_days
ORDER BY
    bundle_id,
    active_date,
    media_source
```
