# PI 吸收 ROI360 附件 Good Case 建设方案

## 元信息

| 项 | 内容 |
|---|---|
| ID | `sop_20260706_pi_absorb_roi360_attachment_good_case` |
| 状态 | `draft_for_runtime_absorption` |
| 来源 case | `../decision_cases/20260704_BB_GP_ROI360周六消耗下降附件分析案例.md` |
| 适用对象 | PI / Data Agent runtime、PI reviewer、真实问题验收集维护 |
| 目标 | 让 PI 学会把 ROI360 附件型业务问题组织成可信分析链，而不是只复述附件或直接查数 |
| 当前落地方式 | 文档 + answer contract + case 回链；本轮不改 runtime 代码 |

## 核心结论

这个 good case 的重点不是“7.4 到底为什么消耗下降”这个时效性数值结论，而是 Codex 在处理问题时体现出的分析编排能力：

1. 识别业务问题真实目标：解释消耗下降，而不是普通表格摘要。
2. 校验用户口径：用户说“同比”，但附件不含去年同期，不能伪造年同比。
3. 识别证据结构：两个 Excel 是同一批 ROI360 数据的不同粒度。
4. 选择可验证 baseline：改用附件内同为周六的 2026-06-27 vs 2026-07-04。
5. 先看总量三件套：消耗、注册、CPI。
6. 再做贡献拆解：国家、Campaign、国家 × Campaign。
7. 做反证检查：注册上升、CPI 改善时，不能说整体投放能力变差。
8. 标注证据等级：附件级 reviewed，不是 live verified。
9. 输出下一跳验证：live ROI360 / CK / 操作日志 / owner decision。
10. 交付并回填：把分析写入钉钉文档，并沉淀成 case。

PI 要吸收的是这条可信分析链，而不是背诵本次 7.4 的具体数值。

## PI 触发条件

满足以下任一条件时，PI 应启用本方案：

- 用户上传或引用 ROI360 导出 Excel，并要求解释消耗、ROI、注册、CPI、DNU 或 campaign 变化。
- 用户要求“按国家 / campaign / 国家+campaign / media_source 维度分析”。
- 用户说“同比 / 环比 / 周六 / 昨天 / 最近几天为什么下降”，但输入证据可能不支持该对比口径。
- 用户要求把结果输出到钉钉文档或沉淀成 case。

## 固定分析链

| 步骤 | PI 必须做什么 | 验收标准 |
|---|---|---|
| 1. 问题识别 | 判断是否为 ROI360 / 投放消耗下降归因问题 | 输出或 trace 中有 `question_type=roi360_spend_drop_diagnosis` |
| 2. 附件识别 | 识别文件类型、sheet、列头、日期范围、包体、粒度 | 能说明附件粒度，如 `campaign`、`country_campaign` |
| 3. 口径校验 | 判断用户说的同比 / 环比 / 同周序是否被附件支持 | 若缺去年同期，必须标 `baseline_missing_for_year_over_year` |
| 4. baseline 选择 | 选择附件内可验证的临时基准 | 必须说明“本次按附件内同为周六对比，不等于年同比” |
| 5. 总量判断 | 汇总消耗、注册、CPI，必要时列行数 | 必须同时输出 cost / registers / CPI，不能只看消耗 |
| 6. 贡献拆解 | 输出国家、Campaign、国家 × Campaign 三层正负贡献 | 必须包含 top drops 和 top offsets |
| 7. 反证检查 | 检查注册和 CPI 是否支持“整体变差” | 注册上升或 CPI 改善时，必须避免“整体投放变差”结论 |
| 8. 成熟度判断 | 判断 ROI / 收入字段是否能解释近端日期 | 近端 cohort 收入/ROI 不成熟时必须标风险 |
| 9. 证据分级 | 标注附件、MI、CK、MC、操作日志分别支撑什么 | 必须输出 `attachment_reviewed` 或更高等级 |
| 10. 下一跳验证 | 生成 live 数据和操作记录复核清单 | 必须包含 `live_roi360_or_ck_validation`、`operation_log_check`、`needs_decision` |
| 11. 交付回填 | 若写入文档或 case，记录 URL、附件、证据表和状态 | index / case 中保留 source、output、status |

## Answer Contract

PI 回答这类问题时，至少包含以下模块：

```text
问题识别：
口径与 baseline：
数据来源与证据等级：
总体变化：
国家贡献：
Campaign 贡献：
国家 × Campaign 定位：
反证检查：
风险与不确定性：
下一跳验证：
needs_decision：
```

必须包含：

