# 探索型异步 Agent 实施待办

- 状态：`implementation_complete / real_off_on_ab_pending / default_off`
- 创建：2026-07-26
- 更新：2026-08-02
- 当前架构：[`探索型异步 Agent 当前架构方案`](../data_agent_plan/探索型异步Agent架构方案.md)
- 评测：[`eval/exploration_ab/README.md`](../eval/exploration_ab/README.md)、[`cases.yaml`](../eval/exploration_ab/cases.yaml)

## 已实现基线

- [x] 10 道探索 A/B case、静态 validator 和 registry eligibility 门。
- [x] exploration mode/config snapshot、policy/registry/prompt/tool manifest/build revision 固化与 retry drift fail-closed。
- [x] 受治理 catalog、DataContractView、policy、semantic contract 和 verified SQL 检索/读取。
- [x] Python `MinimalToolLoop` 与固定 9 个进程内 Runtime 工具；已退役的 Node 执行器与 Extension 已移除。
- [x] on 模式 slim prior、exploration prompt、共享预算和知识正文 metadata-only 安全投影。
- [x] exact fast path coverage/freshness eligibility；partial bootstrap 只作 evidence seed。
- [x] trace、tool execution、QueryRecord、asset revision/hash 和安全配置快照。
- [x] 本地组件测试及静态 `--validate-only --require-registry-eligible` 门可通过。

## 已纠正的旧表述

- `off` 不再表示“Runtime 只看到旧 4 工具”。当前 `resolve_runtime_tool_names()` 在三种 mode 下都返回同一固定 9 工具；安全由 Runtime registry、DataContract binding 和 L5 guard 控制。
- mode 的当前差异是 prompt/prior 与探索行为：`on` 使用 slim prior/exploration prompt，`off/shadow` 使用 business prompt/既有上下文。
- `shadow` 不能替代 `on` 的质量评测；Runtime gateway 429 也不再是现行架构阻塞描述。

## 仍开：真实 A/B 与灰度

- [ ] 固定同一 commit、model、policy/registry、prompt/tool manifest 和 case split，对 10 题分别跑 `off/on`，每题每 mode N≥3。
- [ ] 评分者隐藏 mode；记录逐题证据、terminal、latency、token/cost 和失败类型。
- [ ] A+B+C 均分 `on >= off + 1.0/10`。
- [ ] required evidence group 命中率提升至少 20pct。
- [ ] bootstrap trap 错误短路、exact fast path 新回归、safety violation、metadata-only 泄漏均为 0。
- [ ] 先 Test compatibility observation，再经授权做 `on` 小流量；Prod 另行验收。
- [ ] 固定停止线、owner、回滚阈值和安全 trace；失败立即退 `off`，不删除历史证据。

## 完成定义

- 真实 A/B 达到全部质量与安全硬门，不用平均分掩盖 hard failure。
- Test 小流量证明知识读取、SQL binding、claim coverage、terminal 和回滚一致。
- 默认 mode 的任何改变有当前构建 provenance 和配置证据；Test 结果不冒充 Prod。
- 产品边界保持只读分析与预警，不新增广告平台写动作。
