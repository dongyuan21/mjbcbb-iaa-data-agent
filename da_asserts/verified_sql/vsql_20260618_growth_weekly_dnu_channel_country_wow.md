# 0615 周报 DNU / 渠道 / 国家 WoW 验证

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260618_growth_weekly_dnu_channel_country_wow` |
| 状态 | verified |
| 来源 | `../raw/2026-06-15_发行增长周会_docx.md`、`../decision_cases/20260615_发行增长周会ROI_DNU风险案例.md` |
| 适用场景 | 周报产品 DNU、渠道 DNU、kcolb tsalb 自然量国家下钻的 MaxCompute 设备口径复验 |
| 负责人 | Cursor Agent |
| 最后验证 | 2026-06-18 |

## 原始问题

> 0615 周报里 DNU 变化、Word Solitaire Go iOS 大幅降量、kcolb tsalb T3 自然量下滑，哪些能用 MaxCompute 设备口径直接复验？

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | `dt` 活跃日期；本次验证 baseline=`2026-05-29`~`2026-06-04`，current=`2026-06-05`~`2026-06-11` |
| 粒度 | 产品总览：`product × channel_category`；包体明细：`project × bundle_id × os_system`；BB 自然国家：`country` |
| DAU | `SUM(dau)` 后除以 `7.0` 得周均 |
| DNU | `SUM(CASE WHEN age_bucket='D0' THEN dau ELSE 0 END)` 后除以 `7.0` 得周均 |
| 依赖表 | `h-s.ads_market_device_dau_behavior_di` |
| 与语义层关系 | 沿用 `ai_hive/agent_knowledge/tables/ads_market_device_dau_behavior_di.yaml` 和 `verified_sql/vsql_20260617_device_dau_dnu_wow.md` 的设备口径 |

产品包体集合：

| 产品 | bundle_id |
|---|---|
| kcolb tsalb incl VN | `com.kcolb.juggle`、`com.kcolbpuzzle.us.ios`、`com.kcolbtsalb.vn`、`com.kcolbtsalb.vn.ios` |
| Double Tile | `com.HS.mahjong`、`com.HS.mahjong.ios` |
| Sudoku Master | `com.mathbrain.sudoku`、`com.mathbrain.sudoku.ios` |
| Solitaire Master | `solitaire.HS.freecard`、`solitaire.classic.HS.free.klondike.card.patience` |
| Word Solitaire Go | `com.nebula.wordsolitaire`、`com.nebula.wordsolitaire.ios` |
| Arrows Blast | `com.nebula.arrows` |

## SQL

### 产品与渠道周均 WoW

```sql
-- MaxCompute / ODPS.
-- 参数示例:
-- baseline_start = '2026-05-29'
-- baseline_end   = '2026-06-04'
-- current_start  = '2026-06-05'
-- current_end    = '2026-06-11'
WITH base AS (
  SELECT
    CASE
      WHEN dt BETWEEN '${baseline_start}' AND '${baseline_end}' THEN 'baseline'
      WHEN dt BETWEEN '${current_start}' AND '${current_end}' THEN 'current'
    END AS period,
    CASE
      WHEN bundle_id IN ('com.kcolb.juggle','com.kcolbpuzzle.us.ios','com.kcolbtsalb.vn','com.kcolbtsalb.vn.ios')
        THEN 'kcolb tsalb incl VN'
      WHEN bundle_id IN ('com.HS.mahjong','com.HS.mahjong.ios')
        THEN 'Double Tile'
      WHEN bundle_id IN ('com.mathbrain.sudoku','com.mathbrain.sudoku.ios')
        THEN 'Sudoku Master'
      WHEN bundle_id IN ('solitaire.HS.freecard','solitaire.classic.HS.free.klondike.card.patience')
        THEN 'Solitaire Master'
      WHEN bundle_id IN ('com.nebula.wordsolitaire','com.nebula.wordsolitaire.ios')
        THEN 'Word Solitaire Go'
      WHEN bundle_id = 'com.nebula.arrows'
        THEN 'Arrows Blast'
    END AS product,
    COALESCE(channel_category, 'NULL') AS channel_category,
    SUM(dau) AS dau,
    SUM(CASE WHEN age_bucket = 'D0' THEN dau ELSE 0 END) AS dnu
  FROM h-s.ads_market_device_dau_behavior_di
  WHERE dt BETWEEN '${baseline_start}' AND '${current_end}'
    AND bundle_id IN (
      'com.kcolb.juggle','com.kcolbpuzzle.us.ios','com.kcolbtsalb.vn','com.kcolbtsalb.vn.ios',
      'com.HS.mahjong','com.HS.mahjong.ios',
      'com.mathbrain.sudoku','com.mathbrain.sudoku.ios',
      'solitaire.HS.freecard','solitaire.classic.HS.free.klondike.card.patience',
      'com.nebula.wordsolitaire','com.nebula.wordsolitaire.ios',
      'com.nebula.arrows'
    )
  GROUP BY
    CASE
      WHEN dt BETWEEN '${baseline_start}' AND '${baseline_end}' THEN 'baseline'
      WHEN dt BETWEEN '${current_start}' AND '${current_end}' THEN 'current'
    END,
    CASE
      WHEN bundle_id IN ('com.kcolb.juggle','com.kcolbpuzzle.us.ios','com.kcolbtsalb.vn','com.kcolbtsalb.vn.ios')
        THEN 'kcolb tsalb incl VN'
      WHEN bundle_id IN ('com.HS.mahjong','com.HS.mahjong.ios')
        THEN 'Double Tile'
      WHEN bundle_id IN ('com.mathbrain.sudoku','com.mathbrain.sudoku.ios')
        THEN 'Sudoku Master'
      WHEN bundle_id IN ('solitaire.HS.freecard','solitaire.classic.HS.free.klondike.card.patience')
        THEN 'Solitaire Master'
      WHEN bundle_id IN ('com.nebula.wordsolitaire','com.nebula.wordsolitaire.ios')
        THEN 'Word Solitaire Go'
      WHEN bundle_id = 'com.nebula.arrows'
        THEN 'Arrows Blast'
    END,
    COALESCE(channel_category, 'NULL')
),
roll AS (
  SELECT period, product, 'ALL' AS channel_category, SUM(dau) AS dau, SUM(dnu) AS dnu
  FROM base
  WHERE period IS NOT NULL AND product IS NOT NULL
  GROUP BY period, product
  UNION ALL
  SELECT period, product, channel_category, dau, dnu
  FROM base
  WHERE period IS NOT NULL AND product IS NOT NULL
),
pivoted AS (
  SELECT
    product,
    channel_category,
    SUM(CASE WHEN period = 'baseline' THEN dau ELSE 0 END) / 7.0 AS baseline_avg_dau,
    SUM(CASE WHEN period = 'current' THEN dau ELSE 0 END) / 7.0 AS current_avg_dau,
    SUM(CASE WHEN period = 'baseline' THEN dnu ELSE 0 END) / 7.0 AS baseline_avg_dnu,
    SUM(CASE WHEN period = 'current' THEN dnu ELSE 0 END) / 7.0 AS current_avg_dnu
  FROM roll
  GROUP BY product, channel_category
)
SELECT
  product,
  channel_category,
  ROUND(baseline_avg_dau, 0) AS baseline_avg_dau,
  ROUND(current_avg_dau, 0) AS current_avg_dau,
  ROUND(current_avg_dau - baseline_avg_dau, 0) AS dau_delta,
  ROUND((current_avg_dau - baseline_avg_dau) / NULLIF(baseline_avg_dau, 0), 4) AS dau_wow_rate,
  ROUND(baseline_avg_dnu, 0) AS baseline_avg_dnu,
  ROUND(current_avg_dnu, 0) AS current_avg_dnu,
  ROUND(current_avg_dnu - baseline_avg_dnu, 0) AS dnu_delta,
  ROUND((current_avg_dnu - baseline_avg_dnu) / NULLIF(baseline_avg_dnu, 0), 4) AS dnu_wow_rate
