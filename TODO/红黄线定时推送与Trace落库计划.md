# 红黄线定时推送与 Trace 落库待办

- 状态：`code_scaffold_complete / product_decision_and_live_validation_pending`
- 更新：2026-08-02
- 关联：`task_routes/redline_bidaily_review.yaml`、`tools/scripts/run_redline_bidaily_review.py`、`tools/runbooks/红黄线ROI双日review.md`
- 边界：只预警，输出 `threshold_status / trial / needs_decision`；不自动停投、放量或改预算。

## 已有基线

- 数据脚本可生成 xlsx、CSV、Markdown 和 JSON。
- `scheduled_job_runs` migration/model 和写入 helper 已存在。
- `redline_headless_summary.py` 提供确定性摘要 helper，不依赖已退役的 Runtime 主链。
- DingTalk delivery helper、mock 测试、CronJob 样板、shell runner 和归档 runbook 已存在。

这些只证明代码/样板存在，不证明山海调度、真实 MySQL、真实钉钉或连续运行已经通过。

## P0 · 产品拍板

- [ ] 频率：每日 15:00 还是隔日；统一 `daily` / `bidaily` 命名。
- [ ] 接收方：群机器人、企业应用或文档链接；是否需要 @ 指定人。
- [ ] 附件范围：全量 campaign 命中、Top N，或包体/组合级结果。
- [ ] 摘要方式：推荐先用确定性模板；只有明确需要自由文本时才接 Runtime，并单独验收证据/terminal。
- [ ] 失败策略：重试次数、告警对象、同日重复跑的幂等键和 latest 指针规则。

## P0 · 真实接线

- [ ] 在目标环境配置 CronJob/调度器、Secret/ConfigMap、时区、超时和只读网络权限。
- [ ] 用真实 MySQL 验证 `scheduled_job_runs` 从 running 到 success/partial/failed，artifact、trace 和 delivery 可对账。
- [ ] 接入真实钉钉发送和 CSV/链接交付；`DATA_AGENT_DINGTALK_MOCK=false` 只在获准环境启用。
- [ ] 失败必须写稳定 error code 并告警，不静默、不在日志泄露 webhook/token。
- [ ] system job 只能被运维/授权身份查询，不进入普通用户 session 列表。

## P1 · 验收与运营

- [ ] 连续 3 天按计划触发，成功率、延迟、产物、MySQL run 和钉钉消息逐日可对账。
- [ ] 同日重跑不覆盖历史证据；latest 只作便捷指针。
- [ ] 对 0 命中、数据 stale、MI/CK 失败、钉钉失败和部分成功分别验证。
- [ ] 固定 owner、值班/告警通道、回滚和停用开关。

## 完成定义

- 产品参数已拍板并写入配置/运行手册，不靠文档默认猜测。
- 真实环境连续 3 天有调度、数据、产物、trace、delivery 和失败演练证据。
- 推送内容始终是只读预警，任何投放动作仍由人工决定。
