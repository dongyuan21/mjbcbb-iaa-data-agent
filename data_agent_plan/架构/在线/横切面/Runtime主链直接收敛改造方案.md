# Runtime 主链直接收敛改造方案（开发态评审稿）

> 状态：`independent_reviewed / implemented_locally / verification_passed / Test_deployed_and_smoked`
>
> 日期：2026-08-10
>
> 适用环境：当前仅有 Test 开发环境；不存在 Production lane，也不要求兼容历史 Runtime 行为或历史配置。
>
> 评审目标：判断此方案是否以最小实现，把 provider 准入、工具可见面和合同绑定收敛为一条可证明的主链；不是评审 E3 题目通过率。

## 1. 一页结论

建议停止把 `D0`、`D1`、`D2`、`D3` 等验证切片继续当作长期项目阶段。它们已完成的部分只保留为设计与测试证据。

> 实施记录（2026-08-10）：本方案的本地代码收敛与定向性质回归已完成，并已部署至 Test。验证覆盖 admission D1/D2、ToolLoop capability、Runtime 主链、P3/durable 边界与 deployment smoke；未运行 E3，未手工触发 Freshness。

下一次代码改动应直接收敛为最终开发态：

```text
durable Worker + 有效 Job lease
        ↓
强制 provider admission（reserve → issue → dispatch → settle）
        ↓
服务端依当前合同 / binding / recovery 状态投影允许工具
        ↓
Provider 只能看见该投影；Registry 只能执行该投影
        ↓
L5 执行授权与 P3 业务终态继续独立拥有最终权威
```

这里不新增一个“阶段状态机”，不增加 provider callback、receipt inbox、自动 reconcile 或新 workflow engine。
“当前阶段”是由当前 turn 的已验证事实**纯派生**出来的工具集合，不是模型自报、也不是持久化的业务状态。
每一次 provider 调用只使用一个 attempt-local、不可变的 `ProviderAttemptCapabilitySnapshot`；schema、parser、Registry 和 hint 不得在该调用中分别重算。

## 1.1 独立审查已冻结的三条不变量

1. **Provider 外部副作用不变量**：每一次 provider side effect 必须同时有有效 Job lease、reservation 和单次 dispatch claim；缺少任一项即为 bug，不存在旧调用回退。
2. **能力单调性**：binding/evidence/lease/预算事实变差时能力只能缩小；再次展示 query 必须由当前事实重新证明，不能因过去曾允许而保留。
3. **投影不是授权**：`allowed_tools` 只能缩小模型可见/Loop 可接受的集合，永远不能授予执行权限。Registry 与 L5 必须独立重新验证。

独立审查补充并冻结：snapshot 的一致性边界是**一次 provider invocation / immutable attempt**，不是整个 durable turn；
`capability_fence` 由 route/engine 可见面、schema hash、依赖、恢复状态与 binding 的有限摘要共同导出，用于一致性检测或拒绝陈旧 snapshot。它和其中的 `binding_fence` 都绝不能成为 Registry/L5 的授权 token。

## 2. 当前事实与问题边界

### 已完成且保留的底座

- `runtime_admission` 已有 durable `TurnBudget`、`ProviderCallReservation`、lease fencing、单次 dispatch claim 和保守结算；它不驱动 P3 终态。
- `MinimalToolLoop` 已接入 provider 调用边界；D2 Test canary 已证明一次无工具、无 SQL 调用可写入并 `settled_actual`，随后恢复 `shadow` 的 D0 调用证明账本为零。
- 普通 `MinimalToolLoop` 缺少 `ProviderAdmissionContext` 时会在模型 RPC 前拒绝；只有显式命名的 `TestMinimalToolLoop` 可用于纯内存 parser/tool 单测，且 API、SSE、Worker 均不构造它。
- `ToolExecutionContext.data_contract_bindings` 只由成功的 `read_data_contract_view` 写入，仍是 SQL 查询授权的唯一服务端来源。
- Registry 的 `require_allowed` 已能拒绝模型伪造的未允许工具名。

### 仍不应保留的开发态复杂度

