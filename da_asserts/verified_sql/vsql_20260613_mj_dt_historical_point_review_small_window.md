# Verified SQL: MJ/DT 历史点位复盘小窗口模板

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260613_mj_dt_historical_point_review_small_window` |
| 状态 | verified |
| 来源 | `../analysis_sop/MJ_DT历史点位复盘SOP.md` |
| 原始文件 | `../raw/2026-06-13_MJ_DT历史点位复盘手工材料.md` |
| 适用场景 | MJ/DT 历史点位复盘、事件渗透率、事件触发用户 ARPU / 留存小窗口验证 |
| 分区护栏 | 复用时必须按 `../analysis_sop/20260618_DNU安装时间与分区迟到护栏SOP.md` 区分 `install_time_window` 与 `activation_dt_scan_window`；当前窗口必须扫到 `latest_partition`，历史验证至少纳入 T+1。 |
| 最后验证 | 2026-06-18 |

## 原始问题

> 如何在不直接跑全量历史点位复盘大 SQL 的前提下，验证 DT Android 的 cohort、AF 事件渗透率、事件触发用户 ARPU / 留存链路能否跑通。

## 验证范围

| 类型 | 内容 |
|---|---|
| 产品 | DT Android / kcolb Collection |
| bundle_id | `com.HS.mahjong` |
| 国家 | US |
| 安装日期窗口 | 2026-03-01 ~ 2026-03-03 |
| 激活表 `dt` 扫描窗口 | 2026-03-01 ~ 2026-03-04，历史小窗口纳入 T+1；当前窗口复用时改为扫到 `latest_partition` |
| 事件观察窗口 | 2026-03-01 ~ 2026-03-10 |
| 行为观察窗口 | 2026-03-01 ~ 2026-03-10 |
| AF 事件表 | `h-s.ods_appsflyer_block_collection_in_app_events_report_di` |
| 激活表 | `h-s.dwd_market_appsflyer_activation_push_data_di` |
| 行为表 | `h-s.dws_block_collection_all_user_multi_dim_hi` |

```yaml
install_time_window: "2026-03-01 ~ 2026-03-03"
dt_scan_window: "2026-03-01 ~ 2026-03-04"
event_dt_window: "2026-03-01 ~ 2026-03-10"
behavior_dt_window: "2026-03-01 ~ 2026-03-10"
current_window_conclusion: false
```

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | 激活按 `install_time` 截取日期；激活表 `dt` 只是分区扫描窗口，必须覆盖安装日期并向后扩到 T+1 / `latest_partition`；事件观察按 AF 事件表 `dt/hour`；行为按 `dt` 与 `install_datetime` 计算 `day_diff`。 |
| 维度 | `install_date`、`bundle_id`、`country`、`media_source`、`event_name`。 |
| 指标 | cohort 用户数、事件次数、事件用户数、渗透率、事件触发用户 D1/D7 ARPU、D1/D7 留存。 |
| 过滤 | US、`com.HS.mahjong`、短窗口；SQL 1 排除预装媒体。 |
| PII 规则 | 不输出 `distinct_id`、`customer_user_id`、`appsflyer_id` 明细，只输出聚合。 |

## 复用参数

下面 3 条 SQL 共用同一组参数。复用到新日期时，优先只改 `params` CTE，不改主体逻辑。

| 参数 | 默认值 | 说明 |
|---|---|---|
| `install_start` / `install_end` | `2026-03-01` / `2026-03-03` | cohort 业务安装日期窗口。 |
| `activation_dt_start` / `activation_dt_end` | `2026-03-01` / `2026-03-04` | 激活表分区扫描窗口；历史小窗口至少 T+1，当前窗口必须扫到 `latest_partition`。 |
| `event_dt_start` / `event_dt_end` | `2026-03-01` / `2026-03-10` | AF 事件观察窗口。 |
| `behavior_dt_start` / `behavior_dt_end` | `2026-03-01` / `2026-03-10` | 行为表观察窗口，需覆盖 D1/D7 计算所需日期。 |
| `hour_start` / `hour_end` | `00` / `23` | AF 事件小时分区。 |
| `bundle_id` | `com.HS.mahjong` | DT Android / kcolb Collection 包。 |
| `country_code` | `US` | 国家过滤。 |
| `behavior_app_name` | `block_mahjong_gp` | 行为表 app 名。 |

## SQL 1：激活 cohort 小样本

```sql
WITH params AS (
  SELECT
    '2026-03-01' AS install_start,
    '2026-03-03' AS install_end,
    '2026-03-01' AS activation_dt_start,
    '2026-03-04' AS activation_dt_end,
    'com.HS.mahjong' AS bundle_id,
    'US' AS country_code
)
SELECT
  SUBSTR(CAST(a.install_time AS STRING), 1, 10) AS install_date,
  a.bundle_id,
  UPPER(a.country) AS country_code,
  a.media_source,
  COUNT(DISTINCT a.distinct_id) AS user_cnt
