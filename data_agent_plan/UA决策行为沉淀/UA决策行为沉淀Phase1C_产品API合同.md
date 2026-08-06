# UA 决策行为沉淀 Phase1C 产品/API 合同（UA-1C-01）

> 状态：`design_candidate`（AI 自主设计候选版本，无物理表，待后续人工 Gate 确认）
>
> 日期：`2026-07-24`
>
> `TASK_ID=UA-1C-01`；`TASK_TYPE=DESIGN`
>
> `BASE_COMMIT=a1d9c24a`；`WORKTREE=ua-phase1c-2`；`BRANCH=codex/ua-phase1c-2-20260724`

## 0. 人话摘要

Phase1C 把 UA 人工复盘从"自由文本/含糊的 yes-no"收口为**三个一级选项 + 可选原因码 + 预算方向/幅度候选 + 观察窗口 + 缺数据类型 + 脱敏备注**的标准反馈合同。所有反馈进 PGP append-only DB，旧反馈不覆盖、只追加 supersedes revision，并同步写 outbox event 供数仓离线消费。

关键约束：
- **不存在媒体执行接口**——反馈只记录"人类对这条机会的判断意图"，不直接调用 Google/Meta/AppLovin 改预算
- **原生复盘的 assignment/generation/exposure 可空**——历史上人工直接在 Notion/Slack 复盘的案例，没有 advisor 分桶、没有 generation、没有曝光，这些字段允许为 null，不算 schema 违规
- **继续观察不直接覆盖成实际未操作**——"继续观察"是一个主动决策语义，和"用户没填反馈"是两回事，不能把缺反馈当成"继续观察"

## 1. 三选项定义（human_decision 一级枚举）

`human_decision` 是 feedback 合同的唯一一级必填字段，取值固定三选一：

| 枚举值 | 中文 | 语义 | 是否需要预算候选 |
|---|---|---|---|
| `continue_observation` | 继续观察 | 当前证据不足以做预算动作，主动选择再等一个观察窗口；这不是"未操作" | 否 |
| `adjust_budget` | 调整预算 | 人类判断应改预算，并在 `budget_direction_candidate` / `budget_band_candidate` 给出方向和幅度候选 | 是 |
| `supply_data` | 补数据 | 当前决策被数据缺口阻断，人类选择先补数（指定 `missing_data_type`）再决策 | 否 |

约束：
- 三个值以外一律拒绝（schema error，不入 DB）
- `adjust_budget` 必须同时提供 `budget_direction_candidate` 和 `budget_band_candidate`，否则 reject
- `continue_observation` / `supply_data` 若误传预算候选，忽略不报错（防御性），但日志记 `unexpected_budget_candidate`

## 2. interaction_mode（反馈来源模式）

| 模式 | 含义 | assignment/generation/exposure 是否必填 |
|---|---|---|
| `organic` | 原生复盘：人工在日常流程中直接对 opportunity 提交反馈，没经过 advisor 渲染 | 可空 |
| `advisor_experiment` | advisor 实验模式：系统先做 assignment→generation→exposure，人工在看到证据包后反馈 | 必填 |

`interaction_mode` 是 feedback 的必填字段。它是后续策略评估时区分"行为策略数据"和"纯人工复盘数据"的唯一开关。

## 3. feedback 合同字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `feedback_id` | string(24) | 是 | 确定性 hash，`H("feedback", opportunity_id, recorded_at, interaction_mode)`；幂等键候选 |
| `supersedes_feedback_id` | string(24) \| null | 否 | 若本条是对先前反馈的修订，填被取代的 feedback_id；不填表示首版 |
| `opportunity_id` | string(24) | 是 | 关联 Phase1A DecisionOpportunity |
| `interaction_mode` | enum | 是 | `organic` \| `advisor_experiment` |
| `assignment_id` | string(24) \| null | 条件必填 | advisor 模式必填，organic 可空 |
| `generation_id` | string(24) \| null | 条件必填 | advisor 模式必填，organic 可空 |
| `exposure_id` | string(24) \| null | 条件必填 | advisor 模式必填，organic 可空 |
| `human_decision` | enum | 是 | `continue_observation` \| `adjust_budget` \| `supply_data` |
| `reason_codes` | array<string> | 否 | 多选原因码（见 §4） |
| `expected_window_days` | int | 否 | 仅 `continue_observation` 填，预期再观察 N 天；范围 1–30 |
| `budget_direction_candidate` | enum \| null | 条件必填 | `increase` \| `decrease` \| `hold`；`adjust_budget` 必填 |
| `budget_band_candidate` | enum \| null | 条件必填 | `small` \| `medium` \| `large`；`adjust_budget` 必填 |
| `missing_data_type` | enum \| null | 条件必填 | `cost_gap` \| `roi_gap` \| `cpi_gap` \| `config_gap` \| `attribution_gap`；`supply_data` 必填 |
| `free_note_sanitized` | string \| null | 否 | 脱敏后的自由备注（见 §5） |
| `recorded_at` | ISO8601 UTC | 是 | 反馈提交时间，UTC |
| `feedback_revision` | int | 是 | 同一 opportunity 的 revision 序号，首版=1，supersede 时 +1 |

