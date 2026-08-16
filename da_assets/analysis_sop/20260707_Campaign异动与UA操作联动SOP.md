# Campaign 异动与 UA 操作联动 SOP

## 元信息

| 项 | 内容 |
|---|---|
| ID | `sop_20260707_campaign_anomaly_ua_operation_linkage` |
| 状态 | active |
| 生成日期 | 2026-07-07 |
| 适用路由 | `roi_or_campaign_analysis`、`google_ads_config_change_analysis` |
| 来源 | 钉钉文档《Campaign 全览计划详情页宣讲》、分析平台 `分析平台/campaign-overview` 代码、`Campaign全览分析协议.md`、`20260705_投放看板模块知识沉淀SOP.md` |

本 SOP 解决一个固定问题：未来用户问“数据为什么异动”时，Agent 不能只拆 ROI / DNU / CPI / 素材 / 国家；必须检查同窗口 UA 操作历史。反过来，用户问“UA 做了某个操作效果怎么样”时，Agent 不能只复述操作记录；必须补操作前后的数据表现。用户问某段时间的 Campaign 数据、表现或趋势时，若该时间窗内存在 UA 操作，也必须一起带出操作摘要与操作前后数据。

## 适用边界

适用：

- 单个 Campaign 的 分析平台、消耗、CPI、DNU、注册、预估利润、ROI 倍率、素材、国家或 cohort 异动。
- 单个 Campaign 某段时间的数据、表现、趋势、日报或阶段复盘；若窗口内有 UA 操作，必须联动展示。
- 用户明确问 UA 历史、操作历史、调价、控量、放量、预算、状态、出价、素材调整后的效果。
- 分析平台 Campaign 全览页面里的 `UA 历史`、`关键操作影响`、`分析平台 与消耗` 时间轴解释。
- Google Ads campaign / ad_group / ad 层异动，需要进一步读取平台 change log。

不适用：

- 未定位到 Campaign 粒度的大盘问题；先走普通 ROI / DNU / media_source / country 拆解。
- 用户明确要求“只返回数据明细”或“只查操作日志，不分析关联”；此时可以只返回用户指定内容，但必须标注未验证 UA 操作关联或前后数据效果。
- 自动停投、放量、降预算或广告平台写操作。

## 三入口规则

| 用户入口 | 必须补齐 | 输出重点 |
|---|---|---|
| 数据异动入口：ROI / DNU / CPI / 消耗 / 利润 / 留存突然变了 | 同窗口 UA 操作历史、操作类型、操作前后窗口指标 | “指标先变在哪里，附近有什么操作，调后是否改善或恶化” |
| 操作复盘入口：UA 调价 / 控量 / 放量 / 改预算 / 改状态 / 备注后怎么样 | 操作日前后 分析平台、消耗、CPI、利润、DNU / 注册、国家 / 素材结构 | “操作后数据是否朝预期方向变化，但不直接声称因果” |
| 时间段数据入口：用户问某 Campaign 某段时间数据、表现、趋势、日报或阶段复盘 | 该时间窗内 UA 操作摘要；命中操作时补操作日前后指标 | “先给时间段整体表现，再说明窗口内是否有人动过，以及动前动后指标如何变化” |

任何一个入口都不能单边输出。数据异动必须带操作检查；操作复盘必须带前后数据；时间段数据查询若命中 UA 操作，必须带操作摘要和操作前后数据。用户明确只要数据明细或只要日志时，分别标 `ua_operation_linkage_unchecked` 或 `pre_post_data_unchecked`。

## 必填参数

| 参数 | 规则 |
|---|---|
| `campaign_name` / `campaign_id` | 至少一个；优先使用能稳定对齐的 id，名称仅作展示或兜底 |
| `bundle_id` | 分析平台 / 分析平台 scope 必填；不能猜包体 |
| `media_source` | 若页面 scope 已解析则使用；若用户只问 Google 操作，必须确认 `googleadwords_int` 或 Google account / customer |
| `active_date_range` | 异动或数据观察窗口，默认不超过 60 天；普通页面分析默认近 14 天，并用于筛选同窗口 UA 操作 |
| `operation_window` | 操作前后对比窗口；默认前 3 天 vs 操作日起 3 天 |
| `metric_set` | 默认 `分析平台 / cost / CPI / estimated_profit / 分析平台_ROI1_multiplier`；DNU 问题追加 installs / registers |
| `revenue_source` | 默认 `sdk`，不确定时 SDK / AF 并列或标 `revenue_source_uncertain` |
| `forecast_version` | 示例产品 默认 `v6_sdk`，非 示例产品 使用页面 / MI 当前可用版本；必须输出来源 |