FROM pivoted
WHERE current_avg_dau + baseline_avg_dau + current_avg_dnu + baseline_avg_dnu > 0
ORDER BY product, channel_category;
```

### BB 自然量国家下钻

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
    AND bundle_id IN ('com.kcolb.juggle','com.kcolbpuzzle.us.ios','com.kcolbtsalb.vn','com.kcolbtsalb.vn.ios')
    AND channel_category = '自然'
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
  ROUND(baseline_avg_dau, 0) AS baseline_avg_dau,
  ROUND(current_avg_dau, 0) AS current_avg_dau,
  ROUND(current_avg_dau - baseline_avg_dau, 0) AS dau_delta,
  ROUND((current_avg_dau - baseline_avg_dau) / NULLIF(baseline_avg_dau, 0), 4) AS dau_wow_rate,
  ROUND(baseline_avg_dnu, 0) AS baseline_avg_dnu,
  ROUND(current_avg_dnu, 0) AS current_avg_dnu,
  ROUND(current_avg_dnu - baseline_avg_dnu, 0) AS dnu_delta,
  ROUND((current_avg_dnu - baseline_avg_dnu) / NULLIF(baseline_avg_dnu, 0), 4) AS dnu_wow_rate
FROM pivoted
WHERE ABS(current_avg_dnu - baseline_avg_dnu) >= 1000
   OR ABS(current_avg_dau - baseline_avg_dau) >= 10000
ORDER BY dnu_delta ASC
LIMIT 40;
```

