# 包体 ROI 红线与达标线知识

> 机器可读阈值见 `PACKAGE_ROI_TARGET_THRESHOLDS.csv`；包体 `bundle_id` 映射见 `PACKAGE_BUNDLE_MAP.csv`（`prj_pag_list` 探测 + MI ROI360 页面字段字典补充，供预警脚本）。
> 数值首见于 2026-04 周报截图；2026-06-16 经《发行红绿线执行说明简化版（试运行）》DA 最终确认 18 行；2026-07-06 经用户输入更新为 21 行当前试运行阈值。当前状态保持 `trial_active`（试运行生效，按月 review）。历史来源 docx 入库见 `da_assets/raw/2026-06-16_发行红绿线执行说明_docx.md`。

## 时间元数据

```yaml
source_date: 2026-04           # 数值首见
confirmed_via: 发行红绿线执行说明简化版（试运行）
confirmed_date: 2026-06-16     # DA 最终(试运行)确认, 见 DA-26
updated_via: 用户输入包体阈值更新
updated_at: 2026-07-06
team_alignment_date: 2026-06-24
team_alignment_owner: 业务负责人（用户口头确认）
team_alignment_statement: >
  Agent 只预警、不自动投放；trial_active 红绿线可用于预警。
  阈值表外在投包无阈值时只标 missing_threshold，不猜测数值。
ingested_at: 2026-06-14
knowledge_status: trial_active # 试运行生效, 按月 review
validity:
  applies_to_period: true
  applies_to_current: true       # 试运行阶段作为当前红线/达标线
  needs_current_confirmation: false
  trial: true
caliber:
  roi_metric: ROI360
  revenue_source: sdk
  cost: cost_zhe
  organic: 包标准=all(含自然); 红线/达标线=paid_only(扣自然逆推)
source_type: redline_greenline_docx
latest_source_type: user_threshold_update
confidence: high
answers: DA问题已处理结论_20260628.md#DA-26（原 TODO/下周给DA的问题.md 已于 2026-07-14 归档）
archived_source: da_assets/raw/2026-06-16_发行红绿线执行说明_docx.docx
```

## 使用边界

| 项 | 说明 |
|---|---|
| 知识类型 | 2026-04 周报首见、2026-06-16 试运行确认，2026-07-06 用户更新后的红线 / 达标线知识；既保留历史来源，也可作为试运行当前阈值。 |
| 覆盖范围 | 当前 CSV 覆盖 21 个包体 × 平台，不代表全部业务包体。**阈值表外在投包一律标 `missing_threshold`，不猜测阈值。** |
| 当前治理用途 | 试运行阶段可作为当前红线/达标线**预警**依据（标 `trial`）；**已获团队口径确认（2026-06-24）：只预警、不自动投放。** |
| 生效日期 | 2026-06-16 试运行确认；2026-07-06 用户更新覆盖当前阈值，CSV 中 `effective_date=2026-07-06`。 |
| 数据量小 | 2026-07-06 更新未提供样本状态，CSV 中 `sample_status=not_provided`；不得沿用旧周报的 `small_sample` 观察标记。 |
| 冲突处理 | 若当前数据、当前阈值或业务口径与本表冲突，以最新 active 文档 / 用户拍板为准。 |

## 字段说明

