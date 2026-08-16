# SQL 晋升状态机与三层 Gate

> 汇报定位：解释一条 SQL 从"DA 临时写的"到"Agent 默认召回的稳定口径"要经过哪些状态和门禁，为什么不能写出来就用。
> 适合听众：DA、数仓、投放分析同学，以及需要理解"Agent 怎么保证 SQL 写得对"的业务同学。
> 权威依据：`da_assets/SQL晋升治理.md`。
> 时效边界：本文是状态机说明，不是已验证 SQL 数量、覆盖率或最近一次门禁结果的来源；这些状态必须由 SQL 资产字段和最新门禁报告确认。

## 一句话说明

SQL 不是写出来就能用。一条 SQL 要从 `raw`（原始）经过 6 个状态升到 `verified_sql`（已验证），再升到 `semantic_promoted`（语义层晋升）才能被 Agent 当默认口径。每个状态升级都要过一道 Gate（门禁）：结构门禁、执行门禁、召回门禁。**目录名不能替代状态**——即使文件放在 `verified_sql/` 目录下，只要状态字段不是 verified 级别，Agent 也不能默认召回。

## 为什么要状态机

| 痛点 | 状态机怎么解决 |
|---|---|
| DA 临时写的 SQL 没验证就被当事实 | 必须经过小窗口实跑和对账才能升到 validated_sql |
| 候选 SQL 口径没拍板就被默认召回 | 只有 verified_sql 和 semantic_promoted 可默认召回 |
| 表结构变了，旧 SQL 静默失效 | 旧 SQL 标 `deprecated` / `superseded`，必须指向替代 SQL |
| 口径待 owner 拍板的 SQL 被当结论 | 标 `needs_decision`，Agent 必须提示待决，不生成最终判断 |
| 谁也说不清这条 SQL 可不可信 | 状态字段 + `last_validated_at` + `validation_method` 全程留痕 |

## 状态机全景

```
raw
  → draft
  → candidate_sql
  → validated_sql
  → verified_sql
  → semantic_promoted
       |
       v
deprecated / superseded
```

| 状态 | 含义 | Agent 默认行为 |
|---|---|---|
| `raw` | 原始报告、截图、导出件或未加工 SQL | 只作来源，不直接引用结论 |
| `draft` | 已人工整理，但缺 SQL 或缺验证 | 只能作为候选线索 |
| `candidate_sql` | SQL 已写出或复制，尚未完成验证 | 不默认召回；需要先小窗口验证 |
| `validated_sql` | 已小窗口跑通，有聚合结果摘要 | 可作为临时分析参考，不能当稳定口径 |
| `verified_sql` | 口径、分区、粒度、风险和验证记录齐全 | 可默认召回，运行前仍需检查日期和过滤 |
| `semantic_promoted` | 已进入 semantic_contract 或稳定 diagnostics/SOP | 可用于自然语言到 SQL 的默认路径 |
| `needs_decision` | 口径、阈值或动作待业务拍板 | 必须提示待决，不生成最终判断 |
| `deprecated` | 已废弃 | 不引用；必须指向替代 SQL 或说明原因 |
| `superseded` | 被新 SQL 替代 | 默认引用替代 SQL |

## 三层 Gate（门禁）

### Gate A：结构门禁

进入 `candidate_sql` 或更高状态前，必须记录：

- **原始来源**：报告、HTML、SQL、用户消息或数据资产目录路径。
- **业务问题**：这条 SQL 当时要回答什么。
- **口径说明**：时间口径、粒度、维度、指标、过滤条件。
- **依赖表**：包含库名、表名和必要分区字段。
- **风险与陷阱**：预测值、口径未拍板、PII、明细不可落盘、跨源 join 限制等。

### Gate B：执行门禁

进入 `validated_sql` 或 `verified_sql` 前，必须至少有一次安全窗口验证：

- `last_validated_at`：验证日期。
- `validation_method`（验证方法）：
  - `manual_small_window`（手动小窗口）
  - `manual_reconciliation`（手动对账）
  - `automated_regression`（自动回归）
  - `semantic_contract_regression`（语义合同回归）
  - `owner_confirmed`（owner 确认）
- **验证参数**：日期窗口、产品、国家、渠道或 campaign。
- **结果摘要**：row count（行数）、关键聚合指标、对账误差或失败原因。
- **安全判断**：是否含用户级明细、设备 ID、IP、user_agent 或其他不可落盘字段。

### Gate C：召回门禁

Agent 默认召回**只允许**：

- `promotion_status: verified_sql` 且 `sql_status: verified`。
- `promotion_status: semantic_promoted` 且语义层回归通过。
- `status: confirmed` 的业务口径或 policy。

其他状态只能作为线索或待验证项，回答时必须显式说明限制。

## verified_sql 资产的最小字段

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
- Markdown 正文包含四个可机器抽取章节：
  - `## 口径说明`
  - `## SQL`
  - `## 验证记录`
  - `## 风险与陷阱`

## 评估指标

| 指标 | 定义 | 阶段目标 |
|---|---|---|
| verified SQL 数量 | `promotion_status` 为 `verified_sql` / `semantic_promoted` 的 SQL 数 | 稳步增加，不以数量牺牲质量 |
| 高频问题覆盖率 | 高频分析问题中可由 verified SQL 或 semantic_contract 回答的比例 | 下一阶段 ≥ 60% |
| draft 误召回次数 | Agent 把 draft / candidate 当事实引用的次数 | 目标 0 |
| 复跑失败率 | verified SQL 在相同口径下复跑失败或字段漂移的比例 | 持续下降 |
| 待拍板阻断率 | `needs_decision` 场景被正确拒答的比例 | 目标 100% |

## 维护节奏

```
1. 新材料先进入 da_assets/raw/，不直接写入 verified_sql/
2. 有可复用 SQL 但未验证时，放入 candidate_sql/ 并标 promotion_status: candidate_sql
3. 小窗口验证通过后，可升为 validated_sql；补齐结构、风险和验证记录后才升为 verified_sql
4. 高频稳定问题再进入 semantic_contract 或 diagnostics，状态升为 semantic_promoted
5. 表结构、口径或业务决策变化时，旧 SQL 标 deprecated / superseded，不要静默覆盖
```

## 如何确认当前状态

- SQL 的可召回状态：读取资产的 `promotion_status`、`status`、`sql_status` 和验证记录，目录名本身不构成结论。
- 当前资产规模：以 `da_assets/` 下的 index / catalog 为准，不在本文固化计数。
- 当前门禁结论：重新执行本节列出的脚本并读取本次生成的报告；历史 PASS、数量和日期都不能替代本次验证。

## 门禁位置

| 门禁 | 脚本 | 报告 |
|---|---|---|
| SQL 晋升边界与 index 审计 | `check_sql_promotion.py` | `eval/sql_promotion/SQL晋升指标报告.md` |
| Text2SQL 字段证据 | `check_text2sql_field_evidence.py` | `eval/Text2SQL字段证据门禁报告.md` |
| SQL 分区护栏 | `check_sql_partition_guardrails.py` | `eval/SQL分区护栏报告.md` |
| 语义合同可编译 | `semantic_contract/eval/compose_sql.py` | （纳入 agent_regression） |