## 标准窗口

| 窗口 | 定义 | 用途 |
|---|---|---|
| `pre_3d` | 操作日前 3 个有数自然日，不含操作日 | 估计操作前表现 |
| `post_3d` | 操作日起 3 个有数自然日，含操作日 | 估计操作后表现 |
| `pre_7d` / `post_7d` | 样本太小或业务要求更稳时使用 | 降低单日波动 |
| `baseline_7d` | 异动日前 7 天 | 判断异动幅度 |
| `anomaly_window` | 用户指出的异动日 / 异动周期 | 识别主问题 |

默认使用 `pre_3d` / `post_3d` 是为了和 分析平台 `CampaignDataOverview.vue` 的 `buildOperationImpact()` 保持一致。若数据太稀疏、日耗低、cohort 未成熟，应升级为 `pre_7d` / `post_7d` 或只标观察。

## 指标计算

| 指标 | 窗口聚合规则 |
|---|---|
| `cost` | 窗口内折后消耗求和 |
| `registers` / `DNU` | 窗口内求和；DNU 必须排除 `示例产品` 迟到分区风险 |
| `CPI` | `sum(cost) / sum(registers)` |
| `分析平台` | 优先 `sum(revenue_359) / sum(cost) * 100`；无 revenue 时按 cost 加权 ROI |
| `estimated_profit` | `sum(cost * (分析平台 / 100 - recycle_target_line))` |
| `分析平台 / ROI1` | 窗口内日级倍率均值，要求 ROI1 分母非 0 |
| `top_country_cost_share` | 国家 cost / Campaign cost |
| `top_material_cost_share` | 素材 cost / Campaign cost |

所有窗口结果必须输出分母：`cost`、`registers` 或有效行数。分母不足时标 `sample_too_small`。

## 数据源优先级

| 需求 | 默认来源 | 说明 |
|---|---|---|
| 分析平台 页面级 Campaign 指标 | 分析平台 Campaign Overview / CK ROI cohort / 分析平台 | 优先复用已验证页面链路；当前代码存在 CK-first ROI cohort 路径 |
| UA 历史 / 备注 / 操作 | 分析平台 `POST /v1/campaign-overview/history` / MI campaign history | 适合页面级复盘 |
| Google 平台配置变更 | `IAA Game Studio.示例表` | 需要 `customer_id + campaign_id`，只输出聚合变更 |
| 素材表现 | MI `asset_report` / Campaign Overview materials | 判断素材集中和用户质量 |
| 国家贡献 | Campaign Overview Top15 country / CK forecast fallback | forecast partial 时不能给强结论 |
| DNU / activation | MaxCompute AF install / 已验证 DNU SQL | 必须扫到 latest partition 或至少 T+1 |

## 分析步骤

### A. 数据异动入口

1. 定义异动对象：Campaign、包体、渠道、国家、日期。
2. 先做 freshness / 成熟度检查，确认不是数据未到、forecast 落表时序或低样本。
3. 拆主指标：
   - 分析平台 下滑：看 cost scale、CPI、ROI 倍率、留存、国家、素材。
   - DNU / registers 下滑：看 media / country / campaign / DNU 迟到分区。
   - 消耗突变：看 ROI / CPI / 利润是否同向改善或恶化。
4. 查 UA 历史：
   - 分析平台 页面级先查 `/v1/campaign-overview/history`。
   - Google 对象级再查 change log。
5. 只保留异动日前后窗口内的操作作为候选证据。
6. 对每个候选操作计算 `pre_3d` vs `post_3d` 指标变化。
7. 输出“主异动事实 + 同窗口操作候选 + 前后数据变化 + 因果边界”。

### B. UA 操作复盘入口

1. 先解析操作：时间、类型、字段、before / after、来源。
2. 判断操作来源可信度：
   - 结构化字段：`field / before / after` 明确。
   - 文本推断：从 title / body 中推断，必须标 `inferred_only`。
   - 备注：只能作上下文，不能当执行动作。
3. 用操作日构造 `pre_3d` 和 `post_3d`。
4. 补指标变化：
   - 放量 / 加预算：看 cost 是否上升，同时 ROI / 利润是否保持。
   - 控量 / 降预算 / pause：看 cost 是否下降，同时亏损是否收窄。
   - 出价 / tROAS / tCPA：看 CPI、分析平台、registers 是否朝预期变化。
   - 素材调整：看 Top 素材占比、IPM、CPI、ROI0 / ROI7。