FROM h-s.dwd_market_appsflyer_activation_push_data_di a
INNER JOIN params p
  ON a.bundle_id = p.bundle_id
WHERE a.dt BETWEEN p.activation_dt_start AND p.activation_dt_end
  AND SUBSTR(CAST(a.install_time AS STRING), 1, 10) BETWEEN p.install_start AND p.install_end
  AND UPPER(a.country) = p.country_code
  AND NVL(a.media_source, '') NOT IN (
    'aura_int','coolpadzhf_int','digitalturbine_int','huaweiadsglobal_int',
    'honordevicm_int','hihonor_int','lenovotabpai4p_int','nubia8rk_int',
    'onedigitalturbine_int','oppo_int','oppoglobal_int','oppopaipreinstall_int',
    'shalltry_int','shalltrypai_int','TCL','tctmobilewp_int',
    'transsionpreinstall_int','vivoglobal_int','vivootapreload_int',
    'vivopreload_int','xiaomiglobal_int','xiaomipai_int','xiaomipreload_int',
    'ztepai_int','ztesw_int'
  )
GROUP BY
  SUBSTR(CAST(a.install_time AS STRING), 1, 10),
  a.bundle_id,
  UPPER(a.country),
  a.media_source
ORDER BY user_cnt DESC
LIMIT 50;
```

## SQL 2：事件渗透率

```sql
WITH params AS (
  SELECT
    '2026-03-01' AS install_start,
    '2026-03-03' AS install_end,
    '2026-03-01' AS activation_dt_start,
    '2026-03-04' AS activation_dt_end,
    '2026-03-01' AS event_dt_start,
    '2026-03-10' AS event_dt_end,
    '00' AS hour_start,
    '23' AS hour_end,
    'com.HS.mahjong' AS bundle_id,
    'US' AS country_code
),
activation AS (
  SELECT DISTINCT
    a.distinct_id,
    a.bundle_id,
    SUBSTR(CAST(a.install_time AS STRING), 1, 10) AS install_date
  FROM h-s.dwd_market_appsflyer_activation_push_data_di a
  INNER JOIN params p
    ON a.bundle_id = p.bundle_id
  WHERE a.dt BETWEEN p.activation_dt_start AND p.activation_dt_end
    AND SUBSTR(CAST(a.install_time AS STRING), 1, 10) BETWEEN p.install_start AND p.install_end
    AND UPPER(a.country) = p.country_code
),
cohort AS (
  SELECT install_date, COUNT(DISTINCT distinct_id) AS cohort_users
  FROM activation
  GROUP BY install_date
),
events AS (
  SELECT
    a.install_date,
    e.event_name,
    COUNT(1) AS event_cnt,
    COUNT(DISTINCT e.customer_user_id) AS event_users
  FROM h-s.ods_appsflyer_block_collection_in_app_events_report_di e
  INNER JOIN activation a
    ON e.customer_user_id = a.distinct_id
   AND e.bundle_id = a.bundle_id
  INNER JOIN params p
    ON e.bundle_id = p.bundle_id
  WHERE e.dt BETWEEN p.event_dt_start AND p.event_dt_end
    AND e.hour BETWEEN p.hour_start AND p.hour_end
    AND e.event_name IS NOT NULL
    AND e.event_name <> ''
  GROUP BY a.install_date, e.event_name
)
SELECT
  e.install_date,
  e.event_name,
  e.event_cnt,
  e.event_users,
  c.cohort_users,
  CAST(e.event_users AS DOUBLE) / c.cohort_users AS penetration_rate
FROM events e
JOIN cohort c
  ON e.install_date = c.install_date
