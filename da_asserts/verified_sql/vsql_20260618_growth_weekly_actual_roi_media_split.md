# 0615 周报高风险产品实际 ROI / 媒体拆解

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260618_growth_weekly_actual_roi_media_split` |
| 状态 | verified |
| 来源 | `../raw/2026-06-15_发行增长周会_docx.md`、`../decision_cases/20260615_发行增长周会ROI_DNU风险案例.md` |
| 适用场景 | 周报 ROI 红线对象的 CK 实际短期 ROI、消耗占比、注册和 CPI 媒体拆解 |
| 负责人 | Cursor Agent |
| 最后验证 | 2026-06-18 |

## 原始问题

> 0615 周报里 Double Tile GP、Sudoku Master GP、Solitaire Master iOS、Word Solitaire Go iOS、Arrows Blast GP 的 ROI 风险，哪些可以由 CK 实际回收和媒体结构先验证？

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | `active_date` cohort；本次验证 baseline=`2026-05-29`~`2026-06-04`，current=`2026-06-05`~`2026-06-11` |
| 维度 | `period × product × bundle_id × media_source`，另有产品总览聚合 |
| 指标 | 折后消耗 `SUM(cost_zhe / NULLIF(currency,0))`、注册 `SUM(registers)`、CPI、实际 ROI1/ROI7 |
| 回收源 | `shucang_market.tj_ad_sdk_revenue_view`，MI ROI360 默认 SDK 回收口径 |
| 依赖表 | `shucang_market.tj_ad_spend_active_v2_view`、`shucang_market.tj_ad_sdk_revenue_view` |
| 与语义层关系 | 沿用 `ai_ck/agent_knowledge/tables/tj_ad_spend_active_v2.yaml`、`ai_ck/agent_knowledge/tables/tj_ad_sdk_revenue.yaml` 和 `verified_sql/vsql_20260616_mi_roi360_campaign_board_recon.md` 的 ROI_N 实际段口径 |

适用包体：

| 产品 | bundle_id | 备注 |
|---|---|---|
| Double Tile GP | `com.HS.mahjong` | 0615 周报连续破红线对象 |
| Sudoku Master GP | `com.mathbrain.sudoku` | 0615 周报新增 GP ROI 风险 |
| Solitaire Master iOS | `solitaire.HS.freecard` | 0615 周报 iOS 破红线对象 |
| Word Solitaire Go iOS | `com.nebula.wordsolitaire.ios` | 0615 周报降量后仍破红线对象 |
| Arrows Blast GP | `com.nebula.arrows` | 0615 周报投放重启对象 |

## SQL

```sql
-- ClickHouse / CK.
-- 参数示例:
-- baseline_start = '2026-05-29'
-- baseline_end   = '2026-06-04'
-- current_start  = '2026-06-05'
-- current_end    = '2026-06-11'
-- ROI7 需要 revenue 覆盖到 current_end + 6，本次验证 CK revenue 最新 active_date/revenue 覆盖满足。
WITH
spend AS (
  SELECT
    if(active_date BETWEEN '${current_start}' AND '${current_end}',
       'current',
       'baseline') AS period,
    multiIf(
      bundle_id = 'com.HS.mahjong', 'Double Tile GP',
      bundle_id = 'com.mathbrain.sudoku', 'Sudoku Master GP',
      bundle_id = 'solitaire.HS.freecard', 'Solitaire Master iOS',
      bundle_id = 'com.nebula.wordsolitaire.ios', 'Word Solitaire Go iOS',
      bundle_id = 'com.nebula.arrows', 'Arrows Blast GP',
      bundle_id
    ) AS product,
    bundle_id,
    any(pag_name) AS pag_name,
    media_source,
    sum(cost_zhe / nullIf(currency, 0)) AS cost_zhe_usd,
    sum(cost / nullIf(currency, 0)) AS cost_usd,
    sum(registers) AS registers
  FROM shucang_market.tj_ad_spend_active_v2_view
  WHERE active_date BETWEEN '${baseline_start}' AND '${current_end}'
    AND bundle_id IN (
      'com.HS.mahjong',
      'com.mathbrain.sudoku',
      'solitaire.HS.freecard',
      'com.nebula.wordsolitaire.ios',
      'com.nebula.arrows'
    )
  GROUP BY period, product, bundle_id, media_source
),
rev AS (
  SELECT
    if(active_date BETWEEN '${current_start}' AND '${current_end}',
       'current',
       'baseline') AS period,
    bundle_id,
    media_source,
    sumIf(revenue, date_diff <= 0) AS rev_d0,
    sumIf(revenue, date_diff <= 6) AS rev_d6
  FROM shucang_market.tj_ad_sdk_revenue_view
  WHERE active_date BETWEEN '${baseline_start}' AND '${current_end}'
    AND bundle_id IN (
      'com.HS.mahjong',
      'com.mathbrain.sudoku',
      'solitaire.HS.freecard',
      'com.nebula.wordsolitaire.ios',
      'com.nebula.arrows'
    )
  GROUP BY period, bundle_id, media_source
),
totals AS (
  SELECT
    period,
    bundle_id,
    sum(cost_zhe_usd) AS bundle_cost_zhe_usd
  FROM spend
  GROUP BY period, bundle_id
)
SELECT
  s.period,
  s.product,
  s.pag_name,
  s.bundle_id,
  s.media_source,
  round(s.cost_zhe_usd, 2) AS cost_zhe_usd,
  round(s.cost_usd, 2) AS cost_usd,
  round(100 * s.cost_zhe_usd / nullIf(t.bundle_cost_zhe_usd, 0), 1) AS cost_share_pct,
  s.registers,
  round(s.cost_zhe_usd / nullIf(s.registers, 0), 3) AS cpi,
  round(100 * r.rev_d0 / nullIf(s.cost_zhe_usd, 0), 1) AS roi1_pct,
  round(100 * r.rev_d6 / nullIf(s.cost_zhe_usd, 0), 1) AS roi7_pct
