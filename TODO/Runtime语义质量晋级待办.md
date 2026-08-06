# Runtime 语义质量晋级待办

- 状态：`open / B1_gold_frozen / promotion_blocked`
- 优先级：`P1`
- 更新：2026-08-02
- 架构：[`Runtime 控制面架构`](../data_agent_plan/Runtime控制面架构/README.md)
- 历史证据：[`Runtime 控制面历史实施材料`](归档/2026-08-02_过时与已完成事项/Runtime用户问题管理与控制面收敛_历史实施材料/README.md)

## 当前事实

QuestionContract 的 B1 r4 双审、仲裁、Gold 冻结和 provenance overlay 已形成可复验离线输入，但当前候选理解器仍未通过晋级门。最近一次安全聚合记录显示 protected required-claim recall 为 `51.56%`、protected silent claim drop 为 `109`，`promotion_eligible=false`；因此 B2 离线模型候选评测和 B3 Semantic shadow 继续阻塞。

这些数字是 2026-07-29～30 冻结题卷的离线评测结果，不是当前线上用户流量质量，也不属于 P0-Core、P3 Test 功能或 Prod 发布状态。

## 仍需完成

1. 对 `109` 个 protected silent claim drop 按 observer、resolver、reducer、event semantics 和安全拒绝做互斥归因；不得通过放宽 Gold 或修改评分口径洗绿。
2. 所有修复先进入无正文、无 SQL、无结果行的 L2 offline sidecar，固定 Gold、split、vocabulary、provenance overlay 和 comparator revision 重放。
3. B1 只有在显式事实保存为 100%、silent drop 为 0、事故 fixture 精确通过且重复回放稳定后，才允许申请 B2。
4. B2 仅做脱敏离线候选合同对照；模型 proposal 必须经 Runtime validator/reducer，不能获得 SQL 授权或终态权。
5. B3 Semantic 只有在 B2 质量与安全门全部通过后才可申请 shadow；shadow 不改变回答、route、工具授权或 terminal。

## 完成定义

- B1 的 hard gate 全绿，且失败归因、修复半径和回放证据可复验。
- B2 相对 B1 的提升、重复性、成本和安全门均有冻结报告，不以平均分掩盖 hard failure。
- B3 Semantic 经独立授权进入 Test shadow，并有停止线、回滚和隐私审计。
- 任一阶段都不保存题干、原始模型回答、SQL、结果行、filter 原值或凭证。
