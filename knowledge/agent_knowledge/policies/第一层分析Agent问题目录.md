# 第一层分析 Agent 问题目录

> 状态：active_backlog  
> 创建日期：2026-06-14  
> 目的：沉淀广告投放第一层分析 agent 应能识别和回答的问题类型。本文只收集问题、参数草案、资产入口和护栏，不拍板投放动作、不定义红线阈值。

## 使用边界

第一层分析 agent 负责：

- 识别问题类型。
- 收集分析所需参数。
- 召回表卡、语义模型、verified SQL、SOP。
- 检查数据新鲜度和口径风险。
- 生成或复用 SQL，输出事实、拆解、风险和待确认项。

第一层分析 agent 不负责：

- 自动停投、放量、降预算。
- 拍板 ROI 红线、达标线、风控黄线。
- 将 draft / raw 材料当作已验证事实。
- 把用户级明细写入长期知识库。

## 状态约定

| 状态 | 含义 |
|---|---|
| `seed` | 问题刚沉淀，尚未绑定完整 SQL / SOP。 |
| `verified_asset_available` | 已有可优先引用的 verified SQL 或回归资产。 |
| `partial_verified` | 已能回答一部分指标，仍缺 ROI、长窗口、join 或动作阈值。 |
| `draft_sql_needed` | 有分析方向，但缺可复用 SQL。 |
| `needs_business_params` | 参数、阈值或口径需要业务 / DA 人工校正。 |

## 通用必填参数草案

这些参数不是所有问题都必填，具体以问题类型为准。

| 参数 | 说明 |
|---|---|
| `bundle_id / app_name` | 产品或包体。 |
| `country / region` | 国家、地区或国家组。 |
| `media_source` | 渠道；若涉及 organic，默认输出 `all` 与 `paid_only` 两版。 |
| `active_date_range` | 投放 / 激活 cohort 日期窗口。 |
| `compare_window` | baseline / anomaly 对比窗口。 |
| `grain` | 输出粒度，如 product、country、media、campaign、adset、ad、material、event。 |
| `revenue_source` | 默认 `sdk`，`af` 作对照；差异问题需两版并列。 |
| `cost_metric` | 默认折后消耗 `cost_zhe / cost_zhe_usd`。 |
| `exclude_preinstall` | 是否排除预装媒体。 |
| `maturity_window` | ROI / LTV / 留存需要的数据成熟窗口。 |

## 任务类型

### Q1 ROI / 回收复盘

| 项 | 内容 |
|---|---|
| 状态 | `partial_verified` |
| 典型资产 | `knowledge/agent_knowledge/semantic_contract/model.json`、`ai_ck/agent_knowledge/metrics/ROI360指标语义.md`、`da_assets/verified_sql/sdk_vs_af_revenue_by_cohort.md`、`da_assets/verified_sql/roi_prediction_accuracy_snapshot.md` |
| 必填参数草案 | `bundle_id`、`country`、`media_source`、`active_date_range`、`grain`、`revenue_source`、`ROI_N` |
| 护栏 | ROI_N 业务天数应映射到 `date_diff <= N-1`；跑数前查 freshness；蓝底预测值不得当真实回收。 |

问题池：

- 某产品在某国家最近 7 / 14 / 30 天 ROI 是上升还是下降？
- SDK 回收和 AF 回收差异主要来自哪些 campaign / media_source？
- ROI7 好但 ROI30 差的 campaign 有哪些？
- ROI1 很差但 ROI7 / ROI30 修复明显的对象有哪些？
- 哪些 campaign 的 ROI 预测持续下修？
- 哪些包体 / 渠道存在真实 ROI 低于预测 ROI 的系统性偏差？
- organic 是否影响当前 ROI 判断？`all` 和 `paid_only` 差多少？

### Q2 DNU / 激活下滑归因

