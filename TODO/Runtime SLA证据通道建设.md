# Runtime SLA 证据通道建设

> 状态：`p0_local_implemented_live_evidence_pending`
> 权威入口：`runtime/Runtime SLA证据通道.md`（端点、证据字段、边界以该文为准）
> 更新：2026-07-25（P0 本地实现不再在本 TODO 复述）

## 已完成

P0 本地已落地：`GET /api/runtime/sla`（ops-only / machine HMAC）、job/outbox/lease/event/Freshness 元数据聚合、`evidence_gap` / fail-closed、UTC session、敏感字段裁剪、`numeric_slo_status=unconfigured`。详见权威入口与 `runtime/backend/tests/test_runtime_sla.py`。

## 仍开

- [ ] shared test 用 machine auth 读一次真实窗口，只存元数据结果
- [ ] MySQL 双连接 claim / lease / fencing 与 UTC session 验收（SQLite 不代替）
- [ ] Worker heartbeat registry（`claimed_at` / `last_heartbeat_at`）
- [ ] 持久化 job `execution_mode`，消除 legacy inline / missing outbox 分类缺口
- [ ] operator/admin 授权模型后再开放 prod 证据入口
- [ ] 客户端 SSE delivery/reconnect 证据 + 真浏览器刷新/切网人工验收
- [ ] `runtime_deploy_smoke.py` 走 durable async worker 路径
- [ ] owner / SRE 确认 availability、P95/P99、error budget、证据保留周期

## 边界

只保障只读分析、证据完整性、故障定位与长任务恢复；不含自动投放写操作。未配置数值型 SLO 时，`observed` ≠ SLA PASS。
