# UA 决策行为沉淀 Phase1C 三选项 UI 合同（UA-1C-04）

> 状态：`design_candidate`
>
> 日期：`2026-07-24`
>
> `TASK_ID=UA-1C-04`；`TASK_TYPE=DESIGN`
>
> `BASE_COMMIT=a1d9c24a`；`WORKTREE=ua-phase1c-2`

## 0. 人话摘要

定义人工复盘界面上"三选项反馈"的 UI 合同：一级三选项必选 + 可选原因码多选 + 预算方向/幅度桶 + 观察窗口 + 缺数据类型 + 脱敏自由备注。明确**无媒体写入口**——界面只产出反馈记录，不调用任何媒体 API。明确**继续观察 ≠ 实际未操作**——主动选"继续观察"和"用户没填"是两回事。

## 1. 一级三选项（必选，单选）

UI 顶部三个互斥按钮：

| 选项 | 值 | 选中后展开 |
|---|---|---|
| 继续观察 | `continue_observation` | 观察窗口输入 |
| 调整预算 | `adjust_budget` | 方向桶 + 幅度桶 |
| 补数据 | `supply_data` | 缺数据类型单选 |

- 必选其一才能提交
- 默认不预选（防止锚定偏差）
- 三选项以外不允许自定义

## 2. 可选原因码（多选）

折叠面板，选中一级选项后展开。多选，可空。词表见 UA-1C-01 §4。

- `roi_below_target` / `roi_above_target`
- `cpi_too_high` / `cpi_too_low`
- `scale_plateau` / `scale_declining` / `scale_rising_fast`
- `budget_util_low` / `budget_util_high`
- `learning_phase_not_done`
- `creative_fatigue`
- `external_event`
- `data_maturity_low`
- `config_drift`
- `other`（强制弹出备注框）

`other` 必须配合 `free_note_sanitized`，否则提交禁用。

## 3. 预算方向/幅度桶（adjust_budget 必填）

`adjust_budget` 选中后展开两段：

### 3.1 方向桶 `budget_direction_candidate`（单选必填）
- `increase` 增预算
- `decrease` 降预算
- `hold` 维持（仍归入 adjust_budget：人类主动确认维持，区别于 continue_observation）

### 3.2 幅度桶 `budget_band_candidate`（单选必填）
- `small` 小幅（±10% 以内）
- `medium` 中幅（±10%–30%）
- `large` 大幅（±30% 以上）

UI 不要求填具体数值——数值在 operation 层由媒体执行时观测，反馈层只收桶。

## 4. 观察窗口（continue_observation 可选）

`continue_observation` 选中后展开 `expected_window_days` 输入：
- 数字输入框，范围 1–30
- 单位"天"
- 可空（空表示"无明确预期"）

## 5. 缺数据类型（supply_data 必填）

`supply_data` 选中后展开 `missing_data_type` 单选：
- `cost_gap` 消耗数据缺失
- `roi_gap` ROI 数据缺失
- `cpi_gap` CPI 数据缺失
- `config_gap` 配置数据缺失
- `attribution_gap` 归因数据缺失

必选其一。

## 6. 自由备注（脱敏）

所有三个选项下都可填自由备注：
- 文本框，上限 2000 字符
- 提交前前端不做脱敏，**入库前服务端脱敏**（见 UA-1C-01 §5）
- 原文不入库
- UI 提示文案："备注将自动脱敏，请勿填写敏感个人信息（邮箱/手机号/账户ID）"

## 7. 无媒体写入口

明确声明：
- 提交按钮只调用 `submit_feedback` 接口
- UI 上**不存在**任何"直接改预算"、"直接暂停"、"直接改出价"的按钮
- `adjust_budget` 选中后不出现"立即执行"选项
- 媒体执行仍走原 OperationEvent 链路，由人工或既有自动化在媒体后台完成

这样设计的理由：
- 反馈与执行解耦，避免 UI 一步到位的执行污染 uplift 估计
- 人工在 UI 表态后，仍需去媒体后台执行，operation 层独立观测这个时间差

## 8. 继续观察 ≠ 实际未操作

关键语义区分：

| 状态 | 含义 | UI/数据表现 |
|---|---|---|
| 人工主动选"继续观察" | 人类看了证据后主动决策：再等一个窗口 | feedback 记录 `human_decision=continue_observation` |
| 用户没填反馈 | 人工没看/没填 | 无 feedback 记录，`has_feedback=false` |
| 人工填了 adjust_budget 但没去媒体后台执行 | 表态改但实际没改 | feedback=adjust_budget，operation 层无对应事件 |

三者不可混同。UI 上"继续观察"按钮的文案是"继续观察（再等一个窗口）"，不是"暂不操作"——防止被理解成"未操作"。

## 9. 提交校验规则（前端）

| 条件 | 校验 |
|---|---|
| 一级选项未选 | 提交禁用 |
| adjust_budget 未选方向桶或幅度桶 | 提交禁用 |
| supply_data 未选缺数据类型 | 提交禁用 |
| reason_codes 含 other 但备注为空 | 提交禁用 |
| 备注超 2000 字符 | 提交禁用 |
| expected_window_days 超出 1–30 | 提交禁用 |

## 10. 交互模式标记

UI 根据进入路径自动标记 `interaction_mode`：
- 从 advisor 证据包进入 → `advisor_experiment`，自动带 assignment_id / generation_id / exposure_id
- 从日常复盘列表进入 → `organic`，三字段为空

用户不可手动切换 interaction_mode（防止污染策略评估）。

## 11. 当前阶段实现

- 无前端实现，本合同为后续 advisor UI / 复盘台 UI 的设计输入
- 反馈提交接口由 `ua_pgp_feedback_store.py` 提供，UI 合同与 store 字段一一对应
- 测试用 fixture 模拟 UI 提交的 payload
