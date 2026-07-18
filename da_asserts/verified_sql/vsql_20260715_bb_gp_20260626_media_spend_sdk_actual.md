# Verified SQL: BB GP 2026-06-26 分媒体消耗与 SDK 实际回收固定回放

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260715_bb_gp_20260626_media_spend_sdk_actual` |
| 状态 | verified |
| promotion_status | verified_sql |
| sql_status | verified |
| 运行来源 | 本文档 `### Canonical SQL` 下唯一的 `sql` fence |
| 适用场景 | kcolb tsalb GP 固定日期 PI 回放：分媒体消耗（USD）与 SDK 实际回收（D0 + 有界 D0-D359） |
| 最后验证 | 2026-07-15 |
| validation_method | manual_small_window |
| owner | Cursor Agent |
| supersedes | [] |
| 源 candidate | `candidate_sql/roi/bb_gp_20260626_media_spend_sdk_actual.sql`（晋升后已移除） |

## 原始问题

> 对 BB GP 2026-06-26 安装日的分媒体做消耗和 SDK 实际回收固定回放，用于 PI 对账合同。

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | 固定 `active_date = '2026-06-26'` |
| 粒度 | `media_source` |
| 消耗 | `cost_zhe / currency` → USD 口径 |
| 激活 | `registers`（AF 安装） |
| SDK 回收 D0 | `sumIf(revenue, date_diff = 0)` |
| SDK 回收累计 | `sum(revenue)` where `date_diff BETWEEN 0 AND 359` |
| 有界 date_diff | 0–359，最终成熟窗口以实际 `max(date_diff)` 为准 |

## 依赖表

| 表 | 用途 |
|---|---|
| `shucang_market.tj_ad_spend_active_v2_view` | 分媒体消耗+激活 |
| `shucang_market.tj_ad_sdk_revenue_view` | SDK 回收明细（date_diff 级） |

## 复用参数

| 参数 | 说明 |
|---|---|
| `${active_date}` | 固定回放日，如 `2026-06-26` |
| `${bundle_id}` | `com.kcolb.juggle` |

## 风险与陷阱

- 只用于固定 PI 回放合同，**不泛化到其他包体或日期**。
- 消耗使用 ROI360 折后美元口径 `cost_zhe / currency`。
- SDK 回收只取有界 D0-D359 明细；最终成熟窗口以实际返回的最大 `date_diff` 为准。
- 只读分析与预警，不输出最终投放动作。
- 无 PII；输出为聚合粒度。

## 验证记录

### 2026-07-15 · ClickHouse 实时探测

探测：`tj_ad_spend_active_v2_view` max(active_date)=2026-07-14；`tj_ad_sdk_revenue_view` max(active_date)=2026-07-14, max(date_diff)=13。

| 验证批次 | 日期 | spend 行数 | sdk_revenue 行数 | 结果摘要 |
|---|---|---|---|---|
| smoke-1 | 2026-06-26 | 26 | 36 | Google spend=$149,659.50/installs=272,799; Aura $78,881.05/72,334; DT $51,031.72/98,482. SDK: Google max_dd=18, d0=$12,587.73, total=$49,999.18; organic d0=$12,159.41, total=$48,639.42 |

Top 5 消耗媒体：

| media_source | cost_zhe_usd | af_installs |
|---|---|---|
| googleadwords_int | 149,659.50 | 272,799 |
| aura_int | 78,881.05 | 72,334 |
| applovin_int | 51,233.86 | 58,598 |
| digitalturbine_int | 51,031.72 | 98,482 |
| moloco_int | 23,605.39 | 13,115 |

Top 5 SDK 回收媒体：

| media_source | max_date_diff | d0_sdk_revenue | sdk_revenue |
|---|---|---|---|
| googleadwords_int | 18 | 12,587.73 | 49,999.18 |
| organic | 18 | 12,159.41 | 48,639.42 |
| aura_int | 18 | 8,575.13 | 26,110.57 |
| digitalturbine_int | 18 | 6,135.73 | 17,978.30 |
| applovin_int | 18 | 2,453.87 | 11,481.88 |

## SQL

### Canonical SQL

> 两个子查询分别执行，结果按 media_source 对齐。

```sql
/* BB_SPEND_20260626 */
SELECT
  media_source,
  sum(cost_zhe / nullIf(currency, 0)) AS cost_zhe_usd,
  sum(registers) AS af_installs
FROM shucang_market.tj_ad_spend_active_v2_view
WHERE active_date = '${active_date}'
  AND bundle_id = 'com.kcolb.juggle'
GROUP BY media_source
HAVING cost_zhe_usd > 0
ORDER BY cost_zhe_usd DESC
LIMIT 50;

/* BB_SDK_REVENUE_20260626 */
SELECT
  media_source,
  max(date_diff) AS max_date_diff,
  sumIf(revenue, date_diff = 0) AS d0_sdk_revenue,
  sum(revenue) AS sdk_revenue
FROM shucang_market.tj_ad_sdk_revenue_view
WHERE active_date = '${active_date}'
  AND bundle_id = 'com.kcolb.juggle'
  AND date_diff BETWEEN 0 AND 359
GROUP BY media_source
ORDER BY sdk_revenue DESC
LIMIT 50;
```
