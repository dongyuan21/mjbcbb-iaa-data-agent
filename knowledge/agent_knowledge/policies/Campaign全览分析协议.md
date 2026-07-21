# Campaign 全览分析协议

> 状态：active
> 创建日期：2026-07-07
> 来源：钉钉文档《Campaign 全览计划详情页宣讲》、PGP `pgp/campaign-overview` 代码、`20260705_投放看板模块知识蒸馏SOP.md`、`20260706_投放看板live验证记录.md`
> 目的：固定 Campaign 全览的分析顺序，特别是 UA 操作历史如何和 ROI / 消耗 / CPI / 素材 / 国家 / cohort 异动做关联。

执行层 SOP：`da_assets/analysis_sop/20260707_Campaign异动与UA操作联动SOP.md`。该 SOP 固定三个入口：用户问数据异动时必须补 UA 操作历史；用户问 UA 操作效果时必须补操作前后数据；用户问某段时间的 Campaign 数据、表现或趋势时，若窗口内有 UA 操作，也必须补操作摘要和操作前后数据。

## 定位

Campaign 全览是优化师的单 Campaign 诊断工作台，不是 MI ROI360 的复制页。它把 Campaign 的状态判断、ROI360、消耗、CPI、预估利润、ROI 倍率、素材、国家、cohort、健康度和 UA 历史放到同一个分析路径里，用来回答：

- 这条 Campaign 当前是达标、观察还是需要优先复核。
- ROI 或利润变差时，问题更像来自消耗规模、买量成本、回收节奏、素材集中、国家结构还是 cohort 异常。
- UA 近期调价、控量、放量、备注是否发生在异动窗口附近，以及调后窗口的指标是否改善。

边界：

- 只输出风险预警、候选原因和 `needs_decision`，不替 UA / 业务 owner 下最终停投、放量、降预算动作。
- UA 操作历史只能把异动推进到“同窗口发生过某类操作，调后指标如何变化”，不能单独证明因果。
- 预估利润是投放判断口径，不是财务利润。
- 低消耗、新 Campaign、未成熟 cohort 的红黄灯优先解释为观察信号，不能直接写成明确劣化。

## 标准分析顺序

### 1. 先看当前状态与基线差距

先比较当前 Campaign 近 7 日、上一周期和同包同渠道基线，确认偏离发生在哪个指标：

| 观察项 | 分析目的 |
|---|---|
| 近 7 日均值 | 判断当前 Campaign 最近表现 |
| 上一周期均值 | 判断最近是否改善或变差 |
| 同包同渠道基线 | 避免只看单 Campaign，忽略大盘变化 |

输出时优先用表格差距解释，雷达图只适合快速看形状，不适合承载精确结论。

### 2. 再看健康度时序与成熟度

健康度时序是优先级判断入口：

- 成熟期：已有较完整 ROI360，适合判断真实回收稳定性。
- 未成熟期：用同龄 ROI、ROI360 预测和红黄灯做早期预警。
- 灯色连续性比单日灯色更重要；单日红灯可能是波动，连续红灯且消耗不低才进入高优先复核。
- 日消耗小或冷启动阶段的红灯，只能标观察或样本不足。

回答必须同时给出：

```text
threshold_status / lamp_status
maturity_status
cost_scale
needs_decision
```

### 3. 用 ROI360 与消耗确认“回收和规模是否同向变化”

ROI360 不能脱离消耗柱单独解读：

- ROI 下滑但消耗很小：优先标低优先级观察或样本波动。
- ROI 下滑且消耗持续放大：进入高优先复核。
- ROI 回升但消耗明显收缩：不能直接说变好，要看利润和规模是否保住。
- ROI 掉线、零值或空值时，先检查 forecast / 成熟度 / CK 落表时序，不把空值当真实 0。

PGP 页面实现中，`CampaignDataOverview.vue` 的 `ROI360 与消耗` 图会把 UA 操作 / 备注打到同一时间轴上；点击曲线点、柱子或操作标记会定位右侧 UA 历史。

### 4. 用 CPI 与预估利润区分成本问题和回收压力

CPI 回答“买量成本是否变贵”，预估利润回答“扣除回收达标线后是否还有投放判断空间”。

预估利润公式：

```text
折后消耗 * (ROI360 / 100 - 回收达标线)
```

其中回收达标线优先使用页面 / 治理配置给出的 `recycle_target_line`；无值时不能擅自补长期正式线。历史版本里曾有 `0.9` 或页面 fallback，但输出必须说明来源。