## 4. reason_codes 受控词表（可选多选）

`reason_codes` 是开放但受控的多选词表，初始集合：

- `roi_below_target` / `roi_above_target`
- `cpi_too_high` / `cpi_too_low`
- `scale_plateau` / `scale_declining` / `scale_rising_fast`
- `budget_util_low` / `budget_util_high`
- `learning_phase_not_done`
- `creative_fatigue`
- `external_event`（节日/竞品/版本发布）
- `data_maturity_low`
- `config_drift`
- `other`（必须配合 `free_note_sanitized`）

词表可后续追加，但不删旧值；变更需 bump `schema_version`。

## 5. free_note_sanitized 脱敏规则

自由备注是 PII 高风险字段。规则：
- 入库前必须经过脱敏管道：邮箱、手机号、姓名、内部 IM 用户名、账户 ID 全部 token 化为 `<email>` / `<phone>` / `<name>` / `<im_user>` / `<account>`
- 不允许出现裸 URL 中的 query 参数（可能含 PII）
- 长度上限 2000 字符
- 脱敏后字符串入库；原文不落盘、不入 outbox、不入数仓

## 6. 七层分离

反馈合同严格遵循 UA 七层分离模型，字段到层映射：

| 层 | 字段 | 说明 |
|---|---|---|
| 1. assignment | `assignment_id` | advisor 把 opportunity 分到哪个分桶/策略组 |
| 2. generation | `generation_id` | 证据包生成版本（哪个 evidence bundle 被渲染） |
| 3. exposure | `exposure_id` | 证据包实际曝光给人工的事件 ID |
| 4. view | （不在本合同） | 人工实际是否看到、看多久——单独 view 事件表，不在 feedback 里 |
| 5. feedback | `feedback_id` / `human_decision` / `reason_codes` / `budget_*` / `expected_window_days` / `missing_data_type` / `free_note_sanitized` / `recorded_at` | 本合同主体 |
| 6. operation | （不在本合同） | 媒体侧实际执行的操作，由 CanonicalOperationEvent 承载 |
| 7. outcome | （不在本合同） | 决策结果指标，由 Outcome 承载 |

七层分离的目的是防止"反馈=操作"的隐含假设：人类填了 `adjust_budget` 不等于预算真的改了；operation 层独立观测。

## 7. 原生复盘（organic）字段可空规则

`interaction_mode=organic` 时：
- `assignment_id` / `generation_id` / `exposure_id` 允许为 null，不算 schema 违规
- `feedback_id` / `opportunity_id` / `human_decision` / `recorded_at` / `feedback_revision` 仍必填
- 策略评估时，organic 反馈只能进 `behavior_policy_era=v0_pre_advisor` 的样本，不能进 advisor A/B 评估

## 8. 不存在媒体执行接口

明确声明：本合同**不提供**任何媒体执行接口。`adjust_budget` 只是一个"人类候选意图"，不触发任何 Google/Meta/AppLovin API 调用。媒体执行仍走原 OperationEvent 链路（Phase0 CanonicalOperationEvent），由人工或既有自动化在媒体后台完成后再回流入仓。

这样设计的理由：
- 反馈与执行解耦，避免"反馈即执行"的因果捷径污染 uplift 估计
- 反馈可以比执行早（人工先表态再操作），也可以比执行晚（操作完了补录理由）
- outbox 只投递"反馈事实"，不投递"执行指令"

## 9. schema_version 与演进

- 当前 `schema_version = "ua_feedback_v0.1"`
- 字段新增：minor bump（v0.2），旧消费者忽略未知字段
- 枚举值新增：minor bump
- 字段语义变更 / 必填收紧：major bump（v1.0），必须双写期

## 10. 当前阶段限制

- 无物理 PGP DB，本合同用 `tools/scripts/ua_pgp_feedback_store.py` 内存版模拟
- 无 advisor 前端，`advisor_experiment` 模式仅靠测试 fixture 验证
- outbox event 由 feedback store 同步生成，导出合同见 UA-1C-05A