| 项 | 内容 |
|---|---|
| 状态 | `verified_asset_available` |
| 典型资产 | `da_assets/verified_sql/vsql_20260613_bb_us_ua_media_source_dnu_delta.md`、`ai_hive/agent_knowledge/tables/dwd_market_appsflyer_activation_push_data_di.yaml` |
| 必填参数草案 | `bundle_id`、`country`、`baseline_window`、`anomaly_window`、`source_scope`、`exclude_preinstall` |
| 护栏 | baseline / anomaly 必须同口径；请求日期超过最新分区时只输出“数据未到”。 |
| 工具路由 | 若缺口集中在 Google / Meta 等媒体，且问题涉及“主动管控 / 预算 / 状态 / 出价变化”，agent 应自主查广告平台操作记录；只在缺 `customer_id` / `campaign_id` / account 映射或权限时追问。 |

问题池：

- 某产品某国家 DNU 下滑主要来自哪些 media_source？
- DNU 下滑是整体渠道都降，还是头部渠道压量？
- DNU 下滑是否来自 organic / preinstall 变化？
- 如何将自然量分摊给 UA 渠道？默认按 UA `paid_dnu` 占比分摊，输出 `allocated_organic_dnu` 与 `adjusted_dnu`，并标明这是经营试算而非真实归因。
- 某 campaign 消耗没降但注册下降，是 IPM 下降还是 CPI 上升？
- 某媒体注册下降是曝光减少、点击率下降，还是 CVR 下降？

### Q3 素材冷启动与疲劳

| 项 | 内容 |
|---|---|
| 状态 | `partial_verified` |
| 典型资产 | `ai_hive/agent_knowledge/tables/ads_market_material_metric_di.yaml`、`ai_hive/agent_knowledge/tables/dim_market_material_unique_info_da.yaml`、`da_assets/verified_sql/vsql_20260613_material_ipm_cpi_snapshot.md` |
| 可支持范围 | MC 已支持素材前端效率：`shows`、`clicks`、`registers`、`cost_zhe_usd`、CTR、CVR、IPM、CPI、素材类型、尺寸、设计师。 |
| 当前缺口 | 单表无收入字段；素材 ROI / ROAS 需 join 回收或归因链路，尚未形成 verified SQL。 |
| 必填参数草案 | `bundle_id`、`media_source`、`active_date_range`、`material / material_type`、`min_shows / min_cost`、`grain` |
| 护栏 | Google / Aura 等部分媒体可能 `material` 为空或聚合为“其他”；素材 ROI 不可从前端表直接计算。 |

问题池：

- 最近新素材里哪些 IPM 高、CPI 低，值得继续观察？
- 高消耗素材里哪些 CTR / CVR / IPM 明显劣化？
- 素材冷启动失败主要是 CTR 低、CVR 低，还是 CPI 高？
- 同一素材在不同国家 / 渠道表现是否稳定？
- 同一素材类型，比如 playable / video / image，哪个更适合当前产品？
- 设计师 / 素材类型 / 尺寸是否和 IPM、CPI 有明显关系？
- 素材前端好但 ROI 差，是不是吸来低价值用户？
- 素材是否出现疲劳：曝光继续涨，但 CTR / IPM 连续下降？

### Q4 首日 ARPU / 广告变现拆解

| 项 | 内容 |
|---|---|
| 状态 | `partial_verified` |
| 典型资产 | `da_assets/verified_sql/vsql_20260613_day0_arpu_anomaly_attribution.md`、`da_assets/analysis_sop/20260611_首日ARPU异动归因SOP.md`、`da_assets/verified_sql/vsql_20260613_ad_impression_metrics.md` |
| 必填参数草案 | `bundle_id / app_name`、`cohort_window`、`behavior_window`、`media_source`、`ad_format / ad_source`、`exclude_preinstall` |
| 护栏 | `ARPU = 人均展示次数 × eCPM / 1000`；广告明细含用户级 ID 时不得落盘。 |

问题池：

- 首日 ARPU 下滑是广告展示次数下降还是 eCPM 下降？
- 插屏和激励广告分别贡献了多少 ARPU 变化？
- eCPM 下降是否集中在某 ad_source / ad_format？
- 新增用户广告展示率是否下降？
- 某媒体用户 ARPU 下降，是用户质量下降还是广告填充 / eCPM 变化？
- 设备机型、RAM、国家是否解释了 ADX eCPM 低的问题？