常见解释：

- CPI 上升、ROI 下滑：先怀疑买量成本和流量质量，再拆国家、素材。
- CPI 稳定、ROI 下滑：继续看 ROI 倍率、留存、素材质量和国家结构。
- 预估利润为负且消耗放大：高优先风险预警。
- 预估利润改善但消耗大幅下降：可能是控量止损，不等于规模健康。

### 5. 用 ROI 倍率判断早期回收节奏

ROI 倍率用于判断早期质量和成熟节奏：

| 倍率 | 解释 |
|---|---|
| ROI3 / ROI1 | D0 后短期回收是否接得上 |
| ROI7 / ROI1 | 一周内留存和变现是否继续成长 |
| ROI360 / ROI1 | 早期回收与长期预测的相对关系 |

如果 ROI1 不差但 ROI7 / ROI3 接不上，优先怀疑后续留存或变现走弱。如果早期倍率稳定，而健康度短期变黄，可能是样本或预测时序问题。

倍率不能单独解释长期变差；需要和 ROI360、留存、素材、国家结构一起判断。

### 6. 用 Top 素材判断是否是素材拉低质量

素材模块优先看：

- 首位素材、前三素材消耗占比：判断是否过度集中。
- 安装、CPI、IPM：判断拉量能力和买量成本。
- ROI0 / ROI7 / 留存：判断素材带来的用户质量。
- 素材预览：辅助判断创意内容是否疲劳或与目标人群错配。

解释规则：

- 健康度变差且素材消耗高度集中：优先怀疑头部素材疲劳或流量质量变化。
- 素材 CPI / IPM 正常但 ROI / 留存弱：继续查用户质量、国家和 cohort。
- 素材模块来自 Campaign 消耗视角；素材效能看板来自生产 cohort，二者不能混为同一口径。

### 7. 用 Top15 国家贡献判断风险集中市场

国家模块用于判断整体回收是否被某些国家拖累：

- 高消耗国家 ROI 低，会显著拖累整体。
- 利润贡献为负的国家应优先进入复核。
- 如果只有一个国家贡献很大，优化动作更需要人工拍板，避免误伤主力市场。

国家派生收入、利润和 ROI 拉动只在预测完整可展示时输出；若 `forecast_partial_failed` 或国家 forecast 不完整，不得用半截预测给强结论。

### 8. 最后用 cohort 表定位具体日期

当趋势图发现异常后，用 ROI & LTV cohort 表定位是哪几天的 cohort 出问题：

- 每日 / 每周的折后消耗、注册、CPI、ARPU。
- ROI1、ROI7、ROI30、ROI60、ROI360 是否逐步长起来。
- LTV30、LTV360 是否和 ROI 变化方向一致。

cohort 表适合验数和追日期，不适合绕过成熟度直接判最新 cohort 长期失败。

## UA 操作历史与异动关联

### 数据来源与页面实现

PGP `campaign-overview` 当前链路：

| 层 | 入口 | 作用 |
|---|---|---|
| 前端 API | `queryCampaignHistory()` | 调 `POST /v1/campaign-overview/history` |
| 后端 handler | `Controller.History` | 解析 Campaign scope，读取 MI campaign history |
| MI 历史来源 | `QueryCampaignUARemarks` / `QueryCampaignOperates` | 返回 UA 备注和操作 |
| 前端展示 | `index.vue` | 右侧 `UA 历史` 列表，按全部 / 操作 / 备注筛选 |
| 图表关联 | `CampaignDataOverview.vue` | 把同日操作 / 备注打到 ROI、消耗、CPI、利润、倍率图上 |

后端事件字段统一为：

```text
date / changed_at / type / title / body / field / before / after / source / status
```

后端会尝试把 `target_roas`、`target_cpa`、`bid_strategy`、`conversion_action`、`budget`、`status`、`material` 等字段归一，并从文本中推断 `before -> after`。这些推断应视为辅助展示，不等于平台原始结构化变更。

### 关联方法

关联 UA 操作历史时按以下步骤：

1. 先定位指标异动窗口：ROI360、消耗、CPI、预估利润、倍率或 cohort 里哪一天开始明显偏离。
2. 把 UA 历史按 `changed_at` / `date` 归一到 `active_date`。
3. 只把同日或邻近窗口的操作作为候选解释，备注只作为上下文，不当作执行动作。
4. 对操作类事件，比较“操作日前 3 天”与“操作日起 3 天”：
   - 消耗：两窗口求和。
   - ROI360：按 cost 加权均值。
   - 预估利润：按日预估利润求和。
   - 倍率：窗口内 `ROI360 / ROI1` 均值。
