# UA 决策行为沉淀 Phase 1A — Level 0 抽样重建方案（UA-1A-10）

> 日期：2026-07-23
> 分支：`codex/ua-1a-09r-10-20260723`
> Base commit：`6e38f0e3`

## 0. 人话摘要

这个方案定义"怎么验证 Google Episode 数据准不准"——抽样几条 Episode，人工核对每一步的数据对不对。

## 1. 抽样策略

按以下维度分层抽样，每层至少 3 条：

| 层 | 维度 | 样本量候选 |
|---|---|---|
| 动作类型 | budget_increase_large / budget_decrease_small / no_budget_change | 各 3 条 |
| DecisionSubject | campaign_budget / shared_budget | 各 3 条 |
| 时间 | 近 7 天 / 近 30 天 / 90 天前 | 各 3 条 |
| 名称兜底 | 用 campaign_name 匹配（非 ID） | 3 条 |
| 边界 | compound action / coverage incomplete / 空结果 | 各 2 条 |

总样本量：约 20-30 条 Episode。

## 2. 需要报告的 9 个指标

| 指标 | 定义 | 冻结门槛候选 |
|---|---|---|
| `operation_event_link_precision` | CanonicalOperationEvent 与来源操作链接的 precision | ≥ 0.95 |
| `budget_before_after_accuracy` | 预算 before/after/币种/幅度的抽样准确率 | ≥ 0.90 |
| `decision_unit_accuracy` | DecisionSubject 与真实预算控制对象一致的准确率 | ≥ 0.95 |
| `reviewed_no_action_precision` | 显式继续观察且无预算变化标签的 precision | ≥ 0.90（有样本时） |
| `observed_no_budget_change_precision` | 覆盖完整未处理标签的 precision | ≥ 0.90 |
| `point_in_time_reconstruct_rate` | 能冻结完整操作前快照的机会占比 | ≥ 0.80 |
| `source_window_complete_rate` | 标签窗口所有 endpoint/页/预算资源覆盖完整的占比 | ≥ 0.90 |
| `future_leakage_count` | 任何未来字段进入训练或检索 | 0 |
| `pii_leakage_count` | Agent 或评估产物泄漏 PII | 0 |

**冻结规则**：门槛在查看测试集结果前冻结，不因结果不好而下调。

## 3. 当前可做的 dry-run 级验证

| 验证项 | 方法 | 结果 |
|---|---|---|
| 全链路可运行 | dry-run 10 步全 exit 0 | ✅ 已验证 |
| 采集→Observation 数量一致 | MI 返回 7 条操作 = Observation 7 条 | ✅ 已验证 |
| coverage 完整性 | terminal_cursor=True, status=complete | ✅ 已验证 |
| 脱敏正确 | 输出不含操作人邮箱明文 | ✅ 已验证 |
| Episode evidence_hash 确定性 | 相同输入相同 hash | ✅ 测试已验证 |
| future_leakage_count | 特征快照泄漏检测返回 0 | ✅ mock 已验证 |

## 4. 需要物理表落地后才能做的

| 验证项 | 为什么现在做不了 |
|---|---|
| operation_event_link_precision | 需要人工核对真实操作 vs Episode 事件 |
| budget_before_after_accuracy | 需要 Google change event old/new 与 Episode before/after 交叉核对 |
| decision_unit_accuracy | 需要人工判断"改的是 Campaign 还是 shared budget" |
| reviewed_no_action_precision | 需要 PGP 显式反馈样本（Phase 1C 后才有） |
| point_in_time_reconstruct_rate | 需要历史快照数据 |
| source_window_complete_rate | 需要多 Campaign 全量采集 |

## 5. 盲审流程

1. AI 生成抽样 Episode 清单（不含真实操作人/金额）
2. 人工核对每条 Episode 的 6 个维度（身份/时间/before/after/意图/Outcome）
3. 人工标注"正确/错误/部分正确"
4. 计算 9 个指标
5. 与冻结门槛对比
6. 通过 → `GO_FACTUAL(google, campaign_budget)` candidate；不通过 → 修复后重跑

## 6. 非目标声明

本方案未签发 `GO_FACTUAL`；未执行 DDL/DML；未部署。
