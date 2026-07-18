# Verified SQL: BB GP 渠道×国家内用户 Top20% D30 DA 收入集中度

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260630_d30_top20_user_concentration_channel_country` |
| 状态 | verified |
| promotion_status | verified_sql |
| sql_status | verified |
| 运行来源 | 本文档 `### Canonical SQL` 下唯一的 `sql` fence |
| 关联文档 | `../../bugfix_doc/20260630_PI同题稳定性_D30渠道国家Top20集中度.md` |
| 适用场景 | 每个渠道×国家格子内，用户 D30 DA 行为 ARPU Top20% 占该格 D30 总收入比例 |
| 最后验证 | 2026-06-30 |
| validation_method | manual_small_window |

## 原始问题

> 分析 kcolb_tsalb_gp 每个渠道每个国家，top20% 累积 d30arpu，能占 d30 总 arpu 的比例。

## 口径说明

| 类型 | 内容 |
|---|---|
| Top20% 语义 | **A**：每个 `(media_source, country)` 格子内，按用户 D30 累计 DA `ad_revenue` 降序，取 **`CEIL(用户数 × 0.2)`** 个用户 |
| 分子 | Top20% 用户的 D30 DA 行为收入之和 |
| 分母 | 该格子 cohort 全量用户的 D30 DA 行为收入之和（含 0 收入用户） |
| 输出列 | `top20_user_revenue_share_in_segment` = 分子 / 分母 |
| 收入口径 | **DA 行为** `dws_kcolb_tsalb_all_user_multi_dim_hi.ad_revenue`（非 SDK attributed） |
| D30 窗口 | 安装日起 D0–D29 共 30 个自然日 `dt` 累计 |
| Cohort 成熟度 | 仅 **D30 完整**安装日；数据最新行为日 `t-1` 时，成熟安装窗 **`install_date ∈ [t-59, t-30]`** |
| 小样本 | 默认 `HAVING cohort_users >= 20`；不足须标 `needs_decision` |
| PII | `distinct_id` 仅 CTE 内使用，最终 SELECT 不输出 |

## 依赖表

| 表 | 用途 |
|---|---|
| `h-s.dwd_market_appsflyer_activation_push_data_di` | 激活 cohort、`media_source`、`country`、install 日 |
| `h-s.dws_kcolb_tsalb_all_user_multi_dim_hi` | DA 日级 `ad_revenue`，须 `app_name='kcolb_tsalb_gp'` |

## 复用参数

| 参数 | 说明 |
|---|---|
| `${bundle_id}` | `com.kcolb.juggle` |
| `${app_name}` | `kcolb_tsalb_gp` |
| `${mature_install_start}` | 成熟窗起点，如 `t-59` |
| `${mature_install_end}` | 成熟窗终点，如 `t-30`（须满足 `mature_install_end + 29 <= behavior_dt_end`） |
| `${activation_dt_scan_start}` | 通常 = `mature_install_start` |
| `${activation_dt_scan_end}` | 激活表 latest 分区或 ≥ `mature_install_end` |
| `${behavior_dt_start}` | 通常 = `mature_install_start` |
| `${behavior_dt_end}` | 通常 = `t-1`（行为数据最新完整日） |

输出必须写明：

```text
install_time_window: [mature_install_start, mature_install_end]
behavior_dt_window: [behavior_dt_start, behavior_dt_end]
d30_maturity: full
revenue_source: da_behavior_ad_revenue
activation_target_latest_dt:
behavior_target_latest_dt:
```

## 验证记录

### 2026-06-30 · MaxCompute 实时探测

探测：`dwd_market_appsflyer_activation_push_data_di` / `dws_kcolb_tsalb_all_user_multi_dim_hi` latest `dt = 2026-06-30`；行为窗口上界取 **`t-1 = 2026-06-29`**。

| 验证批次 | 安装窗 | 样本格子 | 结果摘要 |
|---|---|---|---|
| smoke-1 | 单日 `2026-05-31` | `googleadwords_int × US` | cohort=16,213；D30 DA 收入=25,032.37；**Top20% 占 88.38%**；零收入用户占 23.95% |
| smoke-2 | 成熟 30 日 `[2026-05-02, 2026-05-31]` | Top20 by 收入 | `googleadwords_int × US` cohort=555,408；D30 收入=791,352.16；**Top20% 占 89.84%** |

其他 Top 格子（成熟 30 日窗）示例：

| media_source | country | cohort_users | segment_d30_arpu | top20_user_revenue_share |
|---|---|---:|---:|---:|
| googleadwords_int | US | 555,408 | 1.425 | 0.898 |
| aura_int | US | 448,682 | 1.247 | 0.902 |
| organic | US | 716,763 | 0.553 | 0.967 |
| googleadwords_int | KR | 205,945 | 1.676 | 0.915 |

## SQL

### Canonical SQL

> Runtime 仅可从此 verified 文档提取 SQL；历史候选副本已在晋升后移除。

