# Text2SQL 字段证据模板

> 状态：template  
> 适用范围：所有由 Text2SQL、SQL 写作链或 Agent 草拟的新 `candidate_sql`。  
> 目标：让 SQL 在生成前先证明字段、表、口径和验证边界，避免凭字段名猜语义。

## 使用方式

新建 candidate SQL 前，先复制下面模板到 SQL 文档中。字段证据不足时，不写完整 SQL；先输出缺口和验证计划。

## 最小模板

```yaml
text2sql_task:
  task_id: ""
  user_question: ""
  task_type: text2sql_or_sql_planning
  scenario:
    primary: ""
    policies:
      - knowledge/agent_knowledge/policies/SQL写作业务协议.md
      - knowledge/agent_knowledge/policies/SQL表路由协议.md
  normalized_requirement:
    product: ""
    platform: ""
    time_window: ""
    metrics: []
    dimensions: []
    filters: []
    grain: ""
  output_status: candidate_sql

field_evidence:
  - requirement_item: ""
    item_type: metric | dimension | filter | join_key | partition | pii_boundary
    semantic_name: ""
    source_table: ""
    source_field: ""
    expression: ""
    evidence_source:
      type: verified_sql | semantic_contract | table_card | live_schema | dry_run | small_window | knowledge_policy | candidate_backlog | owner_confirmed
      path: ""
      detail: ""
    validation_status: verified | confirmed | schema_probe | dry_run_passed | small_window_verified | candidate_table_requires_intake | field_requires_validation | owner_confirmation_required
    notes: ""

table_evidence:
  - table: ""
    catalog_status: in_catalog | candidate_table_requires_intake | not_found
    table_card: ""
    partition_filters_required: []
    app_or_product_filters_required: []
    event_filters_required: []
    pii_boundary: ""
    freshness_status: live_probed | snapshot_only | connectivity_unverified | delayed | stale | unknown

sql_safety_gates:
  partition_gate: pass | blocked | not_checked
  pii_gate: pass | blocked | not_checked
  freshness_gate: pass | blocked | not_checked
  join_gate: pass | blocked | not_checked
  dry_run_gate: pass | blocked | not_checked

promotion_boundary:
  current_status: candidate_sql
  can_default_recall: false
  next_validation_step: schema_probe | dry_run | small_window | owner_confirmation | promote_to_verified | keep_candidate
  blockers: []
```

## 阻断规则

出现以下任一情况时，不得输出 verified 口径：

- 字段只来自源材料示例 SQL，未被表卡、schema 或小窗口验证。
- 表未进入 `ai_hive/agent_knowledge/catalog.yaml` / `ai_ck/agent_knowledge/catalog.yaml`，且没有 live schema 证据。
- join key 没有表卡、语义层或 owner 证据。
- 白名单事件表缺少 `event_name` 过滤。
- 共享表缺少 `app_name` / 产品过滤。
- 快照表缺少最新分区或 `hour` 规则。
- 包含用户级 ID、设备 ID、IP、user_agent、token、cookie 或原始明细输出。
- 需要业务阈值、停投、放量或预算动作判断。

## 证据等级

| 等级 | 可用于 SQL 草案 | 可用于 verified |
|---|---:|---:|
| `verified_sql` | 是 | 是 |
| `semantic_contract` | 是 | 需对应回归通过 |
| `table_card` | 是 | 需字段和口径完整 |
| `live_schema` | 是 | 只能证明字段存在 |
| `dry_run` | 是 | 只能证明 SQL 可编译 / 可执行 |
| `small_window` | 是 | 可作为 validated_sql 证据 |
| `knowledge_policy` | 是 | 只证明业务规则，不证明字段存在 |
| `candidate_backlog` | 仅线索 | 否 |
| `owner_confirmed` | 是 | 取决于确认范围 |

## Candidate SQL 文档建议结构

```markdown
# <SQL 名称>

> promotion_status: candidate_sql
> validation_status: schema_probe | dry_run_passed | small_window_verified | not_validated

## 业务问题

## 字段证据

## SQL

## 验证记录

## 风险与陷阱

## 下一步
```

## 与晋升治理的关系

本文只约束 Text2SQL 草案进入 `candidate_sql` 前的字段证据。晋升到 `validated_sql` / `verified_sql` 仍以 `SQL晋升治理.md` 为准。