5. 输出候选效果标签：
   - `scale_effective`：消耗上升且利润 / ROI 不恶化。
   - `control_loss_reduced`：消耗下降且利润改善或亏损收窄。
   - `profit_pressure`：调后利润下降且 ROI 恶化。
   - `volume_lost`：调后 ROI 改善但消耗 / DNU 大幅下降。
   - `needs_more_days`：样本不足、未成熟或窗口太短。
6. 明确 `needs_decision`：是否继续观察、扩大窗口、由 UA owner 判断。

### C. 时间段数据入口

1. 先输出用户所问时间段的 Campaign 主数据：分析平台、消耗、CPI、预估利润、DNU / 注册、ROI 倍率，必要时补素材和国家结构。
2. 查询同一 `active_date_range` 内的 UA 历史；按操作日、操作类型、字段、before / after、来源聚合摘要。
3. 若窗口内有 UA 操作，对每个关键操作计算 `pre_3d` vs `post_3d`，并说明分母、样本量和成熟度。
4. 若窗口内没有 UA 操作，只能说 `ua_operation_history_empty` 或 `operation_log_unavailable`，不能证明无人操作。
5. 输出顺序固定为“时间段整体表现 + 窗口内 UA 操作 + 关键操作前后数据 + 因果边界”。

## 输出字段

建议每次输出一张候选关联表：

| 字段 | 含义 |
|---|---|
| `operation_time` | 操作或备注时间 |
| `operation_type` | budget / status / bid / target_roas / target_cpa / material / remark / unknown |
| `source` | `mi_campaign_history` / `mi_ua_operates` / `mi_ua_remarks` / `google_change_log` |
| `before_after_source` | `structured` / `inferred_text` / `missing` |
| `pre_window` / `post_window` | 前后窗口 |
| `cost_delta` | 调后消耗变化 |
| `分析平台_delta_pp` | 分析平台 百分点变化 |
| `cpi_delta` | CPI 变化 |
| `estimated_profit_delta` | 预估利润变化 |
| `registers_or_dnu_delta` | 注册 / DNU 变化 |
| `candidate_label` | 候选效果标签 |
| `causal_status` | 固定用 `candidate_correlation` / `not_causal_proof` |

## 回答骨架

```text
问题识别：
这是 <数据异动入口 / UA操作复盘入口>，需要双向联动。

口径与参数：
campaign=<...>，bundle_id=<已脱敏>

数据新鲜度与成熟度：
freshness_status=<...>，maturity_status=<...>，sample_status=<...>。

主数据事实：
1. 异动先发生在 <分析平台 / cost / CPI / DNU / 素材 / 国家 / cohort>。
2. 异动幅度：<baseline> -> <anomaly>。

UA 操作联动：
| 操作时间 | 操作类型 | 调前窗口 | 调后窗口 | cost | 分析平台 | CPI | 预估利润 | 候选标签 |
|---|---|---|---|---:|---:|---:|---:|---|

判断：
这些操作和异动在时间窗口上匹配，属于 candidate_correlation，不是因果证明。

风险预警：
<threshold_status / sample_too_small / forecast_partial / operation_log_missing>

needs_decision：
需要 UA owner 判断是否继续观察、回滚、扩大窗口或补平台侧日志。
```

## 禁止输出

- “该操作导致了 ROI 下滑 / DNU 下滑”。
- “操作历史为空，所以没人操作”。
- “备注说明已经执行了预算 / 出价变更”。
- “ROI 上升，所以放量一定有效”。
- “控量后利润改善，所以可以继续停投 / 降预算”。
- 任何最终投放动作指令。
- 操作人邮箱、token、cookie、raw platform JSON。

## 与其他资产的关系

| 资产 | 使用方式 |
|---|---|
| `knowledge/agent_knowledge/policies/Campaign全览分析协议.md` | 分析顺序、页面模块和因果边界 |
| `knowledge/agent_knowledge/policies/第一层分析Agent协议.md` | 第一层分析总流程和 freshness / 输出模板 |
| `task_routes/roi_or_campaign_analysis.yaml` | ROI / campaign 问题默认路由 |
| `task_routes/google_ads_config_change_analysis.yaml` | Google change log 专门路由 |
| `da_assets/analysis_sop/20260706_投放问题线上答题模板.md` | 线上回答合同和因果表达模板 |
| `da_assets/verified_sql/vsql_20260618_google_campaign_dnu_changelog_triage.md` | Google campaign DNU 异动与 change log 联查 |