## 预期输出

第一段 SQL 输出产品和渠道的 DAU/DNU 周均、差值和 WoW；第二段 SQL 输出 BB 家族自然量按国家的 DAU/DNU 周均、差值和 WoW。输出是设备聚合口径，不包含用户或设备明细。

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-18 | AI | verified | MC `SELECT 1` 成功；`ads_market_device_dau_behavior_di` 最新 `dt=2026-06-17`；已刷新 `ai_hive/engineering_artifacts/freshness_snapshot.json`。本 SQL 在 `2026-05-29`~`2026-06-11` 窗口真实执行通过。 |

验证摘要：

| 对象 | current vs baseline 结果摘要 |
|---|---|
| kcolb tsalb incl VN | 设备口径 DNU 周均 `2,003,866` -> `1,960,517`，WoW `-2.2%`；其中自然 DNU `562,828` -> `522,078`，WoW `-7.2%`，与周报自然量下滑方向一致。 |
| BB 自然国家 | 自然 DNU 下滑最大的国家为 VN `-4,425`、ID `-3,259`、TR `-2,906`，支持周报“T3 自然量下滑集中在越南/印尼/土耳其”的方向判断。 |
| Double Tile | DNU 周均 `27,484` -> `18,387`，WoW `-33.1%`，方向与周报 `-28.6%` 一致。 |
| Sudoku Master | DNU 周均 `11,997` -> `14,993`，WoW `+25.0%`，方向与周报 `+20.4%` 一致；需要和 ROI 拆解同看。 |
| Solitaire Master | DNU 周均 `2,206` -> `1,656`，WoW `-25.0%`，方向与周报 `-19.4%` 一致。 |
| Word Solitaire Go | iOS 单包 `com.nebula.wordsolitaire.ios` DNU 周均 `1,044` -> `192`，WoW `-81.6%`，与周报 `-80.8%` 基本吻合；若 GP+iOS 合并则为增长，说明周报 DNU 行疑似 iOS 单包口径。 |
| Arrows Blast | DNU 周均 `736` -> `4,079`，WoW `+454.0%`，与周报投放重启、DNU 暴增方向一致。 |

## 风险与陷阱

- `ads_market_device_dau_behavior_di` 是设备行为聚合表，DNU 是 `age_bucket='D0'` 的设备口径，不等于 AF install / activation 分母。
- 本 SQL 更适合验证方向、周均趋势、渠道/国家贡献；绝对值可能和周报 BI 截图口径不完全一致。
- 周报中 Word Solitaire Go 的 DNU 行更接近 iOS 单包；回答时不要默认把 GP+iOS 合并。
- `channel_category='自然'` 是本表一级渠道取值，不能替换成 `media_source='organic'` 后混用。
- `unknown` 国家如果出现在输出中，应作为数据质量/映射项保留，不要静默过滤。
