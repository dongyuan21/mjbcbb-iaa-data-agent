# Verified SQL: 首日 ARPU 异动归因小窗口验证

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260613_day0_arpu_anomaly_attribution` |
| 状态 | verified |
| 来源 | `../raw/2026-06-11_BB首日ARPU预装归因HTML材料.md` |
| 关联 SOP | `../analysis_sop/20260611_首日ARPU异动归因SOP.md` |
| 适用场景 | 首日 ARPU 异动、预装渠道 ARPU 下跌、广告格式拆解、media_source 贡献拆解 |
| 最后验证 | 2026-06-18 |

## 原始问题

> BB Android 预装渠道新增用户首日 ARPU 在 2026-05-24 ~ 2026-05-30 为什么下降？是用户行为、展示次数、eCPM 单价，还是媒体结构变化导致？

## 验证范围

| 类型 | 内容 |
|---|---|
| 产品 | BB Android |
| bundle_id | `com.kcolb.juggle` |
| app_name | `kcolb_tsalb_gp` |
| baseline_window | 2026-05-17 ~ 2026-05-23 |
| anomaly_window | 2026-05-24 ~ 2026-05-30 |
| 业务范围 | 预装 media_source |
| 激活表 | `h-s.dwd_market_appsflyer_activation_push_data_di` |
| 行为聚合表 | `h-s.dws_kcolb_tsalb_all_user_multi_dim_hi` |

## 口径说明

| 类型 | 内容 |
|---|---|
| cohort | 激活表中 `install_time` 截取日期为安装日。 |
| Day0 行为 | 行为表 `dt = install_date`，并按 `distinct_id + bundle_id` join。 |
| ARPU | `SUM(ad_revenue) / COUNT(DISTINCT activated_user)`。 |
| 格式拆解 | 激励：`rewarded_ad_revenue / rewarded_ad_pv * 1000`；插屏：`inter_ad_revenue / inter_ad_pv * 1000`。 |
| 用户行为 | `game_cnt`、`real_time / 60`。 |
| PII 规则 | 不输出 `distinct_id` 明细，只输出聚合。 |

## 复用参数

复用本 SQL 时，不直接复制历史日期。必须先确定以下参数，并把窗口写进最终输出：

| 参数 | 说明 |
|---|---|
| `${bundle_id}` | 激活表包名，如 `com.kcolb.juggle`。 |
| `${app_name}` | 行为聚合表产品桶，如 `kcolb_tsalb_gp`。 |
| `${baseline_start}` / `${baseline_end}` | baseline 的 install / activation 业务日期窗口。 |
| `${anomaly_start}` / `${anomaly_end}` | anomaly 的 install / activation 业务日期窗口。 |
| `${activation_dt_scan_start}` | 通常取 baseline/anomaly 中最早业务日期。 |
| `${activation_dt_scan_end}` | 当前窗口必须取激活表 `latest_partition`，或至少覆盖 anomaly 结束日 T+1。 |
| `${behavior_dt_start}` / `${behavior_dt_end}` | Day0 行为表窗口，通常等于 install 业务日期窗口。 |

输出必须同时写明：

```text
install_time_window:
activation_dt_scan_window:
behavior_dt_window:
activation_target_latest_dt:
activation_dt_scan_end_rule:
current_window_conclusion_allowed:
```

如果 `${activation_dt_scan_end}` 未覆盖 `${anomaly_end}` 的 T+1，结果只能标为 `partial_partition_scan`，不能给当前窗口强 ARPU 下滑结论。规则见 `../analysis_sop/20260618_DNU安装时间与分区迟到护栏SOP.md`。

## SQL 1：预装 cohort smoke

```sql
WITH params AS (
  SELECT
    '${bundle_id}' AS bundle_id,
    '${app_name}' AS app_name,
    '${baseline_start}' AS baseline_start,
    '${baseline_end}' AS baseline_end,
    '${anomaly_start}' AS anomaly_start,
    '${anomaly_end}' AS anomaly_end,
    '${activation_dt_scan_start}' AS activation_dt_scan_start,
    '${activation_dt_scan_end}' AS activation_dt_scan_end,
    '${behavior_dt_start}' AS behavior_dt_start,
    '${behavior_dt_end}' AS behavior_dt_end
)
SELECT
  CASE
    WHEN SUBSTR(CAST(t.install_time AS STRING), 1, 10)
      BETWEEN p.baseline_start AND p.baseline_end THEN 'baseline'
    WHEN SUBSTR(CAST(t.install_time AS STRING), 1, 10)
      BETWEEN p.anomaly_start AND p.anomaly_end THEN 'anomaly'
    ELSE 'other'
  END AS period,
  COUNT(DISTINCT t.distinct_id) AS users,
  COUNT(DISTINCT t.media_source) AS media_sources,
  COUNT(DISTINCT t.country) AS countries
