# UA 决策行为沉淀 Phase1C PGP append-only DB 与 Outbox 设计（UA-1C-02）

> 状态：`design_candidate`
>
> 日期：`2026-07-24`
>
> `TASK_ID=UA-1C-02`；`TASK_TYPE=DESIGN+IMPLEMENTATION`
>
> `BASE_COMMIT=a1d9c24a`；`WORKTREE=ua-phase1c-2`

## 0. 人话摘要

把 Phase1C 三选项反馈存进一个 append-only 的 PGP 反馈库：旧反馈永远不覆盖，修改反馈 = 追加一条新 revision 并用 `supersedes_feedback_id` 指向旧记录。每次写入 feedback 同时写一条 outbox event，数仓离线消费 outbox 做对账。当前阶段无物理 PGP DB，用 `tools/scripts/ua_pgp_feedback_store.py` 内存版模拟全部语义。

## 1. 存储模型

### 1.1 feedback 表（append-only）

逻辑表 `pgp_ua_feedback`，append-only，不允许 UPDATE / DELETE：

| 列 | 类型 | 说明 |
|---|---|---|
| `feedback_id` | string(24) PK | 确定性 hash |
| `supersedes_feedback_id` | string(24) \| null | 指向被取代的 feedback_id |
| `opportunity_id` | string(24) | 关联机会 |
| `interaction_mode` | enum | `organic` \| `advisor_experiment` |
| `assignment_id` | string(24) \| null | |
| `generation_id` | string(24) \| null | |
| `exposure_id` | string(24) \| null | |
| `human_decision` | enum | 三选项 |
| `reason_codes` | array<string> | |
| `expected_window_days` | int \| null | |
| `budget_direction_candidate` | enum \| null | |
| `budget_band_candidate` | enum \| null | |
| `missing_data_type` | enum \| null | |
| `free_note_sanitized` | string \| null | 脱敏后 |
| `recorded_at` | timestamp | |
| `feedback_revision` | int | 同一 opportunity 递增 |
| `schema_version` | string | |
| `created_at` | timestamp | 入库时间 |

### 1.2 outbox 表

逻辑表 `pgp_ua_feedback_outbox`，与 feedback 同事务写入：

| 列 | 类型 | 说明 |
|---|---|---|
| `event_id` | string(24) PK | `H("outbox", feedback_id, recorded_at)` |
| `feedback_id` | string(24) | 指向 feedback |
| `opportunity_id` | string(24) | 冗余便于消费 |
| `event_type` | enum | `feedback_created` \| `feedback_superseded` |
| `supersedes_feedback_id` | string(24) \| null | 冗余 |
| `feedback_revision` | int | 冗余 |
| `human_decision` | enum | 冗余 |
| `recorded_at` | timestamp | |
| `created_at` | timestamp | outbox 写入时间 |
| `exported_at` | timestamp \| null | 被导出消费后回填 |
| `schema_version` | string | |

## 2. supersedes revision 规则

- 同一 `opportunity_id` 允许多条 feedback，每条 `feedback_revision` 递增（1, 2, 3...）
- 新 feedback 通过 `supersedes_feedback_id` 指向上一条
- 旧 feedback 不删除、不修改，永久保留
- 读取"当前有效反馈"时取 `opportunity_id` 下 `feedback_revision` 最大的那条
- 若新 feedback 不填 `supersedes_feedback_id` 但该 opportunity 已有 feedback，则拒绝（必须显式 supersede）——防止隐式覆盖

## 3. outbox 对账规则

- 每次 append feedback 在同事务写一条 outbox event
- `event_type`：
  - `feedback_created`：该 opportunity 首版 feedback
  - `feedback_superseded`：supersede 链上的新 revision
- outbox event 冗余关键字段，消费者无需回查 feedback 表即可对账
- 导出消费后回填 `exported_at`，但不删除 event（append-only）
- outbox 是 feedback 的唯一对外投递通道，数仓不直连 feedback 表

## 4. 幂等规则

- 幂等键：`(opportunity_id, recorded_at, interaction_mode, feedback_revision)`
- 重复提交同一组合不重复写入，返回已有 `feedback_id`
- `feedback_id` 本身由 `H("feedback", opportunity_id, recorded_at, interaction_mode)` 生成，是幂等键的 hash 投影

## 5. 无曝光 Control 处理

- `interaction_mode=advisor_experiment` 但 `exposure_id=null` 的提交视为"分桶了但没曝光"的 Control
- 不拒绝入库（Control 也是有效数据），但在 outbox event 上标记 `event_type=feedback_created` 且 `exposure_id` 字段投影为 null
- 消费端可据此区分"曝光后反馈"和"未曝光 Control 反馈"

## 6. PII 不落盘

- `free_note_sanitized` 入库前必须脱敏（见 UA-1C-01 §5）
- 原始备注只在调用方内存中存在，不进 feedback 表、不进 outbox
- `assignment_id` / `generation_id` / `exposure_id` 都是确定性 hash，不含 PII
- outbox 导出（UA-1C-05A）只投影安全字段，再次过滤

## 7. 当前阶段实现

- 无物理 PGP DB：`tools/scripts/ua_pgp_feedback_store.py` 用内存 dict 模拟
- 接口：
  - `submit_feedback(payload) -> (feedback_id, event_id, is_duplicate)`
  - `get_current_feedback(opportunity_id) -> dict | None`
  - `get_feedback_chain(opportunity_id) -> list`
  - `list_outbox(cursor, limit) -> (events, next_cursor)`
- 测试：`tools/scripts/test_ua_pgp_feedback_store.py`，7 场景见下文

## 8. 测试场景（7 个）

1. 正常提交：首版 feedback 入库 + outbox event
2. 修改反馈：supersede 链，旧 revision 保留，新 revision revision+1
3. 重复提交：相同幂等键不重复写入
4. 无曝光 Control：advisor 模式 exposure_id=null 允许入库
5. supersedes 链：多级 supersede，取最新 revision
6. outbox 对账：feedback 与 outbox 一一对应
7. PII 不落盘：原始备注不入库，只存脱敏版
