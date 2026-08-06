# UA 决策行为沉淀 Phase0 Opportunity 与标签合同（UA-P0-07）

> 状态：`frozen_candidate`
>
> 日期：`2026-07-23`
>
> `TASK_ID=UA-P0-07`；`TASK_TYPE=IMPLEMENTATION`；`BASE_COMMIT=20018f69`
>
> 权威方案：第 4.3、5.2、8.11 节
>
> 合并来源：P0-03（MI 接口）、P0-04（来源覆盖矩阵）、P0-06（OperationEvent 合同）

## 0. 人话摘要

这个任务冻结"什么时候算一次决策机会"和"怎么给这次机会打标签"的规则。

核心规则：
- **两类决策机会**：每天固定复盘（所有活跃 Campaign）+ 异常触发（ROI/消耗/利润出问题时）
- **24 小时标签窗口**：窗口内发生的预算动作关联到该机会
- **三套标签互不混淆**：实际动作（observed_treatment）、人工决定（human_decision）、审核状态（review_status）
- **"没查到日志"永远不能直接生成"未操作"真值**——必须证明覆盖完整

## 1. DecisionOpportunity 生成规则

### 1.1 两类机会

| 机会类型 | 生成时点 | 覆盖范围 | trigger_reason_code |
|---|---|---|---|
| `scheduled_review` | 每日固定时点（建议北京时间 10:00） | 所有活跃且满足最低数据条件的 DecisionSubject | `scheduled_daily` |
| `anomaly_triggered` | 异常检测首次可见时间 | 触发异常的 DecisionSubject | `roi_below_threshold` / `cpi_above_threshold` / `cost_spike` / `profit_drop` / `lifecycle_change` / `data_quality` |

### 1.2 最低数据条件（scheduled_review）

一个 DecisionSubject 要生成 `scheduled_review` 机会，需同时满足：
- 过去 3 天有消耗（`cost_zhe > 0`）
- Campaign 状态为活跃（`status = ENABLED/ACTIVE`）
- 有至少 7 天历史数据（`launch_days >= 7`）

具体 cutoff 值在 P0-08（as-of 特征审计）后用 live 数据校准。

### 1.3 去重规则

同一 DecisionSubject 的 `scheduled_review` 和 `anomaly_triggered` 在 24 小时内过近时：
- 保留一个主 Episode
- 记录多个 `trigger_reason_codes`
- 不生成两个相互重叠的 treatment 样本

去重键：`dedupe_group_id = H(decision_subject_id, date)`，同一对象同一天只保留一个主机会。

## 2. 24 小时标签窗口

### 2.1 窗口定义

- **窗口起始**：`opportunity.as_of_ts`
- **窗口结束**：`as_of_ts + 24 hours`
- 窗口内发生的 OperationEvent（P0-06 定义的 CanonicalOperationEvent）关联到该机会

### 2.2 窗口用途限制

24 小时标签窗口**只用于**定义"UA 在决策机会后选择了什么动作"（行为标签）。

**不能用于** Uplift 的 treatment 生效窗口——Uplift 必须使用精确 `action_at`（P0-06 的 `change_at`），或对允许在 24h 内开始 treatment 的 grace period 使用预注册的 landmark/clone-censor-weight 方法，避免 immortal-time bias。

## 3. 三套标签定义

### 3.1 `observed_treatment`（实际动作）

| 值 | 定义 | 来源 |
|---|---|---|
| `no_budget_change` | 窗口内无预算变化，且来源覆盖完整 | coverage_run complete + 无 OperationEvent |
| `budget_decrease_large` | `change_pct <= -30%` | OperationEvent 的 `change_pct` |
| `budget_decrease_small` | `-30% < change_pct < 0%` | 同上 |
| `budget_increase_small` | `0% < change_pct <= 30%` | 同上 |
| `budget_increase_large` | `change_pct > 30%` | 同上 |
| `unknown` | 覆盖不完整、资源缺失、复合动作、或来源不可用 | coverage_run incomplete |

### 3.2 `human_decision`（人工决定）

| 值 | 定义 | 来源 |
|---|---|---|
| `continue_observe` | UA 明确选择继续观察 | PGP 三选项反馈（Phase 1C 上线后）或经审计的历史备注 |
| `adjust_budget` | UA 明确选择调整预算 | 同上 |
| `need_data` | UA 明确选择补数据 | 同上 |
| `unobserved` | 没有显式反馈 | 默认值 |

### 3.3 `review_status`（审核状态）

| 值 | 定义 |
|---|---|
| `explicit` | 有 PGP 显式反馈或经审计的当时人工决定 |
| `inferred` | 从备注或操作模式推断，但无显式反馈 |
| `not_observed` | 没有任何反馈或备注记录 |

## 4. 派生标签

### 4.1 `reviewed_no_action`