FROM h-s.dwd_market_appsflyer_activation_push_data_di t
INNER JOIN params p
  ON t.bundle_id = p.bundle_id
WHERE t.dt BETWEEN p.activation_dt_scan_start AND p.activation_dt_scan_end
  AND SUBSTR(CAST(t.install_time AS STRING), 1, 10)
    BETWEEN p.baseline_start AND p.anomaly_end
  AND NVL(t.media_source, '') IN (
    'aura_int','coolpadzhf_int','digitalturbine_int','lenovotabpai4p_int',
    'nubia8rk_int','xiaomipai_int','xiaomipreload_int','shalltry_int',
    'vivopreload_int','xiaomiglobal_int','onedigitalturbine_int','oppo_int',
    'oppoglobal_int','oppopaipreinstall_int','transsionpreinstall_int',
    'ztepai_int','ztesw_int','huaweiadsglobal_int','honordevicm_int',
    'hihonor_int','TCL','tctmobilewp_int','vivoglobal_int','vivootapreload_int'
  )
GROUP BY
  CASE
    WHEN SUBSTR(CAST(t.install_time AS STRING), 1, 10)
      BETWEEN p.baseline_start AND p.baseline_end THEN 'baseline'
    WHEN SUBSTR(CAST(t.install_time AS STRING), 1, 10)
      BETWEEN p.anomaly_start AND p.anomaly_end THEN 'anomaly'
    ELSE 'other'
  END;
```

## SQL 2：首日 ARPU 与广告格式拆解

```sql
WITH params AS (
  SELECT
    '${bundle_id}' AS bundle_id,
    '${app_name}' AS app_name,
    '${baseline_start}' AS baseline_start,
    '${baseline_end}' AS baseline_end,
    '${anomaly_start}' AS anomaly_start,
    '${anomaly_end}' AS anomaly_end,
    '${activation_dt_scan_start}' AS activation_dt_scan_start,
    '${activation_dt_scan_end}' AS activation_dt_scan_end,
    '${behavior_dt_start}' AS behavior_dt_start,
    '${behavior_dt_end}' AS behavior_dt_end
),
activation AS (
  SELECT DISTINCT
    t.distinct_id,
    t.bundle_id,
    t.media_source,
    t.country,
    SUBSTR(CAST(t.install_time AS STRING), 1, 10) AS install_date,
    CASE
      WHEN SUBSTR(CAST(t.install_time AS STRING), 1, 10)
        BETWEEN p.baseline_start AND p.baseline_end THEN 'baseline'
      WHEN SUBSTR(CAST(t.install_time AS STRING), 1, 10)
        BETWEEN p.anomaly_start AND p.anomaly_end THEN 'anomaly'
    END AS period
  FROM h-s.dwd_market_appsflyer_activation_push_data_di t
  INNER JOIN params p
    ON t.bundle_id = p.bundle_id
  WHERE t.dt BETWEEN p.activation_dt_scan_start AND p.activation_dt_scan_end
    AND SUBSTR(CAST(t.install_time AS STRING), 1, 10)
      BETWEEN p.baseline_start AND p.anomaly_end
    AND NVL(t.media_source, '') IN (
      'aura_int','coolpadzhf_int','digitalturbine_int','lenovotabpai4p_int',
      'nubia8rk_int','xiaomipai_int','xiaomipreload_int','shalltry_int',
      'vivopreload_int','xiaomiglobal_int','onedigitalturbine_int','oppo_int',
      'oppoglobal_int','oppopaipreinstall_int','transsionpreinstall_int',
      'ztepai_int','ztesw_int','huaweiadsglobal_int','honordevicm_int',
      'hihonor_int','TCL','tctmobilewp_int','vivoglobal_int','vivootapreload_int'
    )
),
behavior AS (
  SELECT
    t.dt,
    t.distinct_id,
    t.bundle_id,
    t.ad_revenue,
    t.ad_pv,
    t.inter_ad_revenue,
    t.inter_ad_pv,
    t.rewarded_ad_revenue,
    t.rewarded_ad_pv,
    t.game_cnt,
    t.real_time
  FROM h-s.dws_kcolb_tsalb_all_user_multi_dim_hi t
  INNER JOIN params p
    ON t.app_name = p.app_name
  WHERE t.dt BETWEEN p.behavior_dt_start AND p.behavior_dt_end
)
SELECT
  a.period,
  COUNT(DISTINCT a.distinct_id) AS users,
  COUNT(DISTINCT b.distinct_id) AS matched_users,
  SUM(NVL(b.ad_revenue, 0)) / COUNT(DISTINCT a.distinct_id) AS arpu,
  SUM(NVL(b.rewarded_ad_revenue, 0)) / COUNT(DISTINCT a.distinct_id) AS rewarded_arpu,
  SUM(NVL(b.rewarded_ad_pv, 0)) / COUNT(DISTINCT a.distinct_id) AS rewarded_pv_per_user,
  CASE
    WHEN SUM(NVL(b.rewarded_ad_pv, 0)) > 0
    THEN SUM(NVL(b.rewarded_ad_revenue, 0)) / SUM(NVL(b.rewarded_ad_pv, 0)) * 1000
  END AS rewarded_ecpm,
  SUM(NVL(b.inter_ad_revenue, 0)) / COUNT(DISTINCT a.distinct_id) AS inter_arpu,
  SUM(NVL(b.inter_ad_pv, 0)) / COUNT(DISTINCT a.distinct_id) AS inter_pv_per_user,
  CASE
    WHEN SUM(NVL(b.inter_ad_pv, 0)) > 0
    THEN SUM(NVL(b.inter_ad_revenue, 0)) / SUM(NVL(b.inter_ad_pv, 0)) * 1000
  END AS inter_ecpm,
  SUM(NVL(b.game_cnt, 0)) / COUNT(DISTINCT a.distinct_id) AS game_cnt_per_user,
  SUM(NVL(b.real_time, 0)) / COUNT(DISTINCT a.distinct_id) / 60 AS real_minutes_per_user
