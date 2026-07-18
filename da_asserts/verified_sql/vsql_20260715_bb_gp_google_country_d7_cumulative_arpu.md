# Verified SQL: BB GP Google 分国家 D0 / D7 累计 ARPU

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260715_bb_gp_google_country_d7_cumulative_arpu` |
| 状态 | verified |
| promotion_status | verified_sql |
| sql_status | verified |
| 适用场景 | `kcolb_tsalb_gp` / `googleadwords_int` 固定历史 cohort `2026-06-17` 的分国家 D0 与 D7 累计 DA 行为 ARPU 回放 |
| 最后验证 | 2026-07-15 |
| validation_method | MaxCompute live historical-window rerun |

## 口径说明

- cohort 来源：`h-s.dwd_market_appsflyer_activation_push_data_di`，`bundle_id='com.kcolb.juggle'`、`media_source='googleadwords_int'`、`install_date='2026-06-17'`。
- 收入来源：`h-s.dws_kcolb_tsalb_all_user_multi_dim_hi.ad_revenue`，`app_name='kcolb_tsalb_gp'`。
- D0：安装当日 `2026-06-17` 行为收入。
- D7 累计：D0–D7 共 8 个自然日，行为窗口 `2026-06-17~2026-06-24`；不是仅取第 7 天单日收入。
- 分母：`LEFT JOIN + COALESCE` 保留 cohort 中 0 收入用户。
- 输出仅保留国家级聚合，`distinct_id` 仅用于 CTE 内部，不输出用户级明细。
- 该 SQL 是固定历史 replay 证据，不用于推导当前日期的实时投放结论。

## SQL 1：激活表当前分区探测

```sql
SELECT max(dt) AS latest_dt
FROM h-s.dwd_market_appsflyer_activation_push_data_di;
```

## SQL 2：行为表当前分区探测

```sql
SELECT max(dt) AS latest_dt
FROM h-s.dws_kcolb_tsalb_all_user_multi_dim_hi;
```

## SQL 3：分国家 D0 / D7 累计 ARPU

```sql
WITH activation_cohort AS (
    SELECT DISTINCT
        distinct_id,
        COALESCE(country, 'unknown') AS country
    FROM h-s.dwd_market_appsflyer_activation_push_data_di
    WHERE dt BETWEEN '2026-06-17' AND '2026-06-24'
      AND bundle_id = 'com.kcolb.juggle'
      AND media_source = 'googleadwords_int'
      AND SUBSTR(CAST(install_time AS STRING), 1, 10) = '2026-06-17'
),
user_revenue AS (
    SELECT
        c.country,
        c.distinct_id,
        SUM(
            CASE WHEN b.dt = '2026-06-17'
                 THEN COALESCE(b.ad_revenue, 0) ELSE 0 END
        ) AS d0_revenue,
        SUM(
            CASE WHEN b.dt BETWEEN '2026-06-17' AND '2026-06-24'
                 THEN COALESCE(b.ad_revenue, 0) ELSE 0 END
        ) AS d7_cumulative_revenue
    FROM activation_cohort c
    LEFT JOIN h-s.dws_kcolb_tsalb_all_user_multi_dim_hi b
        ON c.distinct_id = b.distinct_id
       AND b.app_name = 'kcolb_tsalb_gp'
       AND b.dt BETWEEN '2026-06-17' AND '2026-06-24'
    GROUP BY c.country, c.distinct_id
)
SELECT
    country,
    COUNT(*) AS cohort_users,
    ROUND(AVG(COALESCE(d0_revenue, 0)), 6) AS d0_arpu,
    ROUND(AVG(COALESCE(d7_cumulative_revenue, 0)), 6) AS d7_cumulative_arpu
FROM user_revenue
GROUP BY country
ORDER BY cohort_users DESC
LIMIT 200;
```

## 验证记录

2026-07-15 使用 MaxCompute 只读 helper 实时执行：

- MC `SELECT 1` 成功。
- 激活表当前 `latest_dt=2026-07-14`。
- 核心历史窗口 SQL 成功返回 200 个国家聚合行（带 `LIMIT 200`）。
- 返回行中 `d7_cumulative_arpu >= d0_arpu` 全部成立。

## 风险与陷阱

- 该回放固定在 2026-06-17 历史 cohort，不能把返回值当作当前实时水位。
- `ad_revenue` 是 DA 行为收入口径，不等于 SDK attributed 回收或 MI ROI360 收入。
- D7 累计使用 D0–D7，与 runtime 的累计口径一致；若业务明确要求“D7 当天”，不能复用本结果。
- 国家小样本只做风险提示；不据此输出停投、放量或预算动作。

## Agent 使用提示

- 固定问题命中 `kcolb_tsalb_gp + googleadwords_int + 分国家 + D0/D7 收入均值` 时，runtime 可执行本文档的 3 条已验 SQL 并直接收口。
- 回答必须显式写 `D7 累计`、`2026-06-17`、`LEFT JOIN + COALESCE`、`freshness_status`。
- 仅输出分析和风险预警，不给停投、放量或预算动作。