5. 根据调后窗口变化输出候选判断，例如改善、恶化、放量有效、控量止损、利润承压或观察。

PGP 当前前端的 `buildOperationImpact()` 就是这个逻辑：先找操作日对应的 cohort 行，再用前 3 天和操作日起 3 天计算 `cost_delta`、`roi_delta`、`profit_delta`、`multiplier_delta`。这些标签是复盘启发，不是因果证明。

强制联动规则：

- 数据异动入口：ROI / DNU / CPI / 消耗 / 利润 / 留存发生异动时，必须检查同窗口 UA 操作历史。
- 操作复盘入口：UA 调价 / 控量 / 放量 / 改预算 / 改状态 / 改素材后效果如何，必须计算操作前后窗口数据。
- 时间段数据入口：用户问某 Campaign 某段时间数据、表现、趋势、日报或阶段复盘时，必须检查该时间窗内 UA 操作；命中操作时必须补操作前后窗口数据。
- 如果用户只要求“列操作日志”，可以只列日志，但必须标注 `pre_post_data_unchecked`，不能推断效果；如果用户只要求“返回数据明细”，可以省略操作展开，但必须标注 `ua_operation_linkage_unchecked`。

### 判断边界

可以说：

- “异动窗口附近有一次预算 / 出价 / 状态 / 素材相关操作，调后 3 天 ROI360 / 利润 / 消耗变化如下。”
- “这更像一次需要 UA 复核的候选关联，建议 owner 判断是否继续观察、回滚或调整。”
- “操作后利润改善但消耗下降，可能是控量止损；不能直接说 Campaign 恢复健康。”

不要说：

- “这次 UA 操作导致了 ROI 下滑。”
- “红灯说明必须停投 / 放量 / 降预算。”
- “操作历史为空，所以一定没有人动过配置。”
- “备注内容等同平台操作记录。”

### 和 Google Ads change log 的关系

Campaign 全览的 UA 历史来自 MI campaign history，适合做页面级复盘和同窗口关联。

当问题已经定位到 Google Ads 的 campaign / ad_group / ad 层，并需要验证平台配置变更时，必须继续走 `google_ads_config_change_analysis` 下一跳，读取：

```text
hungry_studio.ods_market_google_ads_config_wide_hi
da_assets/verified_sql/vsql_20260618_google_ads_config_change_monitoring.md
da_assets/verified_sql/vsql_20260618_google_campaign_dnu_changelog_triage.md
```

Google change log 优先用 `customer_id + campaign_id` 对齐；`campaign_name` 只作展示或兜底线索。输出仍只给聚合摘要和变更类型，不输出操作人邮箱、raw resource JSON、token 或 cookie。

非 Google 媒体若没有同等平台 change log，输出 `operation_log_missing`，不要用空历史替代事实。

## 回答模板

当用户问某个 Campaign 为什么异动，输出结构建议为：

```text
问题识别：
证据状态：
Campaign scope：
状态与基线：
健康度与成熟度：
ROI360 / 消耗：
CPI / 预估利润：
ROI 倍率：
素材与国家：
cohort 日期定位：
UA 操作历史关联：
风险预警：
needs_decision：
下一步验证：
```

其中“UA 操作历史关联”必须写清：

- 操作 / 备注时间。
- 操作类型或字段。
- before / after 是否为结构化字段还是文本推断。
- 调前 3 天与调后 3 天的指标变化。
- 结论是候选关联还是已验证因果。

## 常见误判

| 误判 | 正确处理 |
|---|---|
| 只看 ROI360，不看消耗 | 同时看 cost scale 和利润影响 |
| 单日红灯直接判坏 | 先看成熟度、连续性和日耗阈值 |
| ROI 上升就说操作有效 | 还要看消耗是否缩小、利润是否改善 |
| 操作历史为空就说没有操作 | 只能说 `mi_campaign_history_empty` 或历史不可用 |
| 备注等同投放平台配置变更 | 备注只是上下文；Google 配置要查 change log 表 |
| 预估利润当财务利润 | 只作为投放判断试算 |
| 最新 cohort ROI360 为 0 就说回收为 0 | 先查 forecast 和 CK 落表时序 |
