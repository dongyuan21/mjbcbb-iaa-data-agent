# Runtime SLA 证据通道

> 状态：`p0_local_observability_contract`
> 范围：只读汇总 Runtime durable execution 与 Freshness scheduled-run 的 MySQL 元数据；不修改任务，不查询业务数据。

## 目标

`GET /api/runtime/sla` 把 Runtime 可靠性底座转换为可查询、可判缺口的证据面。它回答：

- 最近时间窗内 durable async job 的状态、成功率样本和观测时延；
- queued / running / due outbox backlog 与 lease 状态；
- durable event 是否满足连续序号和 `answer → done` 终态协议；
- Freshness 定时任务最近状态、窗口内状态分布和重叠运行；
- 样本属于哪些持久化 runtime provenance；
- 哪些事实缺少 heartbeat、客户端回执或 owner 阈值，不能判成正常。

MySQL 是 job、enqueue outbox、lease、event history 和 scheduled-run 的权威。Redis 只是唤醒与传输层，本端点不把 Redis 当持久历史。MySQL 新连接固定为 UTC session，避免 server default 与应用写入时间错位；负时延不会压成 0，而会标记 `clock_skew_or_timezone_mismatch`。

## 调用与授权

这是全局运行态证据，不按普通业务用户隔离，因此当前只开放给：

- test / staging：allowlist 内的 machine HMAC；
- local / dev：machine HMAC 或本机 mock identity。

普通 SSO 用户返回 `403 runtime_sla_requires_ops_auth`。prod 的 machine auth 本来就被禁止，而当前又没有 operator/admin 角色，所以 prod 入口保持关闭；补齐 ops 角色前不得把普通 SSO 当替代授权。

```bash
# 仅 local/dev 本机 mock 调试
curl -sS \
  -H 'X-Data-Agent-User: local-operator' \
  'http://127.0.0.1:8000/api/runtime/sla?window_minutes=60' \
  | jq '{schema_version, observed_at, assessment, jobs, latency_ms, backlog, durability, scheduled_jobs}'
```

`window_minutes` 允许 `5..1440`，默认 `60`。单次最多采样 500 个 job、20,000 个 event；同时返回窗口 job 总数。超过上限时整体标为 `evidence_gap`，不得把采样计数误作总量。时间窗查询使用 `(created_at, id)` 索引，迁移为 `0012_runtime_sla_indexes`。

## 状态解释

| `assessment.status` | 含义 |
|---|---|
| `observed` | 所需证据可观测，且未发现确定的持久化不变量风险；**不等于 SLA PASS** |
| `evidence_gap` | heartbeat、provenance、样本或关键覆盖不完整；不得补齐为绿 |
| `risk_detected` | 至少一个确定的 durable evidence 风险存在 |

当前尚无独立 Worker heartbeat registry，因此即使队列空闲也会返回 `worker_liveness_unavailable_when_idle`；P0 本地实现不会用“无积压”证明 Worker 存活。`observed` 状态为 heartbeat 等证据补齐后的保留状态。

硬性风险包括：

- `enqueue_outbox_missing`
- `active_enqueue_outbox_missing`
- `expired_running_lease`
- `event_sequence_gap`
- `terminal_event_missing`
- `terminal_finished_at_missing`
- `published_outbox_timestamp_missing`
- `publishing_outbox_lease_missing`
- `latest_freshness_run_unsuccessful`
- `overlapping_freshness_runs`

关键 evidence gap 包括：

- 无 durable job、无 Freshness scheduled-run 证据，或所选窗口内没有 Freshness run；
- job、event、backlog 或 scheduled-run 采样截断；
- 有 active job 或 due outbox，但没有独立 Worker heartbeat registry；
- 队列空闲时也没有独立 Worker heartbeat registry，不能证明 Worker 存活；
- 无 enqueue outbox 且没有持久化 `execution_mode`，不能擅自归类为 inline；
- 样本 provenance unknown 或跨 build commit；
- 时间戳倒序或时区不一致。

`sampled_outbox_due_count`、最老 sampled backlog age、成功率和 P50/P95 只是观测值。所有受上限约束的 backlog / scheduled-run 计数均使用 `sampled_*` 命名，并显式返回 sample limit / truncated。仓库当前没有 owner 确认的数值型 SLO，因此响应固定输出 `numeric_slo_status=unconfigured`，并列出 availability、成功率、时延、heartbeat、Freshness 调度延迟、SSE delivery 与证据保留周期等未配置目标。

不得把候选阈值写成生产 SLA，也不得因 sample 为 0 就声称可用率 100%。

## Provenance 解释

- `observer_provenance`：生成本次快照的 API 进程，只代表观察者；
- `sample_runtime_provenance`：来自 job 持久化 metadata 的样本分组与计数。

发布切换期若样本跨 environment / build commit，返回 `mixed_runtime_provenance`；旧记录缺 provenance 返回 `sample_runtime_provenance_unknown`。当前观察者版本绝不覆盖样本归属。

## 安全边界

查询使用列裁剪，不加载 job 的问题、request payload、最终答案、error message 或 outbox payload；event 只读取元数据与 status stage。响应严禁输出：

- `job_id` / `session_id` / `user_id` / worker owner；
- 问题、答案、SQL、结果行、event payload；
- token、cookie、AK/SK、数据库密码、SSO ticket。

error code 采用受控 allowlist；任何未知值统一聚合为 `other`，不会因格式合法而原样返回。

## 离线验收

```bash
cd runtime/backend
uv run --extra dev pytest -q tests/test_runtime_sla.py tests/test_db_timezone.py
uv run --extra dev pytest -q
uv run --extra dev ruff check app/services/runtime_sla.py app/db.py \
  app/services/machine_auth.py tests/test_runtime_sla.py tests/test_db_timezone.py
```

覆盖：正常 durable sample、真实 machine HMAC、普通 SSO 拒绝、数据脱敏、error code allowlist、`answer → done`、outbox 缺失/卡死、lease/event 风险、Worker heartbeat 缺口、时钟倒序、混合 provenance、Freshness 失败/重叠、空窗口和 API 参数门禁。

## 后续 evidence gap

1. 增加 `claimed_at` / `last_heartbeat_at` 和独立 Worker heartbeat registry。
2. 持久化 `execution_mode`，区分 durable async 与 legacy inline，不再靠缺失 outbox 推断。
3. 增加客户端 SSE 接收/重连摘要；服务端 event 持久化不能代替客户端收到证据。
4. 增加 operator/admin 授权模型后再开放 prod 证据入口。
5. 基于真实观测基线，由 owner 确认 availability、latency、error budget 和证据保留周期。
6. 部署 smoke 新增 `/api/jobs → outbox → Worker → durable SSE` 路径，避免 API 绿但 Worker 死亡。