- `折后消耗`
- `注册设备(af)` 或等价注册分母
- `CPI`
- 对比窗口
- 国家贡献
- Campaign 贡献
- 国家 × Campaign 贡献
- `attachment_reviewed`
- `live_data_verified=false` 或已验证状态
- `operation_log_checked=false` 或已检查状态
- `needs_decision`

禁止包含：

- 在缺去年同期数据时声称已完成年同比。
- 把附件 reviewed 数值说成 live verified。
- 把 US 独立日、预算调整、出价策略、学习期变化写成确定原因，除非有操作日志或 owner 证据。
- 输出最终停投、放量、降预算动作。

## 可审计推理路径

PI 不需要暴露原始思维流，但应在 trace / metadata / 答案摘要中保留可审计路径：

| Trace 字段 | 示例值 | 用途 |
|---|---|---|
| `question_type` | `roi360_spend_drop_diagnosis` | 判断问题类型 |
| `input_source_type` | `roi360_excel_export` | 区分附件、live SQL、MI API |
| `detected_grains` | `campaign,country_campaign` | 说明附件粒度 |
| `requested_baseline` | `yoy` | 用户声称口径 |
| `baseline_supported` | `false` | 防止伪造同比 |
| `selected_baseline` | `same_weekday_previous_week` | 说明实际对比 |
| `evidence_level` | `attachment_reviewed` | 证据等级 |
| `live_data_verified` | `false` | 是否 live 复核 |
| `operation_log_checked` | `false` | 是否查操作记录 |
| `next_hops` | `live_roi360_or_ck_validation,operation_log_check,owner_decision` | 后续验证 |

## 附件解析改进要求

本 case 暴露的具体工程问题：

- 文件扩展名是 `.xls`，但实际是 xlsx package。
- 普通 workbook reader 可能被错误 worksheet dimension 误导，只读出 A1。
- 真实数据在 sheet XML 中，有 1,000+ / 31,000+ 行。

因此 PI 的附件解析能力应支持：

```json
{
  "file_type": "xlsx_package_with_xls_extension",
  "dimension_trust": "low",
  "read_strategy": "reset_dimensions_or_parse_sheet_xml",
  "grain_detection": ["campaign", "country_campaign"],
  "required_columns": ["投放日期", "包体", "Campaign", "折后消耗", "注册设备(af)"],
  "optional_columns": ["国家和地区", "累计变现收入$", "ROI360"]
}
```

当前不直接改代码，但后续 runtime / worker 若要支持附件自动处理，应以这段能力要求生成工程任务。

## 真实问题验收落点

本 SOP 对应验收 case：

- `eval/真实问题验收集/cases.yaml` 中的 `RWC_20260706_001`

该 case 不要求 PI 复现完全相同数值，但要求 PI 产出同样的分析结构和证据边界：

- 识别附件不支持年同比。
- 使用可验证同周六口径。
- 识别两个附件不同粒度。
- 输出总量、国家、Campaign、国家 × Campaign 三层。
- 标注附件 reviewed，live 未验证。
- 输出下一跳验证和 `needs_decision`。

## 后续代码改造计划

本轮先不改代码。若要把这个 good case 吸收到 PI runtime，建议拆成以下工程任务：

| 优先级 | 任务 | 验收方式 |
|---|---|---|
| P0 | 在 PI prompt / route profile 中加入 ROI360 附件型消耗下降 answer contract | `RWC_20260706_001` 回归通过 |
| P0 | 增加附件 metadata 解析器，识别 xlsx package with .xls extension 和真实 worksheet dimension | 能解析本 case 两个附件，并输出粒度/日期/列头 |
| P1 | 在 trace metadata 中记录 evidence_level、baseline_supported、selected_baseline、live_data_verified | replay trace 可审计 |
| P1 | 增加贡献拆解 helper：date summary、country、campaign、country_campaign、positive/negative offset | 输出结构化 evidence table |
| P1 | 增加下一跳推荐器：Google Ads 操作日志、live ROI360/CK、owner decision | 答案包含 pending checks |
| P2 | 钉钉输出与 case 回填自动化 | 文档 URL、case path、index entry 可追溯 |

## 与现有 PI 复核 SOP 的关系

- `PI查询执行复核护栏.md` 解决“查数 / SQL / 0 行 / query_records”执行质量。
- `20260623_PI调用日志复核与线上回归SOP.md` 解决“复核线上 trace / replay / 修 runtime”。
- 本 SOP 解决“PI 如何吸收一个高质量业务分析 good case，并把它变成 answer contract 和 runtime 能力要求”。

三者关系：

```text
good case -> 本 SOP 定义答案合同和推理路径
answer contract -> 真实问题验收集约束 PI 输出
PI 执行 / replay -> 用现有 PI 复核 SOP 检查 trace、工具和落库
```