FROM spend s
LEFT JOIN rev r
  ON s.period = r.period
 AND s.bundle_id = r.bundle_id
 AND s.media_source = r.media_source
LEFT JOIN totals t
  ON s.period = t.period
 AND s.bundle_id = t.bundle_id
WHERE s.cost_zhe_usd > 100 OR s.registers > 100
ORDER BY s.product, s.period, cost_zhe_usd DESC;
```

产品总览可复用同一口径，将 `spend` 和 `rev` 聚合到 `period × product × bundle_id` 后输出。

## 预期输出

输出每个产品在 baseline/current 两个窗口内的媒体级消耗、消耗占比、注册、CPI、实际 ROI1 和实际 ROI7。用于回答：

- 消耗变化来自哪个媒体；
- 降量后短期实际回收是否改善；
- 周报 ROI360 预测段是否需要取 MI 蓝底预测或应用层等价口径验证；
- 媒体叙事是否与 CK spend/revenue 当前快照一致。

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-18 | AI | verified | CK `SELECT 1` 成功；`tj_ad_spend_active_v2`、`tj_ad_revenue_v2` 最新 `active_date=2026-06-17`；已刷新 `ai_ck/engineering_artifacts/freshness_snapshot.json`。本 SQL 在 `2026-05-29`~`2026-06-11` 窗口真实执行通过。 |

验证摘要：

| 产品 | current vs baseline 结果摘要 |
|---|---|
| Double Tile GP | 折后消耗 `$292,580` -> `$185,179`，注册 `207,768` -> `146,861`，实际 ROI7 `26.0%` -> `26.4%`；Applovin 折后消耗占比 `49.5%` -> `40.8%`，实际 ROI7 `20.9%` -> `22.7%`。 |
| Sudoku Master GP | 折后消耗 `$59,941` -> `$62,718`，注册 `52,879` -> `67,365`，实际 ROI7 `29.0%` -> `26.4%`；Facebook Ads 消耗占比 `23.4%` -> `43.8%`，实际 ROI7 `28.9%` -> `23.7%`。 |
| Solitaire Master iOS | 折后消耗 `$60,253` -> `$48,685`，注册 `28,440` -> `23,309`，实际 ROI7 `50.8%` -> `51.8%`；Liftoff 和 Applovin 实际 ROI7 均约 `48%`。 |
| Word Solitaire Go iOS | 折后消耗 `$30,280` -> `$8,712`，注册 `7,317` -> `1,391`，实际 ROI7 `15.0%` -> `26.6%`；降量后短期回收改善但样本显著变小。 |
| Arrows Blast GP | 折后消耗 `$957` -> `$45,236`，注册 `4,777` -> `26,815`，实际 ROI7 `13.1%` -> `23.4%`；投放重启成立，但仍应按冷启动观察。 |

## 风险与陷阱

- 本 SQL 只验证实际 ROI1/ROI7，不复现 ROI360 预测段。周报里的 ROI360、媒体 ROI 69%/86%/93% 等数字不能用本 SQL 直接对账。
- CK spend/revenue 视图是当前快照；与历史 MI 截图或周报截图比较时，回填和预测会造成差异。
- `media_source` 需要保留原值；`Facebook Ads`、`Social_facebook` 等不可擅自合并。
- Sudoku Master GP 本轮 CK spend 显示 Facebook Ads 消耗占比上升，不支持“Facebook 已缩量”这一叙事；需用 MI 同窗口 campaign/媒体明细或投放平台 change log 继续确认。
- 输出为聚合结果，不含用户级明细；不要扩展到设备 ID、IP、user_agent 等字段。
