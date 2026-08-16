# Runtime 主链直接收敛：GPT-Sol 最终红队复核包

> 复核对象：提交 `<提交标识>`（2026-08-10）
>
> 复核目的：审查一个开发态 Data Agent Runtime 是否已删除未治理 provider 调用路径，并把 provider 外部副作用与工具可见面收敛到可证明的 durable 主链。不是评审 E3 题目通过率、模型回答质量、Freshness 或生产发布。

## 请先接受的完整上下文

这是一个只读分析型 Data Agent。Runtime 有三个彼此独立的权威边界：

1. provider admission 只负责 token/resource liability；
2. L5 / `DataContractBinding` / SQL-PII guard 只负责工具执行授权；
3. P3 只负责业务证据覆盖与终态。

它们不能互相越权：预算结算不得写 P3 terminal，工具可见面不得成为 SQL 授权，P3 也不得绕过 provider admission。

provider 没有可信 callback、status lookup 或幂等键。因此本设计追求的是**不超卖 Runtime 预算、失去 lease 后不再有状态写权限**，不是 provider 账单精确对账，更不声称物理网络请求 exactly-once。

当前只有 Test 开发环境，没有 Production lane；允许删除历史兼容开关。E3、Freshness 的正常 Cron、L5/P3 授权规则和任何 SQL 失败阈值均不在此变更范围。

## 最终目标语义

任何真正发往 provider 的 Runtime 调用必须经过唯一链路：

```text
durable Worker + 当前有效 Job lease
  -> TurnBudget reserve
  -> Reservation ISSUED
  -> 单次 dispatch claim
  -> provider invocation（带 granted_max_output_tokens）
  -> actual settle 或 conservative settle
  -> ToolLoop 解释 ModelTurn
```

少 lease、reservation 或 dispatch claim 任一项时，不得调用 provider。没有 inline、SSE 或历史 `off/shadow` 回退。

每一次 provider invocation 还要生成一个仅内存、不可变的 `ProviderAttemptCapabilitySnapshot`：

```text
snapshot = {
  snapshot_id,
  allowed_tool_names,
  visible_tools_hash,
  binding_fence,
}
```

它的生命周期仅覆盖一次 provider response 及该 response 的 tool-call 解析：

```text
derive once -> render provider schema -> parse tool call -> Registry.require_allowed
```

`binding_fence` 只是 server-side ContractView binding 的有限摘要，用于识别陈旧 snapshot 并拒绝；它绝不是 Registry/L5 的授权 token。

## 已实现的改动

1. 删除 `DATA_AGENT_PROVIDER_ADMISSION_MODE`、`ProviderAdmissionMode`、`off`、`shadow` 及 D0 transport 分支。Runtime 若没有 `ProviderAdmissionContext(db, active JobLease, turn_id, cap)`，在 provider 前以 `provider_admission_denied` fail-closed。
2. `ProviderAdmissionExecutor` 是唯一 Runtime provider adapter：先 durable `reserve -> issue -> claim_provider_dispatch`，再调用模型；timeout、cancel、transport error、缺少或非法 usage 都走 conservative settlement。迟到 response 没有重新打开账本状态机的路径。
3. 真实 observation 改成实际字段：`reservation_created`、`issue_recorded`、`settlement_mode`、`settlement_reason`；不再用 D0 `would_*` 影子语义。安全投影只保留有限状态、reason 与计数，不保存 prompt、answer、SQL、rows 或 raw error。
4. `SETTLED_ACTUAL` 必须在同一 current owner、有效 lease、ISSUED reservation、dispatch row version 一致的线性化点完成。实际 output 超 `granted_max_output_tokens`，即使总 token 尚未超过 reservation，也会 `accounting_violation -> SETTLED_CONSERVATIVE -> DEGRADED_NO_ADMISSION`；后者只是禁止后续 provider admission 的资源状态，绝不定义 P3/业务终态。
5. 任何 `ISSUED` liability 不会直接释放回 available；只有 settled state 才会从 active liability 转成 settled Runtime consumption。预算 degraded 是 turn-level durable 状态，不是 Worker 本地 stop。
6. 每个 provider invocation 根据 server-side route/engine 静态范围、`runtime_resolved_sql_dependencies`、当前 `DataContractBinding` 和 recovery state 派生工具面。没有 binding 时 query 工具不进入 schema；多表依赖只读一张仍不可见 query；成功读取所需 ContractView 后才在下一次 provider invocation 展示 query。
7. 同一 snapshot 的 allowed tools 同时用于 provider schema、ToolLoop parser 和 `RuntimeToolRegistry.require_allowed`。snapshot stale 校验覆盖 route/engine 投影、schema hash、依赖、恢复状态与 binding；在模型返回后任一输入变化时，query 被 `capability_snapshot_stale` 拒绝，不能拿旧 snapshot 继续执行。真正 SQL 执行仍由 Registry/L5 重新按当前 binding、engine、SQL、PII 授权。
8. 旧 D0/D1/D2 文档保留为历史测试证据；当前行为的唯一规范是 `Runtime主链直接收敛改造方案.md`。