1. provider 准入同时存在 `off`、`shadow`、`enforce` 三种日常运行分支；这对当前纯开发/Test 环境形成了旧路径与测试兼容负担。
2. route 级工具白名单与合同绑定恢复逻辑分散，容易让模型在未读全量合同或失败恢复时仍看见 query 工具。
3. 同一个安全规则可能同时由 prompt、ToolLoop、Registry 和 L5 表达；最终应以服务端允许工具集合和 Registry 拒绝为准，prompt 只解释原因。

### 明确不处理的事项

- 不修改 E3 题集、E3 阈值、失败次数、授权策略或模型提示词来“过题”。
- 不把 provider 预算结算写成 provider 最终账单系统；不引入 callback/status lookup/reconciliation。
- 不修改 L5 的 DataContractBinding/L5/PII 授权语义，不让 `read_verified_sql` 自身变成查询授权。
- 不让 reservation/settlement 写 Runtime 业务终态或 P3 terminal。
- 不触发、暂停、删除或利用 Freshness Cron；数据发布和 `mc_governed` 正常 Cron 证据独立处理。

## 3. 目标运行语义

### 3.1 Provider 调用只有一条正常路径

在最终开发态，任何会发出 provider 请求的 Runtime turn 必须同时满足：

1. 由 durable Worker 执行；
2. 持有尚未失效的 Job lease；
3. 已按当前 turn budget 成功 `reserve → issue → claim_provider_dispatch`；
4. provider 返回后只能在当前 permit、lease 与 reservation row version 一致时 actual settle；其他不确定结果保守结算；
5. settlement 只改变资源事实，不改变工具授权和 P3 业务终态。

不满足上述条件时 fail-closed；没有“沿用旧 provider 调用”的回退。

推荐移除运行时 `DATA_AGENT_PROVIDER_ADMISSION_MODE=off|shadow|enforce` 的兼容选择：

- `enforce` 成为 durable provider 调用的唯一正常实现；
- 过去的 `shadow` 只作为历史 D0 证据，不再是线上/测试服务的日常分支；需要实验时使用本地 fake provider 测试，而不是保留一条真实 transport 的未记账路径；
- `off` 删除；
- 既有账本表保留为当前真实记录，不做旧语义翻译或兼容读取。

这是开发态取舍：目标是一个更小、可证明的执行路径，而非面向既有客户的无停机迁移。

### 3.2 工具可见面由已验证事实纯派生

新增或收敛一个唯一的服务端函数，概念上为：

```text
allowed_tools = derive_allowed_tools(
    route_task_id,
    question_contract,
    runtime_resolved_sql_dependencies,
    data_contract_bindings,
    latest_typed_outcome,
    engine_enablement,
)
```

输入都来自 Runtime 已验证状态：route 只是候选范围，`runtime_resolved_sql_dependencies` 来自服务端已验证 asset metadata，
`data_contract_bindings` 来自成功的合同读取 receipt；不得接受模型提供的表名、asset id 或“已读合同”声明。

`runtime_resolved_sql_dependencies` 的名字刻意不含 `verified` 或 `authorized`：它不是模型从 SQL 文本声明的表名，
而是 Runtime 对已验证 asset metadata 解析出的物理表依赖；它仅描述依赖，
不是 query 授权。授权仍要求该依赖逐表具备当前 engine、revision、receipt 的 `DataContractBinding`，并在执行时通过 Registry/L5。

该函数不保存 `DISCOVERY/CONTRACT/EXECUTION` 等状态枚举。它只返回当前可以暴露给模型、并能由 Registry 执行的工具名。

### 3.2 ProviderAttemptCapabilitySnapshot：一次 provider 调用的一致性边界

在每次 provider 调用开始、最终 payload 已物化且尚未渲染 tool schema 时，Runtime 只调用一次 `derive_allowed_tools`，
生成内存内不可变的概念对象：

```text
ProviderAttemptCapabilitySnapshot {
  snapshot_id              # opaque / turn-local
  allowed_tool_names       # 有序、不可变
  visible_tools_hash       # 与 admission ticket 绑定
  binding_fence            # 当前 binding 的有限 revision/receipt 摘要；不是授权 token
  route_and_engine_scope   # 服务端 route/engine 范围
  capability_fence         # 上述可见面、依赖、恢复状态与 binding 的有限摘要
}
```

