# 低置信度反问协议 TODO

> 更新：2026-08-02
> 状态：代码默认 `shadow_default_t1_t2`；共享 Test / Prod 实际配置与自然样本待重新验证
> 权威策略：`runtime/backend/app/services/clarification_policy.yaml`  
> 实现：`clarification_gate.py`、`route_confidence.py`

## 触发条件（摘要）

Runtime 用整数 `route_score` / `score_diff`，不是概率。细则以 yaml 为准。

| 编号 | 条件 | 默认 |
|---|---|---|
| T1 | `route_score<=0` 或业务信号却走 `general_answer` | allowlist + shadow |
| T2 | `score_diff<=3` | allowlist + shadow |
| T3 | 关键 slot 缺失 / 极度模糊 | 实现有，**不**在默认 allowlist |
| T4–T5 | 字段证据 / 验证状态 | planned，metadata 未齐 |
| T6 | owner 决策边界（停投/放量等） | 实现有，不全局启用 |
| T7 | 口径矛盾 | 未闭环 |

模板 A–D、trace `clarification_event` 字段见 git 历史或稳定后迁 `knowledge/…/反问协议.md`；运行时以 gate 输出为准。

## 已有基线（不再列为待办）

T1/T2/T3/T6 判定、shadow/enforce 开关、allowlist、置信度校准以及
`clarification_event` 持久化均已有实现；具体行为以权威策略和当前代码为准。
历史 controlled smoke 只能证明当时的链路，不计入自然样本 precision。

## 仍开

- [ ] T4/T5 等证据 metadata 进 runtime
- [ ] 反问文案与 DA/产品确认
- [ ] 打通 route-based T1/T2 反问与 P3 durable `waiting_clarification → resume → answer`；当前两条链路独立，低置信度 gate 返回的是普通 `AgentAnswer`
- [ ] 实时读取共享 Test / Prod 配置并留存非敏感证据，不能用代码默认值推断线上状态
- [ ] 连续 ≥2 业务日且 ≥30 条 **自然** external T1/T2 触发后，用 `tools/scripts/aggregate_clarification_shadow.py` 复核（门槛建议 T1≥95%、T2≥90%），再决定是否只对 T1/T2 开 enforce

## 样本结论（勿用受控流量凑绿）

2026-07-14/15 的历史审计快照为：Test `shadow=true`、`gate=false`、
allowlist=`T1,T2`，自然 external T1/T2 命中不足 30，因此当时结论是
`enforce_candidate=false / evidence_gap`。该快照不代表 2026-08-02 的线上配置；
受控 smoke 只证明链路，不进 precision 分母。