WHERE c.cohort_users > 0
ORDER BY penetration_rate DESC, event_users DESC
LIMIT 100;
```

## SQL 3：事件用户 ARPU / 留存

说明：交接文档中的候选事件在本小窗口未命中，验证时改用 SQL 2 返回的真实 Top 事件，以验证链路本身。

```sql
WITH params AS (
  SELECT
    '2026-03-01' AS install_start,
    '2026-03-03' AS install_end,
    '2026-03-01' AS activation_dt_start,
    '2026-03-04' AS activation_dt_end,
    '2026-03-01' AS event_dt_start,
    '2026-03-10' AS event_dt_end,
    '2026-03-01' AS behavior_dt_start,
    '2026-03-10' AS behavior_dt_end,
    '00' AS hour_start,
    '23' AS hour_end,
    'com.HS.mahjong' AS bundle_id,
    'US' AS country_code,
    'block_mahjong_gp' AS behavior_app_name
),
target_events AS (
  SELECT 'loop_level_5' AS event_name
  UNION ALL SELECT 'loop_playtime_10min' AS event_name
  UNION ALL SELECT 'ad_revenue2' AS event_name
  UNION ALL SELECT 's_ad_revenue_to_af07' AS event_name
  UNION ALL SELECT 'loop_ad_revenue_010' AS event_name
),
activation AS (
  SELECT DISTINCT
    a.distinct_id,
    a.bundle_id,
    SUBSTR(CAST(a.install_time AS STRING), 1, 10) AS install_date
  FROM h-s.dwd_market_appsflyer_activation_push_data_di a
  INNER JOIN params p
    ON a.bundle_id = p.bundle_id
  WHERE a.dt BETWEEN p.activation_dt_start AND p.activation_dt_end
    AND SUBSTR(CAST(a.install_time AS STRING), 1, 10) BETWEEN p.install_start AND p.install_end
    AND UPPER(a.country) = p.country_code
),
event_users AS (
  SELECT DISTINCT
    a.install_date,
    e.customer_user_id AS distinct_id,
    e.bundle_id,
    e.event_name
  FROM h-s.ods_appsflyer_block_collection_in_app_events_report_di e
  INNER JOIN activation a
    ON e.customer_user_id = a.distinct_id
   AND e.bundle_id = a.bundle_id
  INNER JOIN params p
    ON e.bundle_id = p.bundle_id
  INNER JOIN target_events t
    ON e.event_name = t.event_name
  WHERE e.dt BETWEEN p.event_dt_start AND p.event_dt_end
    AND e.hour BETWEEN p.hour_start AND p.hour_end
),
behavior AS (
  SELECT
    b.distinct_id,
    b.bundle_id,
    SUBSTR(CAST(b.install_datetime AS STRING), 1, 10) AS install_date,
    b.dt AS active_date,
    b.ad_revenue,
    b.game_cnt,
    b.usage_duration,
    DATEDIFF(
      TO_DATE(CAST(b.dt AS STRING), 'yyyy-MM-dd'),
      TO_DATE(SUBSTR(CAST(b.install_datetime AS STRING), 1, 10), 'yyyy-MM-dd'),
      'dd'
    ) AS day_diff
  FROM h-s.dws_block_collection_all_user_multi_dim_hi b
  INNER JOIN params p
    ON b.app_name = p.behavior_app_name
  WHERE b.dt BETWEEN p.behavior_dt_start AND p.behavior_dt_end
)
SELECT
  e.event_name,
  COUNT(DISTINCT e.distinct_id) AS event_users,
  CASE
    WHEN COUNT(DISTINCT e.distinct_id) = 0 THEN 0
    ELSE SUM(CASE WHEN b.day_diff = 0 THEN NVL(b.ad_revenue, 0) ELSE 0 END) / COUNT(DISTINCT e.distinct_id)
  END AS arpu_d1,
  CASE
    WHEN COUNT(DISTINCT e.distinct_id) = 0 THEN 0
    ELSE SUM(CASE WHEN b.day_diff BETWEEN 0 AND 6 THEN NVL(b.ad_revenue, 0) ELSE 0 END) / COUNT(DISTINCT e.distinct_id)
  END AS arpu_d7,
  CASE
    WHEN COUNT(DISTINCT e.distinct_id) = 0 THEN 0
    ELSE CAST(COUNT(DISTINCT CASE WHEN b.day_diff = 1 THEN e.distinct_id END) AS DOUBLE) / COUNT(DISTINCT e.distinct_id)
  END AS retention_d1,
  CASE
    WHEN COUNT(DISTINCT e.distinct_id) = 0 THEN 0
    ELSE CAST(COUNT(DISTINCT CASE WHEN b.day_diff = 7 THEN e.distinct_id END) AS DOUBLE) / COUNT(DISTINCT e.distinct_id)
  END AS retention_d7
FROM event_users e
LEFT JOIN behavior b
  ON e.distinct_id = b.distinct_id
 AND e.bundle_id = b.bundle_id
 AND e.install_date = b.install_date
