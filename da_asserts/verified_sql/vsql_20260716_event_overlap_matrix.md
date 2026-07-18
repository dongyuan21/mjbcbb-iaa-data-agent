# Verified SQL: 用户价值×点位事件矩阵 - 事件间用户重叠率

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260716_event_overlap_matrix` |
| 状态 | verified |
| promotion_status | verified_sql |
| sql_status | verified |
| 运行来源 | 本文档 `### Canonical SQL` 下唯一的 `sql` fence |
| 关联 SOP | `../analysis_sop/用户价值点位事件矩阵分析SOP.md` |
| 补充 verified SQL | `vsql_20260616_point_event_penetration_value.md`（渗透率+ARPU，本 SQL 补事件重叠率） |
| 适用场景 | 同一 cohort 内不同事件点位的用户重叠率，判断事件间信息量冗余度 |
| 最后验证 | 2026-07-16 |
| validation_method | manual_small_window |
| owner | Cursor Agent |
| supersedes | [] |
| 源 candidate | `candidate_sql/event_overlap_matrix.sql`（晋升后已移除） |

## 原始问题

> 同一 cohort 内，不同事件点位的用户重叠率是多少？过高重叠说明新增信息量有限，过低渗透说明学习困难。

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | AF 事件表 `dt` 按日，cohort 来自激活表 install_date |
| 粒度 | `event_name_a × event_name_b` 的用户交集/并集 |
| cohort 限定 | 先 join 激活表限定 distinct_id 范围 |
| 重叠率 | `count(同时触发 A 和 B) / count(触发 A 或 B)` |
| A_given_B_rate | `count(同时触发 A 和 B) / count(触发 A)` |
| 去重 | 事件 × 用户粒度先 GROUP BY 去重，再 pairwise JOIN |

## 依赖表

| 表 | 用途 |
|---|---|
| `h-s.dwd_market_appsflyer_activation_push_data_di` | cohort 分母（激活用户） |
| `h-s.ods_appsflyer_all_in_app_events_report_di` | AF 事件明细（~129TB，必须带 dt 分区过滤） |

## 复用参数

| 参数 | 说明 |
|---|---|
| `${start_date}` | 窗口起始日，如 `2026-07-14` |
| `${end_date}` | 窗口结束日，如 `2026-07-14` |
| `${bundle_id}` | 包体 ID，如 `com.kcolb.juggle` |
| `${platform}` | 平台，如 `android` |
| `${event_names}` | 事件名列表，如 `'s_ad_revenue_to_af13','s_ad_revenue_to_af3','s_ad_revenue_to_af_PLTV'` |

## 风险与陷阱

- `ods_appsflyer_all_in_app_events_report_di` 约 129TB，**必须带 dt 分区过滤**，否则全表扫描。
- 事件名可能带后缀变体（如 `s_ad_revenue_to_af13` vs `s_ad_revenue_to_NU_af13`），需先确认事件名清单。
- 重叠率分母用并集（OR），不是单一事件用户数。
- 事件数过多时 pairwise 组合爆炸（N²），建议先筛 Top 10 事件再算重叠。
- 不输出 `distinct_id` 明细，只做聚合。

## 验证记录

### 2026-07-16 · MaxCompute 实时探测

探测：`dwd_market_appsflyer_activation_push_data_di` max(dt)=2026-07-15；`ods_appsflyer_all_in_app_events_report_di` max(dt)=2026-07-15。

| 验证批次 | 日期 | 事件数 | 行数 | 结果摘要 |
|---|---|---|---|---|
| smoke-1 | 2026-07-14 | 3 | 3 | af13×af3 overlap=85.46% (502,286/587,771); af3×PLTV overlap=12.83% (73,177/570,271); af13×PLTV overlap=5.26% (30,235/574,292) |

完整验证结果：

| event_a | event_b | users_a | users_b | intersection | overlap_rate |
|---|---|---|---|---|---|
| s_ad_revenue_to_af13 | s_ad_revenue_to_af3 | 525,568 | 564,489 | 502,286 | 0.854561 |
| s_ad_revenue_to_af3 | s_ad_revenue_to_af_PLTV | 564,489 | 78,959 | 73,177 | 0.128320 |
| s_ad_revenue_to_af13 | s_ad_revenue_to_af_PLTV | 525,568 | 78,959 | 30,235 | 0.052647 |

验证确认：af13 与 af3 高度重叠（85.46%），信息量冗余大；PLTV 与两者重叠低，独立信息量高。

## SQL

### Canonical SQL

```sql
/* EVENT_OVERLAP_MATRIX */
WITH
    cohort_users AS (
        SELECT DISTINCT get_json_object(custom_data, '$.ta_distinct_id') AS distinct_id
        FROM h-s.dwd_market_appsflyer_activation_push_data_di
        WHERE dt BETWEEN '${start_date}' AND '${end_date}'
          AND bundle_id = '${bundle_id}'
          AND platform = '${platform}'
          AND get_json_object(custom_data, '$.ta_distinct_id') IS NOT NULL
          AND get_json_object(custom_data, '$.ta_distinct_id') <> ''
    ),
    event_users AS (
        SELECT
            e.event_name,
            get_json_object(e.custom_data, '$.ta_distinct_id') AS distinct_id
        FROM h-s.ods_appsflyer_all_in_app_events_report_di e
        INNER JOIN cohort_users c
            ON get_json_object(e.custom_data, '$.ta_distinct_id') = c.distinct_id
        WHERE e.dt BETWEEN '${start_date}' AND '${end_date}'
          AND e.bundle_id = '${bundle_id}'
          AND e.event_name IN (${event_names})
          AND get_json_object(e.custom_data, '$.ta_distinct_id') IS NOT NULL
          AND get_json_object(e.custom_data, '$.ta_distinct_id') <> ''
        GROUP BY e.event_name, get_json_object(e.custom_data, '$.ta_distinct_id')
    ),
    event_counts AS (
        SELECT
            event_name,
            count(DISTINCT distinct_id) AS event_users
        FROM event_users
        GROUP BY event_name
    ),
    pairwise AS (
        SELECT
            a.event_name AS event_a,
            b.event_name AS event_b,
            count(DISTINCT a.distinct_id) AS intersection
        FROM event_users a
        INNER JOIN event_users b
            ON a.distinct_id = b.distinct_id
           AND a.event_name < b.event_name
        GROUP BY a.event_name, b.event_name
    )
SELECT
    p.event_a,
    p.event_b,
    ea.event_users AS users_a,
    eb.event_users AS users_b,
    p.intersection,
    round(p.intersection / nullIf(ea.event_users + eb.event_users - p.intersection, 0), 6) AS overlap_rate,
    round(p.intersection / nullIf(ea.event_users, 0), 6) AS a_given_b_rate
FROM pairwise p
INNER JOIN event_counts ea ON p.event_a = ea.event_name
INNER JOIN event_counts eb ON p.event_b = eb.event_name
ORDER BY overlap_rate DESC
LIMIT 100
```
