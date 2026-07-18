# Verified SQL: 点位事件 触发渗透 + 触发用户价值

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260616_point_event_penetration_value` |
| 状态 | verified |
| 来源 | `../analysis_sop/MJ_DT历史点位复盘SOP.md` 方法泛化 + 本次 kcolb_tsalb 实测 |
| 适用场景 | 点位事件(转化优化目标)的用户触发渗透率、触发用户 D1/D7 ARPU 与留存——评估点位事件的覆盖与人群价值 |
| 最后验证 | 2026-06-18 |

## 原始问题

> 投放某点位(优化目标)后,cohort 用户里有多少真正触发了该点位事件,触发用户的 ARPU/留存是否更优?

## 依赖表(MaxCompute h-s)

| 表 | 角色 |
|---|---|
| `dwd_market_appsflyer_activation_push_data_di` | cohort 分母(激活用户) |
| `ods_appsflyer_all_in_app_events_report_di` | 点位事件触发明细(~129TB,必须 WHERE dt+hour);点位事件 = `event_name` |
| `dws_kcolb_tsalb_all_user_multi_dim_hi` | 触发用户价值(ad_revenue / 留存);其他产品换 `dws_block_collection_*` / `dws_nova_collection_*` |

## 口径说明

| 类型 | 内容 |
|---|---|
| 点位事件 | = AF 事件表 `event_name`(实测多为 `event_source='SDK'` 上报,非 S2S 专属) |
| 渗透率 | 触发该 event 的 cohort 用户数 / cohort 安装用户数 |
| 触发用户价值 | 触发用户 join 行为表:`SUM(ad_revenue) where day_diff<=N / 触发用户数`;留存按 day_diff |
| cohort | 激活表 `install_time` 截取日期;join 行为表用 `distinct_id + bundle_id + install_date` |
| 桥(关键) | 映射表 `s2s_event` 与 AF `event_name` **非严格 1:1**(实测 `Total_Ads_Revenue_0013` vs `Total_Ads_Revenue_NU_0013`,带 NU/媒体/编号后缀);精确按点位须先确认对应 event_name,本 SQL 用两边同名的 `s_custom9_revenue_3` 验证 |
| PII | 不输出 distinct_id/customer_user_id 明细,只聚合 |

## 复用参数

复用本 SQL 时，不直接复制历史日期。必须先确定以下参数，并把窗口写进最终输出：

| 参数 | 说明 |
|---|---|
| `${bundle_id}` | 激活表、事件表包名，如 `com.kcolb.juggle`。 |
| `${app_name}` | 行为聚合表产品桶，如 `kcolb_tsalb_gp`。 |
| `${country}` | 激活 cohort 国家，如 `US`。 |
| `${event_name}` | AF 事件名，如 `s_custom9_revenue_3`；必须先完成 s2s_event ↔ AF event_name 桥确认。 |
| `${install_start}` / `${install_end}` | cohort 的 install / activation 业务日期窗口。 |
| `${activation_dt_scan_start}` | 通常取 `${install_start}`。 |
| `${activation_dt_scan_end}` | 当前窗口必须取激活表 `latest_partition`，或至少覆盖 `${install_end}` 的 T+1。 |
| `${event_dt_start}` / `${event_dt_end}` | AF 事件观察窗口，按点位触发观察天数设置，必须带 `hour`。 |
| `${behavior_dt_start}` / `${behavior_dt_end}` | 行为价值观察窗口，按 D1/D7 留存和 ARPU 窗口设置。 |
| `${hour_start}` / `${hour_end}` | AF 事件表小时过滤，默认 `00` ~ `23`。 |

输出必须同时写明：

```text
install_time_window:
activation_dt_scan_window:
event_dt_window:
behavior_dt_window:
activation_target_latest_dt:
event_name_bridge_status:
current_window_conclusion_allowed:
```

如果 `${activation_dt_scan_end}` 未覆盖 `${install_end}` 的 T+1，结果只能标为 `partial_partition_scan`，不能给当前窗口强结论。事件表和行为表窗口是观察窗口，不能替代激活表的迟到分区护栏。

## SQL

```sql
WITH params AS (
  SELECT
    '${bundle_id}' AS bundle_id,
    '${app_name}' AS app_name,
    UPPER('${country}') AS country_code,
    '${event_name}' AS event_name,
    '${install_start}' AS install_start,
    '${install_end}' AS install_end,
    '${activation_dt_scan_start}' AS activation_dt_scan_start,
    '${activation_dt_scan_end}' AS activation_dt_scan_end,
    '${event_dt_start}' AS event_dt_start,
    '${event_dt_end}' AS event_dt_end,
    '${behavior_dt_start}' AS behavior_dt_start,
    '${behavior_dt_end}' AS behavior_dt_end,
    '${hour_start}' AS hour_start,
    '${hour_end}' AS hour_end
),
activation AS (
  SELECT DISTINCT
    t.distinct_id,
    t.bundle_id,
    SUBSTR(CAST(t.install_time AS STRING), 1, 10) AS install_date
  FROM h-s.dwd_market_appsflyer_activation_push_data_di t
  INNER JOIN params p
    ON t.bundle_id = p.bundle_id
  WHERE t.dt BETWEEN p.activation_dt_scan_start AND p.activation_dt_scan_end
    AND SUBSTR(CAST(t.install_time AS STRING), 1, 10)
      BETWEEN p.install_start AND p.install_end
    AND UPPER(t.country) = p.country_code
),
point_users AS (
  SELECT DISTINCT a.distinct_id, a.bundle_id, a.install_date
  FROM h-s.ods_appsflyer_all_in_app_events_report_di e
  INNER JOIN activation a
    ON e.customer_user_id = a.distinct_id
   AND e.bundle_id = a.bundle_id
  INNER JOIN params p
    ON e.bundle_id = p.bundle_id
  WHERE e.dt BETWEEN p.event_dt_start AND p.event_dt_end
    AND e.hour BETWEEN p.hour_start AND p.hour_end
    AND e.event_name = p.event_name
),
behavior AS (
  SELECT
    t.distinct_id,
    t.bundle_id,
    SUBSTR(CAST(t.install_datetime AS STRING), 1, 10) AS install_date,
    ad_revenue,
    DATEDIFF(
      TO_DATE(CAST(t.dt AS STRING), 'yyyy-MM-dd'),
      TO_DATE(SUBSTR(CAST(t.install_datetime AS STRING), 1, 10), 'yyyy-MM-dd'),
      'dd'
    ) AS day_diff
  FROM h-s.dws_kcolb_tsalb_all_user_multi_dim_hi t
  INNER JOIN params p
    ON t.app_name = p.app_name
  WHERE t.dt BETWEEN p.behavior_dt_start AND p.behavior_dt_end
)
SELECT
  (SELECT COUNT(DISTINCT distinct_id) FROM activation) AS cohort_users,
  COUNT(DISTINCT p.distinct_id) AS point_users,
  ROUND(COUNT(DISTINCT p.distinct_id)*1.0/(SELECT COUNT(DISTINCT distinct_id) FROM activation),4) AS penetration,
  ROUND(SUM(CASE WHEN b.day_diff=0 THEN b.ad_revenue ELSE 0 END)/COUNT(DISTINCT p.distinct_id),4) AS arpu_d1,
  ROUND(SUM(CASE WHEN b.day_diff BETWEEN 0 AND 6 THEN b.ad_revenue ELSE 0 END)/COUNT(DISTINCT p.distinct_id),4) AS arpu_d7,
  ROUND(COUNT(DISTINCT CASE WHEN b.day_diff=1 THEN p.distinct_id END)*1.0/COUNT(DISTINCT p.distinct_id),4) AS retention_d1
