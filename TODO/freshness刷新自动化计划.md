# freshness 自动刷新计划（MC + CK）

> 工程链路已落地，见 `tools/runbooks/新鲜度刷新流水线.md`。  
> 历史记录称本机 CK cron 6h 已装（`cron_freshness_6h.sh`）；本轮受系统权限限制无法读取 `crontab -l`，当前 OS 注册状态记为 `local_cron_unverified`。
> 更新：2026-08-02

## 固定链路（现阶段）

评估当前窗口前必须实时探测，**不复用旧 snapshot**：

1. **连通先行**
   - MaxCompute：`maxcompute-dataworks` 执行 `SELECT 1` + 目标表轻量 `max(dt)` / `max(active_date)` probe
   - ClickHouse：`source ~/.clickhouse_env.zsh` 后 `SELECT 1` + 轻量分区 probe
2. **刷新快照**：`python3 tools/scripts/probe_freshness.py`（或 `refresh_freshness_pipeline.py --mode full`）  
   全量刷新要求 MC/CK 同一 `run_id` / `started_at`；单源 `--source` 不能证明全局当前
3. **分流**：`mixed_epoch` / `freshness-blocked` / `connectivity_unverified` 显式降级，不伪造当前窗口结论

## 已完成（不再当待办）

- `probe_freshness.py`、`refresh_freshness_pipeline.py`、`refresh_ai_ck.sh`、`refresh_ai_ck_freshness_runner.sh`
- `check_freshness_health.py`、看板 JSON、`append_freshness_trend.py` → trend JSONL
- 本机 `cron_freshness_6h.sh`（含健康检查 + 告警阈值 env）
- runbook：`tools/runbooks/新鲜度刷新流水线.md`、`ClickHouse连通与新鲜度探测.md`

## 仍开（运维 / 宿主）

| 项 | 状态 | 缺口 |
|---|---|---|
| 共享稳定环境定时 | open | 本机 cron 已有；共享/CI 宿主是否装、周期 1–2h 还是 6h，待运维确认 |
| 告警通道 | blocked | 脚本侧告警已接；需运维 Webhook / 告警栈 |
| 过期硬门 | blocked | warning→CI fail 待宿主环境确认（见工具建设待办） |
| MC 定时全链路 | open | 当前定时偏 CK-only；MC 全量仍按需手动 / full pipeline |
| 3 日验收留证 | open | CK runner 连续 3 日成功率 ≥95% 的归档证据未正式收口 |

## 验收（仍适用）

- 共享环境连续 3 日刷新成功率 ≥95%，且无需手改 `freshness_snapshot.json`
- 当前窗口评估前能拿到可追踪的两源 freshness；阻断在报告中可见可复现
