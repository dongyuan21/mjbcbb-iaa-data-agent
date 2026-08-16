# Runtime 单一主链架构（探索控制面退役）

- 状态：`active_single_runtime / exploration_control_plane_retired`
- 更新：2026-08-09
- 决策提交：`<提交标识>`
- 退役记录：[`../../../../TODO/归档/2026-08-09_已完成任务清理/探索型异步Agent实施.md`](../../../../TODO/归档/2026-08-09_已完成任务清理/探索型异步Agent实施.md)
- 使用与验收：[`../../../../showoff/03-运行与探索/Runtime单一主链使用与验收指南.md`](../../../../showoff/03-运行与探索/Runtime单一主链使用与验收指南.md)
- 总体边界：[`../README.md`](../README.md)

## 当前形态

```text
QuestionContract / route prior
  → fixed slim prior + business prompt
  → Context Compiler
  → MinimalToolLoop
  → Runtime Tool Registry（注册 10；按 route/engine/服务端事实收窄，通常 9，白名单 route 可 10；不构成 SQL 授权）
  → Knowledge Broker / DataContract binding / SQL guard
  → Claim attribution / coverage / typed outcome
```

1. `DataAgentRuntime + MinimalToolLoop` 是唯一执行主链，不存在 off/shadow/on 运行模式。
2. 工具可见性由 route policy 与 Runtime Registry 收窄；每次调用仍经过参数 schema、知识
   registry、DataContract binding、SQL/PII/must-filter 和预算门禁。
3. Worker 首次 claim 固化 registry、policy、prompt、tool manifest 与 build revision；retry
   只能复用同一安全 snapshot，漂移 fail-closed。
4. exact fast path 只有在 typed slots、covered claims 和 freshness 完整时才可短路；partial
   coverage 只能作为 evidence seed。
5. Context Compiler 保留 P0-P2 安全地板，只裁剪可选 P3/P4；无法满足预算时在模型调用前
   fail-closed。

## 不变量

- route 和 prior 提供检索先验；route 还收窄模型可见工具面，但不能授权资产、SQL 或完成状态。
- 模型给出的 asset/evidence id 不能形成执行授权；只有成功读取的 DataContractView 生成
  server-owned binding。
- 禁止 raw/draft/TODO/archive、任意文件系统探测、写 SQL、数据写入和广告平台写 API。
- knowledge 正文、scope/secret、SQL rows、问题/答案全文不进入安全 trace。
- 工具停止、达到轮次或产生文本都不自动等于 `complete`；终态由 Runtime/P3 决定。

## 退役理由

旧 mode 已不承担工具授权，三种 mode 又共享同一工具集合；继续保留它只会增加 prompt、Worker
snapshot、job provenance、重试与配置的分叉。真实配对 A/B 也没有形成可接受的产品证据。
因此直接移除整个控制面，而不是继续维护默认 `off` 的兼容路径。

`eval/exploration_ab/cases.yaml` 只保留为冻结风险语料和静态 Registry 校验输入。未来若要
建设新的探索能力，必须新建产品合同和验收任务，不能复活旧 mode 或沿用历史 A/B 结论。
