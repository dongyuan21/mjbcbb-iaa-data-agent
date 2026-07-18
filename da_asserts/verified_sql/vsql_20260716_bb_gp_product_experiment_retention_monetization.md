# BB GP 商业化方案 fs217631 vs fs217632 D0/RR1/时长/局数/广告收入对比

## 元信息

| 项 | 内容 |
|---|---|
| ID | vsql_20260716_bb_gp_product_experiment_retention_monetization |
| 状态 | verified |
| promotion_status | verified_sql |
| sql_status | verified |
| last_validated_at | 2026-07-16 |
| validation_method | automated_regression |
| owner | Data Agent Runtime |
| 源 | PI replay pass run session `91fb8c14-3a70-4d25-8f4a-df47cb374bb2` |

## 口径说明

- 时间口径：快照分区 `dt=2026-06-22 / hour=23`，install_date 窗口 `2026-06-20 ~ 2026-06-21`，retention_days `IN (0,1)`。
- 维度：按 `user_waynum` 方案号聚合（fs217631 vs fs217632）。
- 指标：D0 分母 = `COUNT(DISTINCT distinct_id) WHERE retention_days=0`；RR1 分子 = `COUNT(DISTINCT distinct_id) WHERE retention_days=1`；D0 人均时长/局数/广告收入以 D0 样本为分母。
- 过滤条件：`dt / hour / app_name / channel / install_date / user_waynum / retention_days` 全部显式声明，WHERE 只用 AND 连接字面量等值或 IN。

## 依赖表

- `h-s.dws_kcolb_tsalb_all_ad_realization_active_user_ab_life_orthogonal_retention_hi`（BB 商业化实验用户生命周期宽表）

## SQL

```sql
SELECT
  user_waynum,
  install_date,
  COUNT(DISTINCT CASE WHEN retention_days = 0 THEN distinct_id END) AS d0_users,
  COUNT(DISTINCT CASE WHEN retention_days = 1 THEN distinct_id END) AS d1_users,
  SUM(CASE WHEN retention_days = 0 THEN usage_duration ELSE 0 END) AS d0_usage_duration,
  SUM(CASE WHEN retention_days = 0 THEN game_cnt ELSE 0 END) AS d0_game_cnt,
  SUM(CASE WHEN retention_days = 0 THEN ad_revenue ELSE 0 END) AS d0_ad_revenue
FROM h-s.dws_kcolb_tsalb_all_ad_realization_active_user_ab_life_orthogonal_retention_hi
WHERE dt = '${dt}'
  AND hour = '${hour}'
  AND app_name = '${app_name}'
  AND channel = '${channel}'
  AND install_date IN (${install_dates})
  AND user_waynum IN (${user_waynums})
  AND retention_days IN (0,1)
GROUP BY user_waynum, install_date
LIMIT 1000
```

## 风险与陷阱

- `distinct_id` 是 PII 字段，只能用于 `COUNT(DISTINCT)` 聚合，禁止 `SELECT distinct_id` 明细输出。
- RR1 窗口（retention_days=1）需 D1 快照已成熟；未成熟时标 `blocked` / `evidence_gap`。
- 不把任一方案臆称 holdout；无配置证据时只称方案组。
- 多指标只读证据用于 `needs_decision`，不代替 owner 下推全或下线决定。

## 验证记录

- 2026-07-16：PI replay N=3 pass run（session `91fb8c14`）使用此 SQL 形态成功返回 fs217631 / fs217632 两个方案的 D0 分母、RR1、人均时长、人均局数、广告收入和人均广告收入。
- 失败 run（session `6bd54645` / `fd16890e`）根因：LLM 首条 SQL `SELECT distinct_id` 被pii_blocked，虽后续重试写出正确聚合 SQL，但 failed 记录未被自愈覆盖，触发 `intermediate_sql_failed`。
