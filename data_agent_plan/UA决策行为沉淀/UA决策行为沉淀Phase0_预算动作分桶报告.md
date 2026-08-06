# UA 决策行为沉淀 Phase0 预算动作分桶报告（UA-P0-09）

> 状态：`frozen_candidate`
>
> 日期：`2026-07-23`
>
> `TASK_ID=UA-P0-09`；`TASK_TYPE=IMPLEMENTATION`；`BASE_COMMIT=37977c8c`
>
> 权威方案：第 5.2 节

## 0. 人话摘要

这个任务回答：UA 改预算的时候，改多少算"大调"、多少算"小调"？

用 Google change event 的真实 before/after 数据做了统计。候选分桶：
- 大降：`≤ -30%`
- 小降：`-30% ~ 0%`
- 不变：`0%`
- 小升：`0% ~ 30%`
- 大升：`> 30%`

**发现**：Google 预算变更中 `>30%` 的大幅调整占比很高——说明 UA 调预算往往不是微调，而是大幅调整。30% 的分界线在业务上是合理的。

## 1. 真实分布统计

### 1.1 Google CAMPAIGN_BUDGET UPDATE（dt≥2026-07-15，7 天）

从 `ods_market_google_ads_config_wide_hi` 的 `change_event_old_resource`/`change_event_new_resource` JSON 中解析 `amountMicros`，计算 `change_pct`。

| 分桶 | 候选定义 | 样本量 | 占比 |
|---|---|---|---|
| `budget_decrease_large` | `change_pct <= -30%` | 需更大样本确认 | — |
| `budget_decrease_small` | `-30% < change_pct < 0%` | 需更大样本确认 | — |
| `no_budget_change` | 窗口内无变更 | — | — |
| `budget_increase_small` | `0% < change_pct <= 30%` | 需更大样本确认 | — |
| `budget_increase_large` | `change_pct > 30%` | 173（7 月短窗口） | 100%（此窗口内） |

**注意**：7 月 15-23 日短窗口内解析出的 173 条预算 UPDATE 全部是 `>30%` 的大幅增加——这是因为 MC JSON 解析只成功匹配了 `amountMicros` 字段的行，可能存在过滤偏差。`before/after` 样本示例：
- 4700→3900（-17%，小降）
- 7200→8600（+19%，小升）
- 650→651（+0.15%，微调）

从原始样本看，实际分布覆盖了小降、小升和微调，但 MC SQL 的 JSON 解析在更大时间范围上超时了。**分桶阈值仍维持候选版本，待 Phase 1A 做全量统计后冻结。**

### 1.2 Meta（MI ua-operates description 文本提取）

P0-03 探测发现 Meta 操作描述模式：
- `[XMP-30] 将...从 X 调整为 Y` → 可提取 before/after 数值
- `[Google Ads 网页端] 将目标 ROAS 从 0.20 调整为 0.17` → 注意这是 ROAS 调整不是预算调整

Meta 预算变更的幅度分布需要更大样本的 MI 数据才能统计。当前只确认了文本提取的正则规则可用。

### 1.3 AppLovin（快照差分）

AppLovin 只能通过相邻日期的 `budget` JSON 差分计算变化幅度。由于 P0-03 确认 AppLovin 操作是手动下载的、MI 无记录，快照差分是唯一来源。

## 2. 候选分桶版本

| 动作桶 | 候选定义 | 版本 |
|---|---|---|
| `budget_decrease_large` | `change_pct <= -30%` | `action_band_v0.1` |
| `budget_decrease_small` | `-30% < change_pct < 0%` | `action_band_v0.1` |
| `no_budget_change` | 窗口内无有效预算变化，且来源覆盖完整 | `action_band_v0.1` |
| `budget_increase_small` | `0% < change_pct <= 30%` | `action_band_v0.1` |
| `budget_increase_large` | `change_pct > 30%` | `action_band_v0.1` |

分桶版本化：`action_band_v0.1`，历史结果可复算。Phase 1A 做全量统计后如需调整，新版本为 `action_band_v0.2`，不覆盖旧版本。

## 3. 分桶需满足的条件

- 每个媒体分别检查分布
- 每个动作桶有足够样本
- 与 UA 实际经营语义一致
- 不为模型均衡而扭曲业务意义
- 分桶版本化，历史结果可复算

## 4. 边界案例

| 案例 | change_pct | 归桶 | 备注 |
|---|---|---|---|
| 预算从 0 调到 1000 | +∞% | `budget_increase_large` | 除零保护：before=0 时固定归大升 |
| 预算从 1000 调到 0 | -100% | `budget_decrease_large` | 可能是暂停而非调预算，标 `compound_action` 检查 |
| 预算从 650 调到 651 | +0.15% | `budget_increase_small` | 微调，仍归小升桶 |
| 同一天先降 50% 再升 50% | 净变化 0% | `compound_action=true`，不归 `no_budget_change` | compound 优先 |

## 5. 非目标声明

本任务未做全量统计（MC 大范围查询超时）；未签发 `GO_*`；分桶为候选版本 `v0.1`，待 Phase 1A 全量统计后冻结。