FROM activation a
LEFT JOIN behavior b
  ON a.distinct_id = b.distinct_id
 AND a.bundle_id = b.bundle_id
 AND a.install_date = b.dt
WHERE a.period IS NOT NULL
GROUP BY a.period
ORDER BY a.period;
```

## SQL 3：预装 media_source 贡献拆解

```sql
WITH params AS (
  SELECT
    '${bundle_id}' AS bundle_id,
    '${app_name}' AS app_name,
    '${baseline_start}' AS baseline_start,
    '${baseline_end}' AS baseline_end,
    '${anomaly_start}' AS anomaly_start,
    '${anomaly_end}' AS anomaly_end,
    '${activation_dt_scan_start}' AS activation_dt_scan_start,
    '${activation_dt_scan_end}' AS activation_dt_scan_end,
    '${behavior_dt_start}' AS behavior_dt_start,
    '${behavior_dt_end}' AS behavior_dt_end
),
activation AS (
  SELECT DISTINCT
    t.distinct_id,
    t.bundle_id,
    t.media_source,
    SUBSTR(CAST(t.install_time AS STRING), 1, 10) AS install_date,
    CASE
      WHEN SUBSTR(CAST(t.install_time AS STRING), 1, 10)
        BETWEEN p.baseline_start AND p.baseline_end THEN 'baseline'
      WHEN SUBSTR(CAST(t.install_time AS STRING), 1, 10)
        BETWEEN p.anomaly_start AND p.anomaly_end THEN 'anomaly'
    END AS period
  FROM h-s.dwd_market_appsflyer_activation_push_data_di t
  INNER JOIN params p
    ON t.bundle_id = p.bundle_id
  WHERE t.dt BETWEEN p.activation_dt_scan_start AND p.activation_dt_scan_end
    AND SUBSTR(CAST(t.install_time AS STRING), 1, 10)
      BETWEEN p.baseline_start AND p.anomaly_end
    AND NVL(t.media_source, '') IN (
      'aura_int','coolpadzhf_int','digitalturbine_int','lenovotabpai4p_int',
      'nubia8rk_int','xiaomipai_int','xiaomipreload_int','shalltry_int',
      'vivopreload_int','xiaomiglobal_int','onedigitalturbine_int','oppo_int',
      'oppoglobal_int','oppopaipreinstall_int','transsionpreinstall_int',
      'ztepai_int','ztesw_int','huaweiadsglobal_int','honordevicm_int',
      'hihonor_int','TCL','tctmobilewp_int','vivoglobal_int','vivootapreload_int'
    )
),
behavior AS (
  SELECT
    t.dt,
    t.distinct_id,
    t.bundle_id,
    t.ad_revenue,
    t.rewarded_ad_revenue,
    t.rewarded_ad_pv,
    t.game_cnt,
    t.real_time
  FROM h-s.dws_kcolb_tsalb_all_user_multi_dim_hi t
  INNER JOIN params p
    ON t.app_name = p.app_name
  WHERE t.dt BETWEEN p.behavior_dt_start AND p.behavior_dt_end
)
SELECT
  a.period,
  a.media_source,
  COUNT(DISTINCT a.distinct_id) AS users,
  SUM(NVL(b.ad_revenue, 0)) / COUNT(DISTINCT a.distinct_id) AS arpu,
  CASE
    WHEN SUM(NVL(b.rewarded_ad_pv, 0)) > 0
    THEN SUM(NVL(b.rewarded_ad_revenue, 0)) / SUM(NVL(b.rewarded_ad_pv, 0)) * 1000
  END AS rewarded_ecpm
