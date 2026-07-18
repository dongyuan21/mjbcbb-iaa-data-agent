# Verified SQL: BB 美国 UA DNU 下滑 media_source 贡献拆解

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260613_bb_us_ua_media_source_dnu_delta` |
| 状态 | verified |
| 来源 | 原 `TODO/周报问题积压清单.md`（已归档，现由 `eval/真实问题验收集/` 接替） |
| 适用场景 | BB 美国 UA DNU 下滑归因、media_source 贡献拆解、周报复盘 |
| 最后验证 | 2026-06-18 |

## 原始问题

> BB 美国 DNU 下滑是否主要由 UA 管控导致？Google / Applovin / Unity Ads 等媒体分别贡献多少缺口？

## 口径说明

| 类型 | 内容 |
|---|---|
| 产品 | BB GP |
| bundle_id | `com.kcolb.juggle` |
| 国家 | US |
| baseline_window | 2026-05-17 ~ 2026-05-23 |
| anomaly_window | 2026-05-24 ~ 2026-05-30 |
| 数据源 | `h-s.dwd_market_appsflyer_activation_push_data_di` |
| 口径 | AF activation / install，排除预装媒体与 organic，只看 UA media_source |

## 复用参数

复用本 SQL 时，不直接复制历史日期。Agent / 分析人必须先确定以下参数，并把它们写进输出：

| 参数 | 说明 |
|---|---|
| `${bundle_id}` | 产品包名，如 `com.kcolb.juggle`。 |
| `${country}` | 国家二字码，如 `US`。 |
| `${baseline_start}` / `${baseline_end}` | baseline 的 install / activation 业务日期窗口。 |
| `${anomaly_start}` / `${anomaly_end}` | anomaly 的 install / activation 业务日期窗口。 |
| `${dt_scan_start}` | 通常取 baseline/anomaly 中最早业务日期。 |
| `${dt_scan_end}` | 当前窗口必须取目标表 `latest_partition`，或至少覆盖 anomaly 结束日 T+1；历史成熟窗口也必须记录为何只扫到该分区。 |
| `${media_source_filter}` | 可选；不传时输出全 UA media_source。 |

输出必须同时写明：

```text
install_time_window:
dt_scan_window:
target_table_latest_dt:
dt_scan_end_rule:
current_window_conclusion_allowed:
```

如果 `${dt_scan_end}` 未覆盖 `${anomaly_end}` 的 T+1，结果只能标为 `partial_partition_scan`，不能给当前窗口强下滑结论。规则见 `../analysis_sop/20260618_DNU安装时间与分区迟到护栏SOP.md`。

## SQL

```sql
WITH params AS (
  SELECT
    '${bundle_id}' AS bundle_id,
    UPPER('${country}') AS country_code,
    '${baseline_start}' AS baseline_start,
    '${baseline_end}' AS baseline_end,
    '${anomaly_start}' AS anomaly_start,
    '${anomaly_end}' AS anomaly_end,
    '${dt_scan_start}' AS dt_scan_start,
    '${dt_scan_end}' AS dt_scan_end,
    DATEDIFF(
      TO_DATE('${baseline_end}', 'yyyy-MM-dd'),
      TO_DATE('${baseline_start}', 'yyyy-MM-dd'),
      'dd'
    ) + 1 AS baseline_days,
    DATEDIFF(
      TO_DATE('${anomaly_end}', 'yyyy-MM-dd'),
      TO_DATE('${anomaly_start}', 'yyyy-MM-dd'),
      'dd'
    ) + 1 AS anomaly_days
),
activation AS (
  SELECT
    CASE
      WHEN SUBSTR(CAST(t.install_time AS STRING), 1, 10)
        BETWEEN p.baseline_start AND p.baseline_end THEN 'baseline'
      WHEN SUBSTR(CAST(t.install_time AS STRING), 1, 10)
        BETWEEN p.anomaly_start AND p.anomaly_end THEN 'anomaly'
    END AS period,
    SUBSTR(CAST(t.install_time AS STRING), 1, 10) AS install_date,
    t.media_source,
    t.distinct_id,
    p.baseline_days,
    p.anomaly_days
  FROM h-s.dwd_market_appsflyer_activation_push_data_di t
  INNER JOIN params p
    ON t.bundle_id = p.bundle_id
  WHERE t.dt BETWEEN p.dt_scan_start AND p.dt_scan_end
    AND SUBSTR(CAST(t.install_time AS STRING), 1, 10)
      BETWEEN p.baseline_start AND p.anomaly_end
    AND UPPER(t.country) = p.country_code
    AND NVL(t.media_source, '') NOT IN (
      'aura_int','coolpadzhf_int','digitalturbine_int','lenovotabpai4p_int',
      'nubia8rk_int','xiaomipai_int','xiaomipreload_int','shalltry_int',
      'vivopreload_int','xiaomiglobal_int','onedigitalturbine_int','oppo_int',
      'oppoglobal_int','oppopaipreinstall_int','transsionpreinstall_int',
      'ztepai_int','ztesw_int','huaweiadsglobal_int','honordevicm_int',
      'hihonor_int','TCL','tctmobilewp_int','vivoglobal_int','vivootapreload_int'
    )
    AND NVL(t.media_source, '') <> 'organic'
    -- 可选媒体过滤，示例：
    -- AND t.media_source IN (${media_source_filter})
),
daily_dnu AS (
  SELECT
    period,
    install_date,
    media_source,
    COUNT(DISTINCT distinct_id) AS dnu,
    MAX(baseline_days) AS baseline_days,
    MAX(anomaly_days) AS anomaly_days
  FROM activation a
  WHERE period IS NOT NULL
  GROUP BY
    period,
    install_date,
    media_source
),
pivoted AS (
  SELECT
    media_source,
    SUM(CASE WHEN period = 'baseline' THEN dnu ELSE 0 END) AS baseline_dnu,
    SUM(CASE WHEN period = 'anomaly' THEN dnu ELSE 0 END) AS anomaly_dnu,
    MAX(baseline_days) AS baseline_days,
    MAX(anomaly_days) AS anomaly_days
  FROM daily_dnu d
  GROUP BY
    media_source
),
with_delta AS (
  SELECT
    media_source,
    baseline_dnu,
    anomaly_dnu,
    baseline_days,
    anomaly_days,
    baseline_dnu * 1.0 / baseline_days AS baseline_avg_dnu,
    anomaly_dnu * 1.0 / anomaly_days AS anomaly_avg_dnu,
    anomaly_dnu * 1.0 / anomaly_days - baseline_dnu * 1.0 / baseline_days AS dnu_delta,
    SUM(anomaly_dnu * 1.0 / anomaly_days - baseline_dnu * 1.0 / baseline_days) OVER () AS total_delta
  FROM pivoted
)
SELECT
  media_source,
  baseline_dnu,
  anomaly_dnu,
  baseline_days,
  anomaly_days,
  baseline_avg_dnu,
  anomaly_avg_dnu,
  dnu_delta,
  CASE WHEN baseline_avg_dnu > 0 THEN dnu_delta / baseline_avg_dnu END AS dnu_delta_rate,
  CASE WHEN total_delta <> 0 THEN dnu_delta / total_delta END AS delta_contribution
