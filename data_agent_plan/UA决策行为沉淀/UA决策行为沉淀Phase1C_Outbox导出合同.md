# UA 决策行为沉淀 Phase1C Outbox 安全导出合同（UA-1C-05A）

> 状态：`design_candidate`
>
> 日期：`2026-07-24`
>
> `TASK_ID=UA-1C-05A`；`TASK_TYPE=DESIGN+IMPLEMENTATION`
>
> `BASE_COMMIT=a1d9c24a`；`WORKTREE=ua-phase1c-2`

## 0. 人话摘要

定义 PGP outbox 的安全导出合同：cursor 分页、supersedes 处理、PII projection（只输出安全字段）、schema version。数仓离线消费按本合同拉取 outbox feed，回填 OpportunityProjection 的 has_feedback / current_feedback_decision。

## 1. 导出接口

`export_outbox_feed(cursor, limit) -> {events, next_cursor, schema_version}`

- `cursor`：上次导出最后一行的 `event_id`，首次为 null
- `limit`：单页条数，默认 100，上限 1000
- `next_cursor`：null 表示已到末尾
- `schema_version`：当前 feed 的 schema 版本

实现：`tools/scripts/ua_pgp_outbox_export.py`

## 2. supersedes 处理

- 导出按 outbox 插入顺序（append-only）输出全部 event，包括 `feedback_superseded` 事件
- 消费方自行根据 `supersedes_feedback_id` 链计算当前有效 feedback
- 导出不删除/不合并被 supersede 的旧 event（append-only，事实不可变）
- 导出提供 `resolve_current_decision(opportunity_id)` 辅助函数，返回该 opportunity 当前最新 revision 的 human_decision

## 3. PII projection（安全字段）

导出 event 只输出以下安全字段，**不输出** `free_note_sanitized`（虽已脱敏，仍不进数仓）：

| 字段 | 输出 |
|---|---|
| `event_id` | 是 |
| `feedback_id` | 是 |
| `opportunity_id` | 是 |
| `event_type` | 是 |
| `supersedes_feedback_id` | 是（null 也输出） |
| `feedback_revision` | 是 |
| `human_decision` | 是 |
| `interaction_mode` | 是 |
| `exposure_id` | 是（null 也输出，用于区分 Control） |
| `recorded_at` | 是 |
| `created_at` | 是 |
| `exported_at` | 是 |
| `schema_version` | 是 |
| `assignment_id` | 是 |
| `generation_id` | 是 |
| `reason_codes` | 是（受控词表，非自由文本） |
| `budget_direction_candidate` | 是 |
| `budget_band_candidate` | 是 |
| `expected_window_days` | 是 |
| `missing_data_type` | 是 |
| `free_note_sanitized` | **否**（不导出） |

## 4. schema version

- 当前 `schema_version = "ua_feedback_outbox_v0.1"`
- 消费方必须校验 schema_version，未知 major 版本拒绝消费
- minor 版本新增字段忽略

## 5. 重复读取不改变事实

- 导出是只读操作，不修改 outbox 内容
- `mark_exported` 只回填 `exported_at` 时间戳，不删除 event
- 重复导出同一 cursor 范围返回相同结果（除 exported_at 外）
- 数仓消费侧应做去重（按 event_id）

## 6. 当前阶段实现

- 无物理 PGP DB，导出从 `FeedbackStore` 内存 outbox 读取
- 输出为 JSONL 文件，便于离线对账
- 测试：`tools/scripts/test_ua_pgp_outbox_export.py`，5 场景

## 7. 测试场景（5 个）

1. 正常导出：首版 feedback → outbox event 导出
2. cursor 分页：limit 分页，next_cursor 正确
3. supersedes：supersede 链导出，resolve_current_decision 取最新
4. PII 过滤：导出不含 free_note_sanitized
5. 重复读取不改变事实：重复导出相同 cursor 结果一致
