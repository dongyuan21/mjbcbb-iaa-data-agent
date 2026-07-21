# ROI 预测准确性表 freshness SLA

## 状态

| 项 | 内容 |
|---|---|
| knowledge_status | active |
| applies_to_current | true |
| confirmed_date | 2026-06-18 |
| confirmed_via | 用户确认的业务结论 |
| 适用表 | `hungry_studio.ads_market_roi_pred_accuracy_da` |

## 当前业务规则

`hungry_studio.ads_market_roi_pred_accuracy_da` 是 ROI 预测准确性评估表。业务已确认该表允许 T-2 分区：

- 以 Asia/Shanghai 业务日判断。
- `latest dt` 落后当前业务日 2 天以内，视为正常到数。
- T-2 范围内不应触发 agent regression 的 freshness blocker。
- 请求日期大于 `latest dt` 时仍按“数据未到”处理，不能把空分区当 0 或真实劣化。

## Agent 使用规则

1. 做 ROI 预测偏差、预测准确性、D3/D7 到 D60/D90/D180 对比时，先读取 `ai_hive/agent_knowledge/tables/ads_market_roi_pred_accuracy_da.yaml` 的 `freshness.allowed_partition_lag_days`。
2. 如果 `ai_hive/engineering_artifacts/freshness_snapshot.json` 显示该表 `status=fresh` 且 `partition_lag_days <= 2`，可以继续使用成熟窗口做分析。
3. 如果该表超过 T-2、状态为 `unknown`，或 MaxCompute 读取能力未验证，只能标 `freshness_blocked` / `connectivity_unverified`。
4. 本规则只改变该表的新鲜度 SLA，不改变 ROI 预测指标口径，也不替业务判断模型优劣或投放动作。

## 工程落点

| 位置 | 要求 |
|---|---|
| `ai_hive/agent_knowledge/tables/ads_market_roi_pred_accuracy_da.yaml` | `freshness.allowed_partition_lag_days: 2`，`freshness_timezone: Asia/Shanghai` |
| `tools/scripts/probe_freshness.py` | 使用 `allowed_partition_lag_days` 判断 `fresh` |
| `eval/agent_regression/run_regression.py` | 读取刷新后的 `ai_hive/engineering_artifacts/freshness_snapshot.json`，不再把 T-2 内状态当 blocker |
| `da_assets/verified_sql/roi_prediction_accuracy_snapshot.md` | 输出时说明 T-2 freshness SLA |
