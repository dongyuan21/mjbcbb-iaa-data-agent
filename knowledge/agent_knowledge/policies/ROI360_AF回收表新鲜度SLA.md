# ROI360 AF 回收表 freshness SLA

## 状态

| 项 | 内容 |
|---|---|
| knowledge_status | active |
| applies_to_current | true |
| confirmed_date | 2026-06-18 |
| confirmed_via | 用户确认的业务结论 |
| 适用表 | `shucang_market.tj_ad_revenue_v2` |

## 当前业务规则

`shucang_market.tj_ad_revenue_v2` 是 ROI360 的 AF 回收表。业务已确认该表允许 T-2 分区：

- 以 UTC0 的 `active_date` 判断。
- latest `active_date` 落后当前日期 2 天以内，视为正常到数。
- T-2 范围内不应触发 agent regression 的 freshness blocker。
- 请求日期大于 `latest active_date` 时仍按“数据未到”处理，不能把空分区当 0 或真实劣化。

## Agent 使用规则

1. 做 SDK / AF 回收差异、ROI360 AF 回收、`revenue_source=af` 对账时，先读取 `ai_ck/agent_knowledge/tables/tj_ad_revenue_v2.yaml` 的 freshness 配置。
2. 如果 `ai_ck/engineering_artifacts/freshness_snapshot.json` 显示该表 `status=fresh` 且 `partition_lag_days <= 2`，可以继续做成熟窗口和对账分析。
3. 如果该表超过 T-2、状态为 `delayed` / `stale` / `unknown`，只能标 `freshness_blocked` / `data_delay_suspected`，不能把 AF 回收下降当业务结论。
4. 本规则只改变该 AF 回收表的新鲜度 SLA，不改变 SDK / AF 指标口径，也不替业务决定默认 `revenue_source`。

## 工程落点

| 位置 | 要求 |
|---|---|
| `ai_ck/agent_knowledge/tables/tj_ad_revenue_v2.yaml` | `freshness.allowed_partition_lag_days: 2` |
| `tools/scripts/probe_freshness.py` | 使用 `allowed_partition_lag_days` 判断 `fresh` |
| `eval/agent_regression/run_regression.py` | 读取刷新后的 `ai_ck/engineering_artifacts/freshness_snapshot.json`，不把 T-2 内的 AF 回收表当 blocker |
| `da_assets/verified_sql/sdk_vs_af_revenue_by_cohort.md` | 输出时说明 AF 回收 T-2 freshness SLA |
