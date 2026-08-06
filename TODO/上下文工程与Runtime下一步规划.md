# 上下文工程与 Runtime 下一步规划

- 状态：`partial_implemented / measurement_ready / mainline_compaction_pending`
- 更新：2026-08-02
- 统一设计：[`多轮对话与上下文压缩工程设计`](../data_agent_plan/多轮对话与上下文压缩工程设计.md)
- 执行分账：[`多轮对话建设`](多轮对话建设.md)、[`KV 缓存观测`](KV缓存命中与压缩关系观测计划.md)、[`探索型异步 Agent`](探索型异步Agent实施.md)

## 当前事实

1. Runtime 已迁移为 Python `DataAgentRuntime + MinimalToolLoop` 单一主链，不再存在外部 RPC 执行链的历史压缩问题。
2. per-stage token 计量、provider usage 对账和 count-only 安全投影已实现，可作为后续压缩 A/B 的度量底座。
3. `search_catalog`、受控知识读取、semantic contract/verified SQL 检索和 exploration slim prior 已实现；但代码默认 exploration `off`，尚不能据此宣称所有生产 route 都已按需切片。
4. `ConversationState`、resolver、orchestrator、Context Compiler/reducer 等组件存在，但完整 `TurnResolution → checkpoint commit → 下一轮读取` 尚未接上真实 API/SSE/Worker 主链。
5. 旧文档中“Stage2 三个索引完全未检索化”“线上仍是 Runtime 多轮历史”等判断已失效，后续不再沿用。

## 相位 A · 固定度量基线（已完成，持续防回归）

- [x] 最终 prompt 的 bootstrap、route、asset、history、user 等阶段计量。
- [x] provider input/output/total 与分阶段估算对账。
- [x] trace 只保存计数、状态和安全 revision，不保存问题、答案、SQL、rows 或 payload。
- [ ] 将上述计量固定进上下文改动的回归报告模板；每次优化必须给出同题 delta，而不是只报字符数估算。

## 相位 B · bootstrap 与固定前缀收敛

- [ ] 对实际 Runtime prompt 和 Codex/Cursor 常驻注入分别采样，不再用 2026-06 的静态文件大小当现状。
- [ ] 固定不可压缩地板：安全/PII、只读边界、freshness、route/授权边界；不得为了 token 降低硬门。
- [ ] 将治理 owner、promotion path 和大 manifest 保持按需读取；任何 bootstrap 调整先做 route/knowledge 回归。
- [ ] 通过前缀稳定度、prompt tokens、cached tokens、TTFT 和回答质量共同判断收益。

## 相位 C · 检索切片与 slim prior 生产验证

- [ ] 基于现有 `search_catalog`、DataContractView、semantic contract 和 verified SQL 工具，盘点每条生产 route 的实际可读资产与缺口。
- [ ] 完成 exploration off/on 同 commit/model/config 的真实 A/B；未完成前保持默认 `off`，不把实现存在写成质量提升。
- [ ] 对 `model.json`、两库 catalog 和 `da_assets/index.yaml` 的整包读取建立负向门；只返回本题需要的切片和 revision。
- [ ] 检索失败、资产状态冲突和预算耗尽必须显式进入 TypedOutcome，不回退为 raw/draft/TODO。

## 相位 D · 多轮状态与渐进压缩

本相位的状态、CAS、commit envelope、TurnKind、Context Compiler 和 L0～L4 语义以统一设计和 [`多轮对话建设`](多轮对话建设.md) 为准，本文件不再复制第二套状态机。

- [ ] 先闭合真实回答后的结构化 checkpoint 提交和下一轮读取。
- [ ] 再验证 Snip/MicroCompact/Collapse/AutoCompact：口径、未决项、freshness、evidence 指针和 source hash 不得丢失。
- [ ] 20/50/100 turn 长会话、topic switch、correction、clarification、并发 CAS 和 Worker 重启均有回放证据。

## 相位 E · 正式召回与数据质量协同

- [ ] 表卡状态/Runtime eligibility 先完成一致性收口，再评估 slim prior 或 P3 default；避免在错误授权上优化上下文。
- [ ] 5 张 `known_pitfalls` 等人取证后回填，不为了压缩把风险字段删除。
- [ ] confirmed policy、semantic contract、table card、verified SQL 只保留单一权威写入点；prompt 使用引用和 revision，不复制公式。

## 相位 F · KV Cache 真实观测

按 [`KV缓存命中与压缩关系观测计划.md`](KV缓存命中与压缩关系观测计划.md) 执行。当前只有模板和计量能力，没有真实 A/B 结论。

## 完成定义

- 所有优化都有同 commit/model/config、同题、单次无重试的 token/latency/cache/quality 对照。
- 生产 route 默认只读取必要的受治理切片，失败不越权回退。
- 结构化多轮主链和 L0～L4 压缩通过长会话、并发、重启和安全回放。
- 固定安全地板、证据资格和产品只读边界在任何压缩级别都不退化。