GROUP BY e.event_name
ORDER BY event_users DESC
LIMIT 50;
```

## 预期输出

- SQL 1：按 `install_date x bundle_id x country x media_source` 输出 cohort 用户数。
- SQL 2：按 `install_date x event_name` 输出事件次数、事件用户数、cohort 用户数和渗透率。
- SQL 3：按 `event_name` 输出事件用户数、D1/D7 ARPU、D1/D7 留存。

## 复用护栏

- 不直接跑全量历史点位复盘大 SQL；先用小窗口验证 cohort、事件、行为三段链路。
- `install_time_window` 是业务 cohort 窗口，`activation_dt_scan_window` 是激活表入仓分区窗口，二者不能混用。
- 历史小窗口至少扫到安装结束日 T+1；当前窗口判断必须先 probe 激活表 `latest_partition`，再把 `activation_dt_end` 设到 `latest_partition`。
- 如果 `activation_dt_end < install_end + 1 day`，结果只能标 `partial_partition_scan`，不能作为完整 cohort 结论。
- `event_dt_window` 和 `behavior_dt_window` 是观察窗口，不用于修正激活迟到分区；两者应按 D1/D7 或点位观察需求单独扩展。

## 风险与陷阱

- 当前只验证 3 天安装窗口和 10 天行为观察窗口，不代表完整 2026-01-01 至 2026-03-31 可直接全量执行。
- SQL 2 / SQL 3 当前使用 `customer_user_id = activation.distinct_id`，扩大窗口前需复核是否要改用 `custom_data.ta_distinct_id` 或其他稳定键。
- SQL 2 / SQL 3 沿用原链路的激活 cohort 过滤，未额外排除预装媒体；如要与 SQL 1 的 media_source 过滤保持完全一致，需要显式同步排除列表。
- SQL 3 的事件列表应先来自 SQL 2 的 Top 事件或业务指定候选点位；不要固定套用不存在的事件名。
- `ods_appsflyer_block_collection_in_app_events_report_di` 必须限制 `dt/hour`。
- 不输出用户级明细。

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-13 | AI | verified | 3 条 SQL 均用 MaxCompute 小窗口执行成功；SQL 3 使用真实 Top 事件替代未命中的候选事件。 |
| 2026-06-13 | AI | verified_7d_window | 将安装窗口从 2026-03-01~03 扩大到 2026-03-01~07，行为/事件观察到 2026-03-14，3 条 SQL 均执行成功。 |
| 2026-06-18 | Codex | verified_template_rerun | 模板化后用 MaxCompute 重跑 3 条 SQL；激活表 `dt` 扫到 2026-03-04 纳入 T+1，三张目标表实时 `max(dt)` 均为 2026-06-18。 |

### 2026-06-13 验证明细

| SQL | 结果 | 聚合摘要 |
|---|---|---|
| SQL 1 | pass | 返回 DT Android / US cohort 聚合，主量级为 `applovin_int`、`Facebook Ads`、`unityads_int`、`organic`。 |
| SQL 2 | pass | 返回 Top 事件渗透率，`install` 为 100%，`loop_level_5`、`loop_playtime_10min`、`ad_revenue2` 等事件有稳定聚合。 |
| SQL 3 | pass | 返回 5 个事件的 D1/D7 ARPU 与 D1/D7 留存聚合，链路可 join 到行为表。 |

### 2026-06-13 七天窗口验证摘要

| SQL | 结果 | 聚合摘要 |
|---|---|---|
| SQL 1 | pass | 2026-03-01~07 安装窗口返回 DT Android / US cohort 聚合，主量级仍为 `applovin_int`、`Facebook Ads`、`unityads_int`、`organic`。 |
| SQL 2 | pass | Top 事件渗透率稳定，`install` 为 100%，`loop_level_5`、`loop_playtime_10min`、`ad_revenue2` 等事件在 7 天窗口继续有稳定聚合。 |
| SQL 3 | pass | 5 个 Top 事件返回 D1/D7 ARPU 与 D1/D7 留存；例如 `loop_level_5` 事件用户 3478，D7 ARPU 约 1.439，D7 留存约 17.34%。 |

### 2026-06-18 模板化重跑摘要

| SQL | 结果 | 聚合摘要 |
|---|---|---|
| 连通与分区 probe | pass | `SELECT 1` 成功；激活表、AF 事件表、行为表实时 `max(dt)` 均为 2026-06-18。 |
| SQL 1 | pass | 2026-03-01~03 安装窗口、激活 `dt` 扫到 2026-03-04 后返回 cohort 聚合，主量级仍为 `applovin_int`、`Facebook Ads`、`unityads_int`、`organic`。 |
| SQL 2 | pass | 返回 Top 事件渗透率，`install` 为 100%；`s_moudle_data_af_init`、`s_deep_link`、`loop_level_5`、`loop_playtime_10min`、`ad_revenue2` 等事件稳定返回。 |
| SQL 3 | pass | 5 个事件返回 D1/D7 ARPU 与 D1/D7 留存；例如 `loop_level_5` 事件用户 1544，D7 ARPU 约 1.5764，D7 留存约 18.91%。 |