条件（全部满足）：
1. `human_decision = continue_observe`
2. `review_status = explicit`
3. `observed_treatment = no_budget_change`
4. 来源覆盖完整

**用途**：案例检索、显式人工决策模仿；满足其他条件时可作 Uplift 未处理样本。

### 4.2 `observed_no_budget_change`

条件（全部满足）：
1. `observed_treatment = no_budget_change`
2. 来源覆盖完整
3. 但 `review_status != explicit`（没有显式反馈）

**用途**：事实时间线；满足 eligibility 时可作 Uplift 未处理机会。**不可冒充显式行为模仿标签**。

### 4.3 `action_unknown`

条件：
- `observed_treatment = unknown`（覆盖不完整、资源缺失、复合动作、来源不可用）

**用途**：仅保留事实与缺口。**不进入**模仿或 Uplift。

## 5. 来源覆盖完整性认定

### 5.1 `observed_no_budget_change=true` 的必要条件

1. 决策标签窗口内所有相关 endpoint（`ua-operates` + `ua-remarks`）的 `coverage_run` 状态为 `complete`
2. 没有生效的 Campaign/共享预算/AdSet/国家预算变化
3. 没有会直接改变该 DecisionSubject 供给的并行动作
4. 对象未因删除、失访、采集失败或接口异常消失
5. 自动动作和人工动作的来源能够识别或明确标记未知

### 5.2 coverage_run 状态

| 状态 | 含义 | 能否生成 `no_budget_change` |
|---|---|---|
| `complete` | 全部分页 + terminal cursor + 全部预算资源 + 完整标签窗口 | ✅ |
| `partial` | 部分页缺失或未到 terminal cursor | ❌ → `observed_treatment=unknown` |
| `failed` | 接口请求失败 | ❌ → `observed_treatment=unknown` |
| `empty_success` | 成功返回空页（has_more=false, rows=[]） | ✅（空结果 ≠ 无操作，但空结果 + complete coverage = 可信无操作） |

### 5.3 各平台覆盖来源

| 平台 | coverage 来源 | 当前状态 |
|---|---|---|
| Google | `ods_market_google_ads_config_wide_hi`（change event 宽表，dt/hour 分区） | `live_verified` |
| Meta | MI `ua-operates`（campaign_name + date + limit/offset 分页） | `live_verified`（分页有效，但需全量分页验证 terminal cursor） |
| AppLovin | MC 配置快照差分（dt 日分区） | `live_verified`（但只能检测日级变化，不能证明"24h 内无操作"） |

**AppLovin 特殊规则**：由于 AppLovin 只有日级快照差分，无法证明"24 小时窗口内无操作"——`observed_no_budget_change` 对 AppLovin 固定为 `false`，`observed_treatment` 固定为 `unknown` 或快照差分推断值。

## 6. exclusion_reasons 规则

| 排除原因 | 条件 | 影响的用途 |
|---|---|---|
| `compound_action` | 24h 内多次预算调整 | Uplift |
| `source_unavailable` | coverage_run failed/partial | 全部用途 |
| `inferred_only` | evidence_tier=inferred_only（AppLovin） | IMITATION + Uplift |
| `no_explicit_label` | review_status != explicit | IMITATION |
| `unknown_origin` | operation_origin=unknown | Uplift |
| `platform_automation` | operation_origin=platform_automation | Uplift（只纳入 human_ua） |
| `interference` | 同账户/shared budget 并行变化 | Uplift |
| `insufficient_data` | 历史数据不足 7 天 | 全部用途 |

## 7. 正例/负例/边界样本

| 样本 | 描述 | 预期标签 |
|---|---|---|
| 正例：显式继续观察且无操作 | PGP 反馈 `continue_observe` + coverage complete + 无 OperationEvent | `reviewed_no_action=true`, `observed_treatment=no_budget_change`, `human_decision=continue_observe`, `review_status=explicit` |
| 正例：显式调预算且执行 | PGP 反馈 `adjust_budget` + OperationEvent 有 `change_pct=+50%` | `observed_treatment=budget_increase_large`, `human_decision=adjust_budget`, `review_status=explicit` |
| 负例：MI 空结果但 coverage incomplete | `ua-operates` 返回 0 行，但分页未到 terminal cursor | `observed_treatment=unknown`, **不能**标 `no_budget_change` |
| 负例：MI 接口失败 | HTTP 5xx | `observed_treatment=unknown`, `exclusion_reasons=source_unavailable` |
| 边界：AppLovin 无操作 | 快照差分无变化 | `observed_treatment=unknown`（不能证明 24h 内无操作）, `exclusion_reasons=inferred_only` |
| 边界：compound action | 24h 内 3 次预算调整 | `observed_treatment=unknown`, `exclusion_reasons=compound_action` |

## 8. 非目标声明

本任务未创建物理表；未执行 DDL/DML；未部署；未签发 `GO_*`。分桶阈值（±30%）为候选版本，待 P0-09 用真实分布校准。
