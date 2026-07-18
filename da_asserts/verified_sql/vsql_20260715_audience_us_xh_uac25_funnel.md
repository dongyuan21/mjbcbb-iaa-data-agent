# Verified SQL: US-XH-UAC2.5 人群包漏斗诊断

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260715_audience_us_xh_uac25_funnel` |
| 状态 | verified |
| promotion_status | verified_sql |
| sql_status | verified |
| 运行来源 | 本文档 `### Canonical SQL` 下唯一的 `sql` fence |
| 适用场景 | 对比 US-XH-UAC2.5-DA_s2-260601 campaign 归因用户在原版/放宽版各层人数差异 |
| 最后验证 | 2026-07-15 |
| validation_method | manual_small_window |
| owner | Cursor Agent |
| supersedes | [] |
| 源 candidate | `candidate_sql/audience/sql/audience_us_xh_uac25_funnel.sql`（晋升后已移除） |

## 原始问题

> 对比 US-XH-UAC2.5-DA_s2-260601 campaign 的 AF 归因用户在严格快照、放宽快照和原版过滤（token+push_status+语言+时区）下各层人数，定位放宽版人群包人数变化来源。

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | AF 事件 `dt BETWEEN '2026-06-01' AND '2026-06-09'`；dim 快照 `dt = '2026-06-09'` |
| 粒度 | campaign 级聚合（无分组维度，输出 4 个计数） |
| af_users | AF campaign 归因去重用户数 |
| join_dim_strict_snapshot | 严格快照（dt=2026-06-09, hour=23）join 命中数 |
| relaxed_final | 放宽快照（dt 范围取 MAX）join 命中数 |
| original_final_no_404 | 原版最终人数：有 token + push_status=open + 有语言 + 有时区 |

## 依赖表

| 表 | 用途 |
|---|---|
| `h-s.ods_appsflyer_all_in_app_events_report_di` | AF 事件，提取 campaign 归因 distinct_id |
| `h-s.dim_kcolb_tsalb_gp_user_ha` | 用户维度小时快照（push_status, pushtoken, language, zone_offset） |
| `h-s.dim_kcolb_tsalb_gp_user_first_start_da` | 用户首次启动信息（last_zone_offset, last_system_language） |

## 复用参数

| 参数 | 说明 |
|---|---|
| `${start_date}` | AF 事件窗口起始，如 `2026-06-01` |
| `${end_date}` | AF 事件窗口结束，如 `2026-06-09` |
| `${snapshot_dt}` | dim 快照日期，如 `2026-06-09` |
| `${campaign}` | campaign 名称，如 `US-XH-UAC2.5-DA_s2-260601` |
| `${bundle_id}` | `com.kcolb.juggle` |

## 风险与陷阱

- `distinct_id` 仅在 CTE 内部 JOIN 使用，最终 SELECT 只输出聚合计数，**不输出用户级明细**。
- `hour = '23'` 严格快照依赖 HA 表的小时分区，若当天 23 时分区缺失则 strict 计数为 0。
- 放宽版取 `dt BETWEEN start AND end` 的 MAX，会合并多天快照，可能导致同一用户多次出现后被 COUNT DISTINCT 去重。
- `original_final_no_404` 的 push_status='open' 过滤会排除关闭推送和卸载（404）用户，这是原版人群包缩小的主要原因。

## 验证记录

### 2026-07-15 · MaxCompute 实时探测

探测：`ods_appsflyer_all_in_app_events_report_di` max(dt)=2026-06-30；`dim_kcolb_tsalb_gp_user_ha` max(dt)=2026-06-30；`dim_kcolb_tsalb_gp_user_first_start_da` max(dt)=2026-06-30。

| 验证批次 | 窗口 | 结果摘要 |
|---|---|---|
| smoke-1 | 2026-06-01..2026-06-09 | af_users=1,099; join_dim_strict_snapshot=1,099; relaxed_final=1,099; original_final_no_404=420 |

漏斗分析：原版过滤后 420/1099 = 38.2% 通过率；放宽版 1099/1099 = 100% 通过率。主要损失来自 push_status=open 和 token 非空过滤。

## SQL

### Canonical SQL

```sql
-- 漏斗诊断：对比原版 vs 当前放宽版各层人数（只读 SELECT）
WITH af_campaign_user AS (
    SELECT DISTINCT get_json_object(custom_data, '$.ta_distinct_id') AS distinct_id
    FROM h-s.ods_appsflyer_all_in_app_events_report_di
    WHERE dt BETWEEN '${start_date}' AND '${end_date}'
      AND bundle_id = 'com.kcolb.juggle'
      AND campaign = '${campaign}'
      AND get_json_object(custom_data, '$.ta_distinct_id') IS NOT NULL
      AND get_json_object(custom_data, '$.ta_distinct_id') <> ''
),
user_dim_strict AS (
    SELECT distinct_id, MAX(s_push_status) AS s_push_status, MAX(s_pushtoken) AS s_pushtoken,
           MAX(system_language) AS system_language, MAX(zone_offset) AS zone_offset
    FROM h-s.dim_kcolb_tsalb_gp_user_ha
    WHERE dt = '${snapshot_dt}' AND hour = '23' AND distinct_id IS NOT NULL
    GROUP BY distinct_id
),
user_dim_relaxed AS (
    SELECT distinct_id, MAX(s_pushtoken) AS s_pushtoken,
           MAX(system_language) AS system_language, MAX(zone_offset) AS zone_offset
    FROM h-s.dim_kcolb_tsalb_gp_user_ha
    WHERE dt BETWEEN '${start_date}' AND '${end_date}'
      AND distinct_id IS NOT NULL
    GROUP BY distinct_id
),
user_first_start_info AS (
    SELECT distinct_id, MAX(last_zone_offset) AS last_zone_offset, MAX(last_system_language) AS last_system_language
    FROM h-s.dim_kcolb_tsalb_gp_user_first_start_da
    WHERE dt = '${snapshot_dt}' AND distinct_id IS NOT NULL
    GROUP BY distinct_id
)
SELECT
    (SELECT COUNT(DISTINCT distinct_id) FROM af_campaign_user) AS af_users,
    COUNT(DISTINCT CASE WHEN ds.distinct_id IS NOT NULL THEN a.distinct_id END) AS join_dim_strict_snapshot,
    COUNT(DISTINCT CASE WHEN dr.distinct_id IS NOT NULL THEN a.distinct_id END) AS relaxed_final,
    COUNT(DISTINCT CASE
        WHEN ds.s_pushtoken IS NOT NULL AND ds.s_push_status = 'open'
         AND COALESCE(f.last_system_language, ds.system_language) IS NOT NULL
         AND COALESCE(f.last_zone_offset, CAST(ds.zone_offset AS STRING)) IS NOT NULL
        THEN a.distinct_id END) AS original_final_no_404
FROM af_campaign_user a
LEFT JOIN user_dim_strict ds ON a.distinct_id = ds.distinct_id
LEFT JOIN user_dim_relaxed dr ON a.distinct_id = dr.distinct_id
LEFT JOIN user_first_start_info f ON a.distinct_id = f.distinct_id;
```