FROM activation a
LEFT JOIN behavior b
  ON a.distinct_id = b.distinct_id
 AND a.bundle_id = b.bundle_id
 AND a.install_date = b.dt
WHERE a.period IS NOT NULL
GROUP BY a.period, a.media_source
HAVING users >= 10000
ORDER BY a.period, users DESC
LIMIT 60;
```

## 预期输出

- SQL 1：baseline / anomaly 的预装新增用户规模、媒体数和国家数。
- SQL 2：整体 Day0 ARPU、rewarded/interstitial ARPU、展示次数、人均行为和 eCPM。
- SQL 3：按预装 `media_source` 拆用户数、ARPU、rewarded eCPM。

## 风险与陷阱

- 本 SQL 复核的是报告核心传导公式 `ARPU = 人均展示次数 * eCPM / 1000`，不是原 DA HTML 报告的完整 SQL 复刻。
- 当前 DWS 链路能做广告格式拆解，但不能复刻原报告的 `ad_source × ad_format` 明细；BB GP 原始事件表需要更明确事件名或 DA 原 SQL 后再补。
- 产品桶 `layertype1217` 和商业化桶 `layertype_business` 的字段来源尚未确认，本 SQL 不包含桶维度。
- `real_time` 单位在 DWS 表注释中为游戏时长，当前按秒除以 60 转分钟；如业务报告使用另一个时长字段，需要再校准。
- 当前窗口必须先 probe 激活表 `max(dt)`，并让 `${activation_dt_scan_end}` 扫到 `latest_partition` 或至少 anomaly 结束日 T+1；否则输出 `partial_partition_scan`。
- Day0 行为表窗口仍按业务安装日取 `behavior_dt_window`，不要因为激活表 T+1 扫描而把 Day0 行为表扩成 T+1 指标。
- 不输出用户级明细。

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-13 | AI | verified | 3 条 SQL 均用 MaxCompute 执行成功；结果为聚合输出，未保存用户级明细。 |
| 2026-06-16 | AI | verified(日级复现) | 按 install_date 日级 cohort 复现 14 天，与报告 echarts 日级值逐日对账：激励 ARPU 高度一致(中位差 0.0001)、趋势 100% 一致；eCPM 系统偏低 ~9%，根因为 dws.rewarded_ad_pv 比报告 ad_source×ad_format 明细 pv 大 ~9.6%(激励 ARPU=pv×eCPM/1000 守恒)，整体 ARPU 偏低集中在非激励收入口径。详见 `../../raw_exports/bb_arpu验证/recon_report.md`。 |
| 2026-06-18 | Codex | verified_template_rerun | 参数化模板 3 段 SQL 均用 MaxCompute 实跑成功；`install_time_window=2026-05-17 ~ 2026-05-30`，`activation_dt_scan_window=2026-05-17 ~ 2026-05-31`，`behavior_dt_window=2026-05-17 ~ 2026-05-30`。 |

### 2026-06-13 验证摘要

| SQL | 结果 | 聚合摘要 |
|---|---|---|
| SQL 1 | pass | baseline 约 695.6 万预装新增用户，anomaly 约 678.4 万。 |
| SQL 2 | pass | ARPU 从约 0.01954 降至 0.01763；rewarded eCPM 从约 35.83 降至 32.37；方向与 DA 报告一致。 |
| SQL 3 | pass | 可按预装 `media_source` 输出 ARPU 与 rewarded eCPM；`digitalturbine_int`、`aura_int` 等主量级媒体可被拆解。 |

### 2026-06-18 模板复跑摘要

本次复跑把激活表 `dt` 扫到 anomaly 结束日 T+1，因此 anomaly cohort 与 2026-06-13 旧摘要略有差异；以新模板复用时，应优先使用 `activation_dt_scan_window` 口径。

| SQL | 结果 | 聚合摘要 |
|---|---|---|
| SQL 1 | pass | baseline 6,956,463 预装新增用户，anomaly 7,036,339；激活表 latest dt 为 2026-06-18，本模板验证扫到 2026-05-31。 |
| SQL 2 | pass | ARPU 从 0.01954 降至 0.01818；rewarded eCPM 从 35.83 降至 32.91；行为次数基本持平，方向仍指向 eCPM / 广告价值下降。 |
| SQL 3 | pass | `digitalturbine_int`、`aura_int`、`xiaomipreload_int` 等主量级预装媒体可按 ARPU 与 rewarded eCPM 拆解；输出为聚合结果。 |