它的生命周期只覆盖**这一次 provider invocation 的响应及其紧随的工具调用解析**：

```text
derive once → render provider schema → parse tool call → Registry.require_allowed
```

- parser 和 Registry 都消费同一个 `snapshot.allowed_tool_names`，不得在 provider streaming 或工具调用到达时重新 derive；
- 一个 durable turn 内可能有多次 `provider → tool → provider`；每次 provider invocation 都必须创建新 snapshot，因此前一工具执行写入的新 binding 只会影响下一次 provider invocation；
- snapshot 不是持久化表、不是业务 FSM、不是授权 receipt，也不跨 Worker/lease 复用；
- Registry/L5 在真正执行时仍以当前 server-side binding、engine、SQL 和 PII 规则独立校验。query 在解析后、执行前会重新计算 `capability_fence`；route/engine scope、schema、依赖、恢复状态或 binding 任一变化都只能拒绝该旧 snapshot。`capability_fence` 与 `binding_fence` 都不能代替这些授权检查；若 snapshot 生成后事实失效，结果只能被拒绝，不能因此扩大能力。

这保证“模型看到什么、parser 接受什么、Registry 的 allowlist 接受什么”在一次 provider 调用内是一致快照；
同时避免把动态事实变化误当作可以绕过 L5 的授权。

| 已验证事实 | 可见能力 | query 工具 |
|---|---|---|
| 没有可执行 SQL/物理表依赖 | 知识、目录、合同发现等只读能力 | 不可见 |
| 已确定 verified SQL 或物理表，但任一目标表缺有效 binding | `read_data_contract_view` 与有限恢复能力 | 不可见 |
| 全部物理表均有当前 engine/revision/receipt binding | 对应受 route/engine 限制的 query 工具 | 可见 |
| query 因 binding/evidence 类错误失败 | 结构化 `recovery_required`，仅露出合同恢复能力 | 隐藏直至重新满足完整 binding |
| lease 失效、预算拒绝、L5 拒绝或 P3 wait | 由各自权威边界处理 | 不因本函数放宽 |

多表 SQL 必须逐表满足 binding；读完一张表不能解除另一张未读表的 query 隐藏。

### 3.3 唯一执行面

同一个 `ProviderAttemptCapabilitySnapshot.allowed_tool_names` 必须同时供给：

1. provider schema 渲染；
2. 模型工具调用解析；
3. `RuntimeToolRegistry.require_allowed`；
4. tool hint 只能解释 ContractView 前置条件，不能声明当前 query 已被允许，也不能独立决定可见面。

因此“模型没看见”与“模型伪造调用”都不会产生不同授权结果；后者一律 `tool_not_allowed`。
工具投影永远不是执行授权：snapshot 可删除能力，但不能替代 `RuntimeToolRegistry` 的执行检查或 L5 的 SQL/PII/合同授权。

### 3.3 能力单调性规则

工具投影在不确定性下必须单调收缩。对同一 Runtime 可验证事实，若新事实相较旧事实减少、失效或无法确认：

```text
capabilities(new) ⊆ capabilities(old)
```

例如 binding 缺失、binding revision 失效、lease 丢失、预算拒绝或 evidence recovery 失败，只能隐藏 query 或拒绝后续 provider admission。
旧 snapshot 曾展示 query 不是恢复能力的依据；必须以新的 provider invocation 重新派生并重新证明事实。

`runtime_source_policy.runtime_visible_tool_names` 只继续回答 route/engine 的静态候选范围；它不得单独决定某个 query 在当前 turn 可见。

## 4. 最小实现范围