FROM with_delta
WHERE baseline_dnu + anomaly_dnu > 0
ORDER BY dnu_delta ASC
LIMIT 50;
```

## 预期输出

按 `media_source` 输出：

- baseline DNU
- anomaly DNU
- baseline / anomaly 天数
- baseline / anomaly 日均 DNU
- DNU delta
- DNU delta rate
- 对总缺口的贡献占比

## 风险与陷阱

- 这是 UA 归因拆解，不包含预装和 organic。
- 预装媒体名单需要随业务维护，新增厂商必须同步到排除列表。
- 该 SQL 使用 AF activation 表，不等于媒体后台 install。
- 当前窗口必须先 probe 目标表 `max(dt)`，并让 `${dt_scan_end}` 扫到 `latest_partition` 或至少 anomaly 结束日 T+1；否则输出 `partial_partition_scan`。
- 历史验证窗口可不扫到今天的 latest partition，但必须说明该窗口已成熟，且 `dt_scan_window` 覆盖 late-arrival 风险。
- campaign / adset / ad 下钻必须沿用同一组 `install_time_window` 与 `dt_scan_window`，只替换聚合维度，不重新缩短 `dt`。
- 不输出 `distinct_id` 明细。

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-13 | AI | verified | MaxCompute 小窗口执行成功，输出 media_source 聚合。 |
| 2026-06-18 | Codex | verified_template_rerun | 参数化模板用 POC-01 当前窗口实跑成功：`install_time_window=2026-06-10 ~ 2026-06-17`，`dt_scan_window=2026-06-10 ~ 2026-06-18`，输出结构和核心结果与 POC 修正版一致。 |

### 2026-06-13 验证摘要

| media_source | baseline_dnu | anomaly_dnu | delta | contribution |
|---|---:|---:|---:|---:|
| `googleadwords_int` | 144792 | 94719 | -50073 | 约 68.7% |
| `applovin_int` | 45682 | 27266 | -18416 | 约 25.3% |
| `unityads_int` | 7844 | 5722 | -2122 | 约 2.9% |
| `moloco_int` | 14706 | 13331 | -1375 | 约 1.9% |
| `Facebook Ads` | 2693 | 1346 | -1347 | 约 1.8% |

### 2026-06-18 POC 复用修正摘要

POC-01 用该类 SQL 分析 2026-06-17 当前窗口时，初版只扫 `dt` 到 2026-06-17，得到约 `-12169.57` 的 DNU 缺口；目标表当时 `latest dt=2026-06-18`，修正为 `dt_scan_window=2026-06-10 ~ 2026-06-18` 后，缺口修正为约 `-2378.57`。

因此，本 SQL 作为模板复用时，`install_time_window` 与 `dt_scan_window` 是输出契约的一部分，不是可省略的执行细节。

2026-06-18 模板实跑 Top 3：

| media_source | baseline_dnu | anomaly_dnu | baseline_avg_dnu | anomaly_avg_dnu | dnu_delta | contribution |
|---|---:|---:|---:|---:|---:|---:|
| `googleadwords_int` | 103371 | 13307 | 14767.29 | 13307.00 | -1460.29 | 61.4% |
| `tiktokglobal_int` | 5988 | 275 | 855.43 | 275.00 | -580.43 | 24.4% |
| `applovin_int` | 29315 | 3896 | 4187.86 | 3896.00 | -291.86 | 12.3% |