FROM point_users p
LEFT JOIN behavior b
  ON p.distinct_id=b.distinct_id AND p.bundle_id=b.bundle_id AND p.install_date=b.install_date;
```

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-16 | AI | verified | com.kcolb.juggle / US / 安装 06-07~09 / 观察至 06-16:cohort 204135,触发 `s_custom9_revenue_3` 83712,**渗透 41.0%**,触发用户 **D1 ARPU 0.286 / D7 ARPU 0.665 / 次留 22.9%**;链路(激活→事件触发→行为价值)跑通,数字符合"收入类点位触发用户价值更高"预期。 |
| 2026-06-18 | Codex | verified_template_rerun | 参数化模板用 MaxCompute 实跑成功；`install_time_window=2026-06-07 ~ 2026-06-09`，`activation_dt_scan_window=2026-06-07 ~ 2026-06-10`，`event_dt_window=2026-06-07 ~ 2026-06-16`，`behavior_dt_window=2026-06-07 ~ 2026-06-16`。 |

### 2026-06-18 模板复跑摘要

本次复跑把激活表 `dt` 扫到 install 结束日 T+1，因此 cohort 分母与 2026-06-16 旧摘要不同；复用本 SQL 时应优先使用 `activation_dt_scan_window` 口径。

| cohort_users | point_users | penetration | arpu_d1 | arpu_d7 | retention_d1 |
|---:|---:|---:|---:|---:|---:|
| 240252 | 97893 | 40.75% | 0.2847 | 0.6820 | 23.99% |

## 风险与陷阱

- **s2s_event ↔ AF event_name 桥(实测量化)**:com.kcolb.juggle 255 个 s2s_event 中 **76.1% 精确同名** AF event_name,去 `_IOS/_NU/编号` 后缀模糊匹配后达 **82.4% 覆盖**;剩余 18% 多为 iOS 专属点位(`_IOS`,GP 包不触发)、浅层事件(`adsvalue_*`/`AdImpression`)或窗口内未触发。建桥规则:精确同名优先 → 去后缀模糊 → 其余标注待确认。桥结果见 `../../raw_exports/点位s2s验证/bridge_map.json`。CK 无 s2s_event↔event_name 桥表(5 张映射表只到 campaign 级)。
- **AF 事件表 ~129TB**:必须 `WHERE dt AND hour`;窗口越长越慢(本 demo 3 天安装 + 10 天观察约 200s)。
- **join 键**:`customer_user_id = activation.distinct_id` 已小窗口验证;扩窗前复核是否改用 `custom_data.ta_distinct_id`。
- **cohort 分母**:本 SQL 用 activation 表;若与 PGP 官方口径对齐,改用 AF ODS `event_name='install'` 去重(见 ai_hive/口径决策记录)。
- **activation 迟到分区**:按 `install_time` 取 cohort 时，激活表 `dt` 必须扫到 `latest_partition` 或至少 T+1；事件表和行为表观察窗口不能替代这个护栏。
- **可扩展**:加"全 cohort vs 触发用户"价值对照,量化点位事件的人群区分度。

## 两跳合并(点位全景)关键发现

把投放侧(CK:点位→消耗/CPI/ROI,US/06-07~09)与用户侧(MC:点位→渗透/D7ARPU/次留)按点位名经桥合并,实测发现:

- **投放有消耗的 Top 优化目标点位**(`af_purchase` CPI11/ROI7 0.13、`Total_Ads_Revenue_0013`、`Total_Ads_Revenue_US_per020` ROI7 0.36、`ad_impression_all`)与**用户高频触发 Top 事件**(`install`、`s_ad_revenue_to_af3/4/13`、`s_custom9_revenue_3`、`game_end_*`)**几乎不重叠**(8 个投放点位全部匹配不到用户侧 Top)。
- **结论**:投放买的"深度转化优化目标"(如购买 af_purchase)触发渗透低、不在用户高频事件里;用户高频触发的是行为/收入埋点(s_custom*/s_ad_revenue*)。s2s_event↔event_name 命名层面 76% 可桥,但"有消耗的优化目标"与"用户高频事件"是**不同事件集、不同层次**。
- **双向验证(2026-06-16)**:反查用户侧高频的 10 个 `s_custom*_revenue` 点位,在投放侧(06-07~09)**仅 1 个有记录且消耗为 0**,其余全无消耗——双向确证"投放优化目标"与"用户高频触发事件"在当前窗口**几乎完全错位、无交集**。
- **含义**:同一点位的"端到端全景"(投放 ROI → 触发渗透 → 价值)在当前数据下做不出来,因为投放花钱的点位(af_purchase/Total_Ads_Revenue,深度优化目标)和用户高频触发的点位(s_custom*/s_ad_revenue*,行为埋点)是**两套**。点位治理须分两层:投放优化目标侧(第一跳,消耗/ROI) vs 用户行为事件侧(第二跳,渗透/价值);仅当某点位既被当作 campaign 优化目标投放、又被用户高频触发时才可同点位端到端,当前窗口此类点位极少。
- 全景合并脚本与结果:`../../raw_exports/点位s2s验证/merge_full.py`、`point_full_view.json`。

## 关联

- 第一跳(点位→campaign→ROI):`vsql_20260616_point_s2s_roi_review.md`
- 方法论:`../analysis_sop/20260616_报告看板数据可信度反查SOP.md`、`MJ_DT历史点位复盘SOP.md`
- 表盘点:`../../ai_hive/agent_knowledge/tables/ods_appsflyer_all_in_app_events_report_di.yaml`