| 区域 | 直接改动 | 不做的兼容工作 |
|---|---|---|
| `app/config.py` 与部署变量 | 移除 provider admission 三态的日常分支；durable 调用固定 enforce | 不迁移旧 `off/shadow` 配置值，不保留回退 |
| `app/services/minimal_tool_loop.py` | 只保留受 lease + admission permit 包裹的 provider 路径；在每轮用唯一工具投影渲染 schema 与执行白名单 | 不让 inline 或旧 Loop 继续无账本调用 provider |
| `app/services/runtime_admission.py` | 保留现有 reservation/settlement FSM 与 fencing；明确 `ISSUED` 代表“外部执行可能已发生”，以 dispatch-claim metadata/settlement reason 表达，不新增数据库状态 | 不增加 UNKNOWN、receipt、callback 或 reconcile FSM |
| `app/services/runtime_source_policy.py` / `runtime_tool_registry.py` | 将 route/engine 静态候选与 attempt 级合同投影合并为单一入口；引入内存内 `ProviderAttemptCapabilitySnapshot` | 不扩大 route 白名单或放松 L5 |
| `app/services/agent.py` | tool hints、provider schema、parser 都消费同一 snapshot，说明恢复步骤但不授予权限 | 不靠 prompt 强迫模型选择正确工具 |
| 测试与部署脚本 | 删除对旧模式的兼容断言，新增最终主链不变量 | 不把 E3 case 写入 unit test |

数据库 schema 不需要为“兼容”新增 migration。已有 `0024_runtime_admission_ledger` 继续作为全新 Test 数据库的唯一初始化事实；
历史 Test 账本只保留审计意义，不参与新路径的语义迁移。

## 5. 必须通过的本地证明

### Provider 准入

1. durable Worker 正常调用：`RESERVED → ISSUED → dispatch claim → SETTLED_ACTUAL`，一次 attempt 至多一次 dispatch。
2. 失 lease、permit mismatch、provider timeout、取消、Worker takeover：旧 owner 不能发 provider、不能写账、不能推进 ToolLoop 或 P3；`ISSUED` 责任只会保守结算。
3. 同一 turn 多次调用：下一次 grant 使用已结算消耗与未结算 liability，不超 cap。
4. 普通 `MinimalToolLoop` 缺 admission 时必须在调用 ModelClient 前拒绝；纯内存测试只能显式构造 `TestMinimalToolLoop`，不再存在隐式 test seam。
5. 静态调用图/文本门禁证明 API、SSE、Worker 只构造普通 `MinimalToolLoop`，provider transport 只由 `MinimalToolLoop → Admission → Provider` 触发；不得保留 `agent.py` 或其他旁路直接调用 provider。

### 工具投影与授权

1. 初始 schema 没有 query 工具；伪造 query 调用被 Registry 拒绝。
2. verified SQL 的多表依赖中，仅绑定一表仍没有 query；读齐全部合同后才出现正确 engine 的 query。
3. binding/evidence 类 query 失败后，下一轮 schema 不含原 query，只含恢复工具；完成恢复后才重开。
4. L5 仍拒绝未绑定、错误 engine、过期 revision、PII 或不被允许的 SQL；工具投影不能成为授权绕过。
5. settlement 不能写 P3 terminal；P3 wait/resume 不能跳过 provider/工具约束。
6. 对同一 provider 响应，schema、parser 与 Registry 使用同一 snapshot；route/engine scope、依赖、恢复状态或 binding 在该响应期间变化时，旧 snapshot 的 query 必须拒绝，不能产生 schema/执行不一致的放行。
7. 旧 snapshot 曾允许 query、随后 binding 被撤销或失效时，旧 snapshot 的执行必须被 Registry/L5 拒绝；snapshot 不能成为能力缓存。

### 质量与安全

- provider payload、trace、QueryRecord、账本只保存既有允许的计数、有限状态、工具名和 reason code；不得新增 prompt、answer、SQL、rows、raw error 或 provider payload。
- `DEGRADED_NO_ADMISSION` 只是 durable Runtime 资源状态：它禁止后续 provider external effect，不定义 Job/turn/P3 的业务成功或失败，也不得写入 P3 terminal。
- admission observation 固定为白名单投影：仅 enum、计数、opaque id、时间戳和有限 reason code；不得扩展为 provider error、模型响应摘要、工具参数预览或其他 payload-derived 字段。
- 测试同时覆盖 provider schema 与实际执行拒绝，不能只测提示词文本。
- `ruff`、相关 pytest、alembic ledger 与 `git diff --check` 通过。