```sql
WITH params AS (
    SELECT
        '${bundle_id}' AS bundle_id,
        '${app_name}' AS app_name,
        '${mature_install_start}' AS mature_install_start,
        '${mature_install_end}' AS mature_install_end,
        '${activation_dt_scan_start}' AS activation_dt_scan_start,
        '${activation_dt_scan_end}' AS activation_dt_scan_end,
        '${behavior_dt_start}' AS behavior_dt_start,
        '${behavior_dt_end}' AS behavior_dt_end
),
activation_cohort AS (
    SELECT
        a.distinct_id,
        COALESCE(a.media_source, 'unknown') AS media_source,
        COALESCE(a.country, 'unknown') AS country,
        SUBSTR(CAST(a.install_time AS STRING), 1, 10) AS install_date
    FROM h-s.dwd_market_appsflyer_activation_push_data_di a
    INNER JOIN params p ON a.bundle_id = p.bundle_id
    WHERE a.dt BETWEEN p.activation_dt_scan_start AND p.activation_dt_scan_end
      AND SUBSTR(CAST(a.install_time AS STRING), 1, 10)
          BETWEEN p.mature_install_start AND p.mature_install_end
),
user_d30_revenue AS (
    SELECT
        c.media_source,
        c.country,
        c.distinct_id,
        SUM(COALESCE(b.ad_revenue, 0)) AS d30_ad_revenue
    FROM activation_cohort c
    LEFT JOIN h-s.dws_kcolb_tsalb_all_user_multi_dim_hi b
        ON  c.distinct_id = b.distinct_id
        AND b.app_name = (SELECT app_name FROM params LIMIT 1)
        AND b.dt >= c.install_date
        AND b.dt <= TO_CHAR(
            DATEADD(TO_DATE(c.install_date, 'yyyy-MM-dd'), 29, 'dd'),
            'yyyy-MM-dd'
        )
        AND b.dt BETWEEN (SELECT behavior_dt_start FROM params LIMIT 1)
                     AND (SELECT behavior_dt_end FROM params LIMIT 1)
    GROUP BY c.media_source, c.country, c.distinct_id
),
ranked_users AS (
    SELECT
        media_source,
        country,
        distinct_id,
        d30_ad_revenue,
        ROW_NUMBER() OVER (
            PARTITION BY media_source, country
            ORDER BY d30_ad_revenue DESC, distinct_id
        ) AS revenue_rank,
        COUNT(*) OVER (PARTITION BY media_source, country) AS segment_user_cnt,
        SUM(d30_ad_revenue) OVER (PARTITION BY media_source, country) AS segment_d30_revenue
    FROM user_d30_revenue
),
labeled AS (
    SELECT
        media_source,
        country,
        d30_ad_revenue,
        segment_user_cnt,
        segment_d30_revenue,
        CASE WHEN revenue_rank <= CEIL(segment_user_cnt * 0.2) THEN 1 ELSE 0 END AS is_top20_user
    FROM ranked_users
)
SELECT
    media_source,
    country,
    MAX(segment_user_cnt) AS cohort_users,
    ROUND(MAX(segment_d30_revenue), 4) AS segment_d30_da_revenue,
    ROUND(MAX(segment_d30_revenue) / NULLIF(MAX(segment_user_cnt), 0), 6) AS segment_d30_arpu,
    SUM(is_top20_user) AS top20_user_cnt,
    ROUND(SUM(CASE WHEN is_top20_user = 1 THEN d30_ad_revenue ELSE 0 END), 4) AS top20_user_d30_revenue,
    ROUND(
        SUM(CASE WHEN is_top20_user = 1 THEN d30_ad_revenue ELSE 0 END)
        / NULLIF(MAX(segment_d30_revenue), 0),
        4
    ) AS top20_user_revenue_share_in_segment
FROM labeled
GROUP BY media_source, country
HAVING MAX(segment_user_cnt) >= 20
ORDER BY top20_user_revenue_share_in_segment DESC, segment_d30_da_revenue DESC;
```

## 风险与陷阱

- **扫描成本**：成熟 30 日窗行为扫描约 58 天分区，全渠道×国家跑数较重；可先按 `media_source` / `country` 缩小。
- **零收入用户**：分母含 0 收入用户，Top20% 按**用户数**而非按有收入用户；organic 小格子可能出现 share≈1.0（几乎全部收入集中在 top 20% 用户）。
- **与 002452 历史报告不可比**：002452 为组合 Top20% + SDK 路径，本 SQL 为格子内用户 Top20% + DA 口径。
- **MaxCompute join**：`user_d30_revenue` 不可 `CROSS JOIN params`；行为表过滤用 scalar subquery `(SELECT … FROM params LIMIT 1)`。

## Agent 使用提示

- 问题含「每个渠道每个国家 + top20% + d30 arpu」→ 默认引用本 verified SQL（解释 A）。
- 必须输出 `install_time_window`、`behavior_dt_window`、`d30_maturity=full`、`revenue_source=da_behavior_ad_revenue`。
- 只预警、不输出停投/放量动作。