### Q5 点位 / 事件矩阵

| 项 | 内容 |
|---|---|
| 状态 | `draft_sql_needed` |
| 典型资产 | `da_assets/analysis_sop/202604_IAA事件点位测试分层评估SOP.md`、`da_assets/analysis_sop/用户价值点位事件矩阵分析SOP.md`、`da_assets/analysis_sop/MJ_DT历史点位复盘SOP.md`、`da_assets/verified_sql/vsql_20260613_mj_dt_historical_point_review_small_window.md` |
| 必填参数草案 | `bundle_id / app_name`、`event_pool`、`cohort_window`、`event_observation_window`、`revenue_maturity_window`、`country`、`media_source` |
| 护栏 | 小窗口验证后再扩大历史窗口；事件重叠、低渗透、高 CPI 都可能让模型学不动。 |

问题池：

- 哪些事件渗透率高，能支撑模型学习？
- 哪些事件触发用户 D7 / D14 / D30 ARPU 明显高于大盘？
- 高价值事件是否样本太少，导致难放量？
- 哪些浅层事件虽然 ARPU 不高，但留存好、长线倍率好？
- 事件之间重叠率是否过高，导致新增信息量有限？
- 某点位首日 ROI 低但长线倍率好，是否值得延长观察？
- 不同国家 / 渠道下，同一个事件点位是否稳定？
- 哪些事件适合 UAC2.5，哪些适合 UAC3.0？
- MJ / DT 历史点位中哪些事件可优先复用？

### Q6 Campaign 观察与候选分层

| 项 | 内容 |
|---|---|
| 状态 | `partial_verified` |
| 典型资产 | `da_assets/verified_sql/mi_spend_activation_by_campaign.md`、`knowledge/agent_knowledge/policies/投放ROI治理政策.md`、`knowledge/agent_knowledge/semantic_contract/model.json` |
| 必填参数草案 | `bundle_id`、`country`、`media_source`、`campaign_scope`、`active_date_range`、`ROI_N`、`daily_spend_threshold` |
| 护栏 | 第一层只给事实与候选标签；放量、停投、预算动作必须进入 `needs_decision`。 |

问题池：

- 哪些 campaign 满足冷启动观察条件？
- 哪些 campaign 已过冷启动，但 ROI、CPI、留存仍不足？
- 哪些 campaign 消耗增长后 ROI 明显变差？
- 哪些头部 campaign 有击穿红线风险？
- 哪些 campaign 数据量太小，只能观察不能下结论？
- 哪些 campaign 指标好但数据未成熟，不能过早放量？

### Q7 数据质量 / 口径校验

| 项 | 内容 |
|---|---|
| 状态 | `seed` |
| 典型资产 | `ai_ck/engineering_artifacts/freshness_snapshot.json`、`ai_hive/engineering_artifacts/freshness_snapshot.json`、`ai_hive/agent_knowledge/口径决策记录.md`、`tools/runbooks/语义模型回归校验.md` |
| 必填参数草案 | `datasource`、`table`、`date_range`、`metric`、`expected_grain` |
| 护栏 | 数据状态为 `unknown` 或 `delayed` 时，不输出强劣化结论。 |

问题池：

- 当前请求日期的数据是否已经到齐？
- CK 和 MaxCompute 同一指标是否一致？
- MI 页面 ROI 和底层 SQL 结果是否对齐？
- `campaign_name` 前导空格是否影响 join？
- `campaign_id` 和 `campaign_name` 在当前问题里应该用哪个？
- ROI7 是否正确使用 `date_diff <= 6`？
- 留存是否同时包含 `date_diff=0` 分母？
- wide 表是否被误用作 安装/激活用户数分母？

## 后续推进方式

1. 从每类问题选 1-2 个高频问题，补齐必填参数和默认值。
2. 优先为 `partial_verified` 和 `draft_sql_needed` 问题补 verified SQL。
3. 将通过验证的问题升级进 `Agent最小回归问题集.md`。
4. 有人类动作和后验的问题，另行进入 `da_assets/decision_cases/`，不在本文拍板。