## 6. Test 验收（不等于 E3）

代码本地证明通过后，Test 仅验证两类主链事实：

1. **无工具、无 SQL 的 durable provider 调用**：必须写 admission ledger 且成功结算；
2. **合同/查询负向路径**：不完整 binding 时不出现 query schema、伪造 query 仍被拒绝。

真实业务 SQL 正向查询不是本方案的启用前置。它必须等待目标表的正常 Freshness publication，且单独记录 freshness、绑定和 QueryRecord 安全证据。

不运行 E3；不把以上 Test 结果描述为 E3 改善或业务质量通过。

## 7. 实施顺序

1. 先删除/收敛 provider mode 与旧直接调用路径；把现有 D2 enforce 设为唯一 durable 路径。
2. 抽出唯一 turn-level `derive_allowed_tools` 投影，并替换 schema、parser、Registry/hint 的分散决定点。
3. 删除旧兼容测试，补第 5 节的主链负向/多表/失 lease 回归。
4. 本地完整验证后，只部署 Worker → API；Freshness 不属于本改造部署对象。
5. 跑第 6 节的两条 Test 验收；失败即修主链，不通过调 E3 阈值、题集或授权来掩盖。

## 8. 请独立审查者重点判断的问题

1. 将 durable provider 调用固定为 enforce、删除 `off/shadow` 日常分支，是否遗漏了仍必须保留的正确性或安全边界？若保留 shadow，应证明它不是旧路径兼容负担。
2. `ProviderAttemptCapabilitySnapshot` 是否正确解决一次 provider 调用内 schema/parser/Registry 的一致性，而没有演变为持久化 workflow state？其失效或 binding 变化时是否只能 fail-closed？
3. `derive_allowed_tools` 的输入是否都由服务端可验证事实提供？是否存在模型可伪造的 asset/FQN/binding 输入？
4. route/engine 静态候选、turn-level binding 投影、Registry 拒绝三层是否会产生授权不一致？“投影只能缩小能力、不能授予权限”是否足够明确？
5. 多表/多 engine、binding 失败恢复、lease loss、预算拒绝时，是否有任何 query 或 provider 调用绕过点？
6. 删除运行时 mode 后，哪些测试必须保留为 durable external-effect 的性质证明，哪些只是历史兼容测试应删除？该方案是否错误地把工具投影、预算账本或 provider settlement 变成 workflow/P3 authority？

## 9. 成功定义

成功不是 E3 分数上升，而是代码只存在一条受约束的 durable provider 主链，且对同一已验证状态：

```text
provider 能看见的工具
= ToolLoop 接受的工具
= Registry 可执行的工具
```

并且任何 provider 外部副作用均有当前 lease、单次 permit 和 reservation 结算事实。E3 之后只能作为该主链的独立质量评估，不能反向改变安全边界。

## 10. Test 发布验收记录（2026-08-10）

本记录只说明 Runtime 主链与部署事实，不代表 E3 质量通过，也不把手工操作冒充为 Freshness 正常 Cron 证据。

- 目标提交：`<提交标识>`，已安全快进至 Test 三服务绑定的 `main`。
- 分析平台任务：Worker `44672`、API `44673`、Freshness `44675` 均成功；三环境 `811/862/874` 的 `current_version` 与镜像 tag 均为 `<提交标识>`。
- API `/health`、`/readyz` 正常；数据库 migration 的当前/唯一 head 均为 `0024_runtime_admission_ledger`；安全 preflight 显示 default model 为 `qwen3.7-max`。
- 受控 machine-auth durable canary：单 job `done`、`runtime_worker`、`durable_async_worker`、一次 worker claim；一条 TurnBudget、一条 Reservation，`settled_actual`，零工具审计记录、零 SQL 记录。只保存有限状态和计数，不保存问题、回答、SQL、rows 或 raw error。
- Freshness 服务的发布任务完成；MySQL 最新 `freshness_ck_only` 受控 run 为 `success`、`active_slot=null`、`age_state=terminal`，最新 `ck_only` publication 为 `published`。未手工触发 Cron。
