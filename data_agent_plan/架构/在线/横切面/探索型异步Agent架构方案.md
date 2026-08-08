# 探索型异步 Agent 当前架构方案

- 状态：`active_architecture / implementation_complete / real_ab_pending`
- 更新：2026-08-02
- 历史的外部执行器方案已移除；本文件是唯一保留的探索型异步架构设计。
- 执行待办：[`../../../TODO/探索型异步Agent实施.md`](../../../TODO/探索型异步Agent实施.md)
- 总体边界：[`Runtime 控制面架构`](../在线/README.md)

## 目标

在单一 Python Runtime 内，让模型可以按需检索受治理知识、读取 DataContractView、调用只读查询并综合证据，同时把授权、预算、状态、证据资格和终态保留在服务端。

```text
QuestionContract / route prior
  → fat prior (off/shadow) 或 slim prior (on)
  → MinimalToolLoop
  → Runtime Tool Registry（固定 9 个受治理工具）
  → Knowledge Broker / DataContract binding / SQL guard
  → Claim attribution / coverage / typed outcome
```

## 当前实现事实

1. 已退役的 Node 执行器、Extension、scope-token 传输和 provider registry 均不再使用；`MinimalToolLoop` 进程内调用 Python handler。
2. `runtime_tool_registry.py` 固定登记 9 个工具：MC/CK 查询、freshness、catalog、DataContractView、policy、semantic contract、verified SQL 元数据/正文读取。
3. 当前 `resolve_runtime_tool_names()` 对 `off/shadow/on` 返回同一受治理工具集合。mode 不再承担工具可见性授权；每次调用仍由参数 schema、知识 registry、DataContract binding、SQL/PII/must-filter 和预算 fail closed。
4. `off/shadow` 使用 business prompt 和既有上下文；`on` 才启用 exploration prompt 与 slim prior。`shadow` 只可用于兼容性/审计观察，不代表 `on` 的回答质量。
5. job 首次 claim 固化 mode、registry/policy/prompt/tool manifest/build revision 与知识读取 hash；retry 必须复用，漂移 fail closed。
6. exact fast path 只有在 typed slots、covered claims 和 freshness 完整时才可短路；partial coverage 只能作为 evidence seed。

## 不变量

- route 只是软先验，不能授权资产或 SQL。
- 模型参数中的 asset/evidence id 不能直接形成执行授权；只有成功读取的 DataContractView 生成 server-owned binding。
- 禁止 raw/draft/TODO/archive、任意文件系统、系统元数据探测、写 SQL、数据写入和广告平台写 API。
- knowledge 正文、scope/secret、SQL rows、问题/答案全文不进入安全 trace。
- 工具停止、达到轮次或产生文本都不自动等于 `complete`；终态由 Runtime/P3 决定。

## 剩余决策与门禁

1. 真实 off/on A/B 必须同 commit、model、policy、registry、prompt revision 和 case split；每题每 mode N≥3。
2. 人工评分隐藏 mode；同时检查 required evidence group、bootstrap trap、safety、metadata-only、latency、cost 和 terminal 一致性。
3. 只有所有硬门通过后才允许 Test 的 `on` 小流量；默认仍为 `off`。
4. mode rollout 必须和知识状态一致性、P3 默认证据门及构建 provenance 分账验收。

## 回滚

将 exploration mode 退回 `off`，保留已提交的安全 snapshot、tool execution、QueryRecord 和 terminal 证据。回滚不删除历史，不改变本轮已固定的 job config，也不放宽知识或 SQL 授权。