| 字段 | 含义 |
|---|---|
| `package_name` | 包体 / 游戏名称。 |
| `platform` | `GP` 或 `iOS`。 |
| `package_standard_pct` | 截图中的“包维度标准”，单位为百分比点。 |
| `package_standard_note` | 包维度标准备注，如 `includes_vietnam_package`、`bottom_line`。 |
| `recovery_redline_pct` | 回收红线，低于此线表示公司无法接受的 ROI 下限。 |
| `delivery_recovery_target_pct` | 投放回收达标线，作为 UA 优化和放量目标线。 |
| `spend_30d_usd_wan` | 近 30 天月消耗，单位为万美元。 |
| `actual_overall_with_organic_pct` | 整体实际，含自然量。 |
| `actual_paid_excluding_organic_pct` | 投放实际，排除自然量。 |
| `redline_gap_pct_point` | 信息流目标 GAP：距离红线的百分比点差。 |
| `target_gap_pct_point` | 信息流目标 GAP：距离达标线的百分比点差。 |
| `overall_gap_pct_point` | 整体目标 GAP。 |
| `business_delivery_target_pct` | 业务制定的投放目标。 |
| `da_30d_reverse_target_pct` | DA 30 天数据反推目标；空值表示截图标注为数据量小或未给出。 |
| `da_30d_reverse_target_note` | DA 反推目标备注，如 `>=90`。 |
| `sample_status` | `normal`、`small_sample` 或 `not_provided`；当前 2026-07-06 阈值更新未提供样本状态。 |
| `source` | 来源标识。 |
| `status` | 知识状态；本表为 `trial_active`。 |
| `extracted_at` | 结构化日期。 |
| `effective_date` | 业务生效日期；未知时填 `unknown`。 |

## Agent 使用规则

1. 本表为 2026-06-16《发行红绿线执行说明（试运行）》确认并由 2026-07-06 用户更新的红线/达标线，可作为试运行阶段治理判断依据。
2. 口径前提（判断时必须随附）：ROI360%（含预估段）、全部 SDK 回收口径、`cost_zhe`；包维度标准=含自然量(all)，回收红线/投放达标线=排除自然量(paid_only) 逆推。
3. 包维度=包×渠道=日均>=1w campaign 同一套阈值（docx 明确不另加渠道修正系数）。
4. 判断时标 `threshold_status`（above_target / between_redline_target / below_redline）+ `trial` 标记；仍不替业务下最终停投/放量/降预算动作。
5. `sample_status=small_sample` 的包默认只观察，不触发红线强动作；`sample_status=not_provided` 表示本次阈值更新未提供样本状态，不能自动当作小样本豁免。
6. 风控黄线阈值、ROI 下修 buffer 仍无数值（见 DA-26 第 10/11 问），保持 `needs_risk_owner` / `algorithm_pending`。
7. 不把 21 行扩展为全部包体标准；新增在投包需补阈值。

## 版本流水 / 划线记录

> **当前阈值以 `PACKAGE_ROI_TARGET_THRESHOLDS.csv`（latest/current）为准。**
> 每次划线或更新阈值，必须同时向 `PACKAGE_ROI_TARGET_THRESHOLD_VERSIONS.csv` 追加一行记录，不得只覆盖当前表而不留历史。

机器可读版本流水见：`PACKAGE_ROI_TARGET_THRESHOLD_VERSIONS.csv`

字段说明：

| 字段 | 含义 |
|---|---|
| `version_date` | 本次划线 / 更新的日期（YYYY-MM-DD）。 |
| `event` | 本次变更事件描述。 |
| `row_count` | 本次版本的数据行数（不含 header）；首见截图未结构化时填 `unknown`。 |
| `status` | 本次版本的知识状态（如 `trial_active`、`historical_report_knowledge`）。 |
| `source` | 来源标识或文件路径。 |
| `effective_date` | 业务生效日期。 |
| `notes` | 补充说明，包括覆盖包体范围、口径变化、团队确认等。 |

已知版本流水摘要：

| version_date | event | row_count | status |
|---|---|---|---|
| 2026-04-01 | 首见于周报截图 | unknown | historical_report_knowledge |
| 2026-06-16 | 发行红绿线执行说明（试运行）DA 最终确认 | 18 | trial_active |
| 2026-06-24 | 团队口径确认：只预警不自动投放 | 18 | trial_active |
| 2026-07-06 | 用户输入更新为 21 行当前阈值 | 21 | trial_active |

**操作规范**：未来每次更新 `PACKAGE_ROI_TARGET_THRESHOLDS.csv`，必须同步在 `PACKAGE_ROI_TARGET_THRESHOLD_VERSIONS.csv` 追加一行，记录 `version_date`、`event`、`row_count`、`status`、`source`、`effective_date`、`notes`。版本流水 CSV 只追加，不删除历史行。
