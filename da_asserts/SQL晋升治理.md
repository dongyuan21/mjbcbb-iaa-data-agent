# SQL 晋升治理

> 目标：把 DA 报告、临时分析和探索 SQL 晋升为 Agent 可默认召回的稳定 SQL，同时保留来源、验证和降级路径。

本机制控制的是“默认信任边界”，不是限制临时跑数。临时 SQL 可以存在，但只有通过门禁的 SQL 才能进入 `verified_sql/` 并被 Agent 当作默认 reference SQL。

## 状态机

```text
raw
  -> draft
  -> candidate_sql
  -> validated_sql
  -> verified_sql
  -> semantic_promoted
       |
       v
deprecated / superseded
```

| promotion_status | 含义 | Agent 默认行为 |
|---|---|---|
| `raw` | 原始报告、截图、导出件或未加工 SQL | 只作来源，不直接引用结论 |
| `draft` | 已人工整理，但缺 SQL 或缺验证 | 只能作为候选线索 |
| `candidate_sql` | SQL 已写出或复制，尚未完成验证 | 不默认召回；需要先小窗口验证 |
| `validated_sql` | 已小窗口跑通，有聚合结果摘要 | 可作为临时分析参考，不能当稳定口径 |
| `verified_sql` | 口径、分区、粒度、风险和验证记录齐全 | 可默认召回，运行前仍需检查日期和过滤 |
| `semantic_promoted` | 已进入 `semantic_contract` 或稳定 diagnostics/SOP | 可用于自然语言到 SQL 的默认路径 |
| `needs_decision` | 口径、阈值或动作待业务拍板 | 必须提示待决，不生成最终判断 |
| `deprecated` | 已废弃 | 不引用；必须指向替代 SQL 或说明原因 |
| `superseded` | 被新 SQL 替代 | 默认引用替代 SQL |

目录名不能替代状态。即使文件位于 `verified_sql/`，只要 `promotion_status` / `status` / `sql_status` 不是 verified 级别，Agent 也不能默认召回。

## 晋升门禁

### Gate A：结构门禁

进入 `candidate_sql` 或更高状态前，必须记录：

- 原始来源：报告、HTML、SQL、用户消息或表卡路径。
- 业务问题：这条 SQL 当时要回答什么。
- 口径说明：时间口径、粒度、维度、指标、过滤条件。
- 依赖表：包含库名、表名和必要分区字段。
- 风险与陷阱：预测值、口径未拍板、PII、明细不可落盘、跨源 join 限制等。

### Gate B：执行门禁

进入 `validated_sql` 或 `verified_sql` 前，必须至少有一次安全窗口验证：

- `last_validated_at`：验证日期。
- `validation_method`：`manual_small_window`、`manual_reconciliation`、`automated_regression`、`semantic_contract_regression` 或 `owner_confirmed`。
- 验证参数：日期窗口、产品、国家、渠道或 campaign。
- 结果摘要：row count、关键聚合指标、对账误差或失败原因。
- 安全判断：是否含用户级明细、设备 ID、IP、user_agent 或其他不可落盘字段。

### Gate C：召回门禁

Agent 默认召回只允许：

- `promotion_status: verified_sql` 且 `sql_status: verified`。
- `promotion_status: semantic_promoted` 且语义层回归通过。
- `status: confirmed` 的业务口径或 policy。

其他状态只能作为线索或待验证项，回答时必须显式说明限制。

## index.yaml 最小字段

所有 SQL 资产建议维护以下字段：

```yaml
promotion_status: candidate_sql | validated_sql | verified_sql | semantic_promoted | needs_decision | deprecated | superseded
last_validated_at: "YYYY-MM-DD"   # 未验证则省略或填 null
validation_method: manual_small_window | manual_reconciliation | automated_regression | semantic_contract_regression | owner_confirmed | not_applicable
owner: "owner_or_agent"
supersedes: []
```

`type: verified_sql` 的资产必须满足：

- `path` 位于 `verified_sql/`。
- `status: verified`。
- `sql_status: verified`。
- `promotion_status: verified_sql` 或 `semantic_promoted`。
- 有 `last_validated_at`、`validation_method` 和验证记录。
- Markdown 正文包含四个可机器抽取章节：`## 口径说明`、`## SQL`、`## 验证记录`、`## 风险与陷阱`。

## 评估指标

| 指标 | 定义 | 阶段目标 |
|---|---|---|
| verified SQL 数量 | `promotion_status` 为 `verified_sql` / `semantic_promoted` 的 SQL 数 | 稳步增加，不以数量牺牲质量 |
| 高频问题覆盖率 | 高频分析问题中可由 verified SQL 或 `semantic_contract` 回答的比例 | 下一阶段 ≥ 60% |
| draft 误召回次数 | Agent 把 draft / candidate 当事实引用的次数 | 目标 0 |
| 复跑失败率 | verified SQL 在相同口径下复跑失败或字段漂移的比例 | 持续下降 |
| 待拍板阻断率 | `needs_decision` 场景被正确拒答的比例 | 目标 100% |

## 维护节奏

1. 新材料先进入 `raw/`，不直接写入 `verified_sql/`。
2. 有可复用 SQL 但未验证时，放入 `candidate_sql/` 并标 `promotion_status: candidate_sql`。
3. 小窗口验证通过后，可升为 `validated_sql`；补齐结构、风险和验证记录后才升为 `verified_sql`。
4. 高频稳定问题再进入 `knowledge/agent_knowledge/semantic_contract/` 或 diagnostics，状态升为 `semantic_promoted`。
5. 表结构、口径或业务决策变化时，旧 SQL 标 `deprecated` / `superseded`，不要静默覆盖。