## 明确的非声明事项

- 不声称 provider 的物理网络请求 exactly-once；dispatch claim 只能保证 Runtime 不会对一个 immutable attempt 发起第二次受控 dispatch。crash/timeout 后一律将已 ISSUED liability 保守结算。
- 不新增 receipt inbox、callback、status lookup 或 billing reconciliation。
- 不将 ContractView binding fence 当授权能力；不放宽 L5、SQL/PII 或 P3。
- 普通 `MinimalToolLoop` 无 admission context 时在 ModelClient 前拒绝；纯内存 parser/tool 单测必须显式构造 `TestMinimalToolLoop`。API、SSE 与 Worker 仅构造普通类，因此缺 admission 不会退化为直接 provider 调用。
- Test 已部署并完成受控 durable admission canary：三服务同 `<提交标识>`、migration head 为 `0024_runtime_admission_ledger`、default model 为 `qwen3.7-max`，一条无工具/无 SQL provider call 为 `settled_actual`。未运行 E3，未手工触发或修改 Freshness Cron。

## 已执行的本地验证

均使用 `runtime/backend/.venv/bin/python`（Python 3.12），不访问真实 provider、仓库外数据库或 Test 环境：

```text
test_runtime_admission_d1.py + test_runtime_admission_d2.py                 26 passed
test_minimal_tool_loop.py                                                    41 passed
test_runtime_mainline.py                                                     42 passed
test_runtime_admission_d1.py + D2 + durable + P3 + deploy-smoke tests       67 passed
targeted capability snapshot + D2 tests                                      3 passed
ruff --select F,I (changed Runtime/test/script files)                         passed
py_compile (changed Runtime/script files)                                    passed
git diff --check                                                             passed
```

覆盖的关键反例包括：预算 CAS 竞争、lease takeover、旧 owner actual/conservative settlement 失败、late response observation-only、超 reservation/超 grant output 进入 degraded、单 dispatch claim、无 lease 时 provider call count 为零、多表 ContractView、binding 变化后的 stale snapshot 拒绝、P3 wait/resume、timeout 的 conservative observation、durable worker/local API 边界与 smoke 输出的安全投影。

## 请做的独立红队审查

请审阅本复核包及随附完整 diff（`git show <提交标识>`）。不要把“没有 E3 结果”当作此变更缺陷；也不要建议为兼容历史 Test 配置恢复 `off/shadow` 分支。

重点逐项判断：

1. 是否仍存在任何 Runtime/API/SSE/Worker 生产调用能绕开 lease + reservation + dispatch claim 而调用 provider？
2. `ISSUED` 后 crash、timeout、takeover、late response 的状态转换是否有 release liability、重发同一 attempt、或旧 owner mutation 的漏洞？
3. `SETTLED_ACTUAL` 的线性化条件和超 grant 处理是否足够严格？
4. snapshot 是否真的把一次 provider invocation 的 schema、parser 与 Registry allowlist 固定在同一事实边界？binding 变化时是否只会收缩或拒绝？
5. 是否有任何地方把 snapshot/fence/route 当作 SQL 授权，而不是让 Registry/L5 重新验证？
6. 纯测试用的 direct `ModelClient` seam 是否能从真实 Runtime 调用图到达？若不能，现有隔离说明与测试是否足够；若能，请按 P0/P1 标出路径。
7. 是否有实现把 admission/settlement 错误地转换为 P3 terminal 或业务回答终态？
8. 是否存在明显的过度设计、冗余状态机或不必要兼容层？如果有，请给出最小删除/收缩建议。

请以如下格式返回：

```text
Verdict: Accept / Accept with constraints / Reject

P0/P1（如有）：文件、精确路径、可复现反例、最小修复。
P2：只列会造成后续语义漂移或测试假绿的事项。
已验证的关键边界：逐项确认或明确无法从 diff 验证。
不要建议：E3 特化、放宽 L5/P3、提高失败阈值、恢复 shadow/off 兼容分支、receipt inbox/reconciliation。
```
