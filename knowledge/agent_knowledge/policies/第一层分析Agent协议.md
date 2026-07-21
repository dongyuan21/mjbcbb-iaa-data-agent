# 第一层分析 Agent 固定分析协议

## 目录

- [适用边界](#适用边界)
- [标准流程](#标准流程)
  - [1. 识别任务类型](#1-识别任务类型) — 源选择原则、Google 异动联动、Campaign × UA 双向联动
  - [2. 收集必填参数](#2-收集必填参数)
  - [3. 召回资产](#3-召回资产)
  - [4. 强制 freshness 检查](#4-强制-freshness-检查) — 含能力建设与实时探测前置
  - [5. SQL 生成与执行护栏](#5-sql-生成与执行护栏)
  - [6. 结果校验](#6-结果校验)
  - [7. 输出模板](#7-输出模板)
- [当前已知硬口径](#当前已知硬口径)
- [与下周共建清单的关系](#与下周共建清单的关系)

> 状态：active  
> 创建日期：2026-06-14  
> 目的：把第一层广告投放分析 agent 的工作流固定下来，避免每次问答临场发挥。本文是 agent / DA 执行规程，不是给 UA 填写的问题清单。

## 适用边界

第一层分析 agent 负责：

- 识别问题类型。
- 收集或追问必要参数。
- 召回表卡、语义模型、verified SQL、SOP。
- 检查数据新鲜度和成熟度。
- 生成或复用 SQL。
- 校验查询结果。
- 输出事实、拆解、**风险预警**和待确认项。

第一层分析 agent 不负责：

- 自动放量、停投、降预算（**缺少自动投放是产品定位，不是缺陷**）。
- 代替业务下最终投放动作；只输出预警与 `needs_decision`。
- 拍板 ROI 红线、达标线、风控黄线的最终业务授权（可用 `trial_active` 阈值做预警判断）。
- 把 draft / raw 内容当作已验证事实。
- 在数据未到或未成熟时给强劣化结论。

**投放治理：必须输出预警，禁止输出最终投放动作。**

## 标准流程

### 1. 识别任务类型

先读 `第一层分析Agent问题目录.md`，把用户问题归到一个或多个任务类型：

| 类型 | 例子 | 默认入口 |
|---|---|---|
| ROI / 回收复盘 | ROI7 / ROI30 / SDK vs AF | 日常看数优先 MI ROI360；自动复算 / 对账用 CK `_view`；明细溯源再回 MC |
| DNU / 激活下滑 | DNU 来源贡献、UA / 预装 / organic 拆解、自然量分摊给 UA 渠道；若下钻到 Google Ads campaign / ad_group / ad 下降，下一跳查配置变更 | `da_assets/verified_sql/vsql_20260613_bb_us_ua_media_source_dnu_delta.md`；自然量分摊 SQL 口径见 `投放与ROI预估SQL协议.md`；Google 操作记录用 `da_assets/verified_sql/vsql_20260618_google_ads_config_change_monitoring.md` |
| 素材冷启动与疲劳 | IPM / CPI / CTR / CVR | 当前前端效率优先 MC；MI 素材接口 / 数据源待探索 |
| 首日 ARPU / 广告变现 | 展示次数 vs eCPM | `da_assets/verified_sql/vsql_20260613_day0_arpu_anomaly_attribution.md` |
| 点位 / 事件矩阵 | 渗透率、事件价值、重叠率 | CK 映射表用于 s2s_event ↔ campaign（见 `点位Campaign映射查询规则.md`）；事件用户、渗透、重叠和价值仍需 MC |
| Campaign 观察 | 冷启动、爬坡候选、头部计划；数据异动需补 UA 操作历史，UA 操作需补操作前后数据；Google campaign 异动需补平台 change log | `Campaign全览分析协议.md` + `20260707_Campaign异动与UA操作联动SOP.md`；Google 变更查 `hungry_studio.ods_market_google_ads_config_wide_hi` |
| 数据质量 / 口径 | freshness、join key、分母口径 | `ai_ck/engineering_artifacts/freshness_snapshot.json`、`ai_hive/agent_knowledge/口径决策记录.md` |

如果无法分类，先要求用户补充业务目标，不直接写 SQL。

### 源选择原则

```text
MC / MaxCompute = 事实数仓、明细源、训练与规则源
CK / ClickHouse = 从 MC / 业务链路同步出的 OLAP 查询层
MI = 使用 CK + 后端 join / summary / forecast 逻辑形成的业务看数入口
```

稳定路由：

| 问题 | 默认源 | 说明 |
|---|---|---|
| 日常 ROI360 复盘 | MI | 优化师日常看数入口，含 forecast_version、revenue_source、summary 逻辑。 |
| MI 口径自动复算 / 对账 | CK `_view` | `_view` 对齐 MI 查询路径；目前确认主要规范化 Applovin `ad_name`。 |
| 训练、标签、规则、明细溯源 | MC | CK 不是训练事实源。 |
| 点位事件渗透 / 重叠 / 触发用户价值 | MC + CK 映射表 | CK 映射表只能说明点位配置到哪些 campaign/adset，不包含用户事件触发明细；映射查询规则见 `点位Campaign映射查询规则.md`。 |
| 素材前端效率 | MC | `ads_market_material_metric_di` 支持 CTR/CVR/IPM/CPI；MI 素材接口待探索。 |
| 素材 ROI / LTV / 留存 | 待探索 | 需要探索 MI 素材能力或 MC/CK join 路径。 |
| 预测准确性 / 预测偏差 | MC | `ads_market_roi_pred_accuracy_da` 更适合做真实 vs 预测评估。 |

### Google Ads campaign 异动与操作记录联动

当 DNU、ROI、CPI、消耗或注册下降已经定位到 `googleadwords_int` 的 campaign / ad_group / ad 层时，必须把 Google Ads 操作记录作为归因辅助证据读取，而不是只停在数仓指标拆解。

默认资产：

- 表卡：`ai_hive/agent_knowledge/tables/ods_market_google_ads_config_wide_hi.yaml`
- 数据源：`hungry_studio.ods_market_google_ads_config_wide_hi`
- verified SQL：`da_assets/verified_sql/vsql_20260618_google_ads_config_change_monitoring.md`

关联规则：

- 优先使用 `customer_id + campaign_id` 对齐下降对象；`campaign_name` 只作展示或兜底线索，不作为唯一 join key。
- 若已下钻到 ad_group / ad，继续带 `customer_id + campaign_id + ad_group_id` 或 `customer_id + campaign_id + ad_group_id + ad_id`。
- 查询窗口围绕异常发生前后选择，必须同时过滤 `dt` 和 `hour`；跨天或跨小时先聚合输出。
- 输出只给 `change_event_change_resource_type`、`change_event_resource_change_operation`、`changed_fields` 命中、变更时间范围和 campaign 聚合摘要。
- 禁止输出 `change_event_user_email`、`change_event_old_resource`、`change_event_new_resource`。

解释边界：

- 操作记录能把结论从“该 campaign 下滑”推进到“下滑窗口附近发生过预算 / 状态 / 出价 / 素材 / 定向等变更”。
- 操作记录本身不等于因果证明；最终是否回滚、恢复预算、停投或放量仍输出 `needs_decision`。
- 当前该链路只覆盖 Google Ads；AppLovin / Meta / TikTok / Unity / Moloco 若无同等 change log 表，仍标 `operation_log_missing` 或交给 UA owner 补充。

### Campaign 数据异动与 UA 操作双向联动

当用户问题进入 Campaign 粒度后，必须套用 `da_assets/analysis_sop/20260707_Campaign异动与UA操作联动SOP.md`：

- 数据异动入口：ROI360、DNU、CPI、消耗、预估利润、留存、素材或国家贡献异常时，必须检查同窗口 UA 操作历史；不能只停在指标拆解。
- 操作复盘入口：用户问调价、控量、放量、改预算、改状态、改素材后效果如何时，必须补操作前后数据；不能只复述操作记录。
- 时间段数据入口：用户问某 Campaign 某段时间数据、表现、趋势、日报或阶段复盘时，必须检查该时间窗内 UA 操作；命中操作时必须一起输出操作摘要和操作前后数据。
- 默认窗口是操作日前 3 天 vs 操作日起 3 天；样本不足或低消耗时改用 7 天窗口或标 `sample_too_small`。
- 输出必须包含 `causal_status=candidate_correlation` 或 `not_causal_proof`，不能把同窗口关联写成因果证明。
- 如果用户只要求列操作日志，可以只列日志，但必须标 `pre_post_data_unchecked`，不得推断操作效果；如果用户只要求返回数据明细，可以省略操作展开，但必须标 `ua_operation_linkage_unchecked`。

### 2. 收集必填参数

除非用户问题已经明确，否则必须追问或使用明确默认值。

| 参数 | 默认 / 规则 |
|---|---|
| `bundle_id / app_name` | 必填；不能猜产品。 |
| `country / region` | 用户未给时，说明输出为全量或要求补国家。 |
| `media_source` | 用户未给时，按全渠道输出；涉及 organic 固定 `all` + `paid_only` 两版。 |
| `active_date_range` | ROI / CPI / 留存 / 激活类问题必填。 |
| `compare_window` | 异动归因必须有 baseline 与 anomaly。 |
| `grain` | 默认按问题最小可解释粒度，如 campaign、media_source、material、event。 |
| `revenue_source` | 默认 `sdk`；SDK vs AF 或口径不确定时两版并列。 |
| `cost_metric` | 默认折后消耗 `cost_zhe` / `cost_zhe_usd`。 |
| `exclude_preinstall` | 用户未说明时不擅自排除；但必须提示预装可能影响结论。 |
| `organic_allocation_basis` | 自然量分摊问题默认按 UA `paid_dnu` 占比分摊；按消耗或增量贡献分摊必须由用户明确指定或提供证据。 |
| `ROI_N / LTV_N` | N 是业务展示天数；底层收入窗口取 `date_diff <= N-1`。 |

### 3. 召回资产

资产优先级：

```text
verified_sql
→ knowledge/agent_knowledge/semantic_contract/model.json
→ ai_hive / ai_ck 表卡
→ analysis_sop
→ raw / draft
```

规则：

- 有 verified SQL 时优先复用，不临时重写大 SQL。
- `knowledge/agent_knowledge/semantic_contract/model.json` 覆盖的问题，优先按机器可读模型生成 SQL。
- 只有 draft SOP 时，输出 `draft_sql_needed`，不能伪装成 verified SQL。
- 涉及 DA / UA 待回答内容时，标注 `needs_decision` 待补项，不当事实。DA 已处理结论见 `knowledge/agent_knowledge/policies/DA问题已处理结论_20260628.md`，未解决项见 `TODO/ai_hive待回填/` 或 `TODO/语义层待补清单.md`。

### 4. 强制 freshness 检查

跑 ROI、留存、回收、激活、点位、素材等分析前，必须先检查相关数据源的新鲜度：

#### 4.0 能力建设与实时探测前置

做数据质量、表质量、Data Agent 基座评估、freshness 判断或回归结论前，必须先确认读取能力，而不是直接引用旧快照：

1. **MC / MaxCompute 能力验证**
   - 使用 `maxcompute-dataworks` helper。
   - 先执行 `SELECT 1 AS ok`。
   - 再对目标域至少一张表执行轻量分区 probe，如 `SELECT max(dt) AS latest FROM hungry_studio.<table>`。
2. **CK / ClickHouse 能力验证**
   - 先 source 本机 ClickHouse env。
   - 使用 `~/.clickhouse-shucang/bin/clickhouse_sql.py` 执行 `SELECT 1 AS ok`。
   - 再对目标域至少一张表执行轻量分区 probe，如 `SELECT max(active_date) AS latest FROM shucang_market.<table>`。
3. **快照使用边界**
   - 未完成上述能力验证时，只能把 `freshness_snapshot.json` 作为历史快照，输出 `snapshot_only` / `connectivity_unverified`。
   - 不得把旧快照、旧回归报告或表卡 `last_verified` 当成当前 freshness 事实。
   - 能力验证成功后，必须重跑 `tools/scripts/probe_freshness.py`，再基于新快照判断 freshness。
4. **回归要求**
   - 如果 freshness 会影响 Data Agent 可用性评估，刷新快照后重跑 `python3 eval/agent_regression/run_regression.py`。
   - 最终输出必须说明：本轮是否 live probed、MC/CK 是否 reachable、快照刷新时间、剩余 blocker。

| 数据源 | 检查入口 |
|---|---|
| ClickHouse / MI ROI360 | `ai_ck/engineering_artifacts/freshness_snapshot.json` |
| MaxCompute / Hive | `ai_hive/engineering_artifacts/freshness_snapshot.json` |
| 需要刷新快照 | `tools/runbooks/ClickHouse连通与新鲜度探测.md` / `tools/scripts/probe_freshness.py` |

表级业务 SLA 优先于通用小时延迟阈值，但必须写进知识和表卡后才生效。例如：

- ROI 预测准确性表 `hungry_studio.ads_market_roi_pred_accuracy_da` 允许 T-2 分区，当前规则见 `ROI预测准确性表新鲜度SLA.md`，工程落点为 `ai_hive/agent_knowledge/tables/ads_market_roi_pred_accuracy_da.yaml` 的 `freshness.allowed_partition_lag_days: 2`。
- ROI360 AF 回收表 `shucang_market.tj_ad_revenue_v2` 允许 T-2 分区，当前规则见 `ROI360_AF回收表新鲜度SLA.md`，工程落点为 `ai_ck/agent_knowledge/tables/tj_ad_revenue_v2.yaml` 的 `freshness.allowed_partition_lag_days: 2`。
- 超出表级 SLA、读取能力未验证或请求日期大于 `latest_partition` 时，仍按 freshness blocker / 数据未到处理。

判断规则：

| 状态 | Agent 行为 |
|---|---|
| `fresh` | 可以正常分析，但仍检查 ROI / 留存成熟窗口。 |
| `delayed` | 输出 `data_delay_suspected`，不把最新边缘分区下降直接判为劣化。 |
| `stale` | 优先提示链路异常；除非用户明确要求，否则不做趋势结论。 |
| `unknown` | 说明 freshness 不可用；不能给强结论。 |
| 请求日期 > `latest_partition` | 输出“数据未到，非劣化”；不要把空分区当 0。 |

如果用户要求实时结论，而 freshness 过期或不可达，先说明风险，再决定是否只做历史成熟窗口分析。

### 5. SQL 生成与执行护栏

生成 SQL 时必须遵守：

- 大表必须带分区过滤：`dt`、`active_date`、`hour` 等。
- 按 `install_time` / 激活业务日期看 DNU、activation、install 时，`dt` 不能只扫到业务日当天；必须扫到目标表 `latest_partition` 或至少 T+1，并输出业务日期窗口与 `dt` 扫描窗口。否则标 `partial_partition_scan`，不能给当前窗口强下滑结论。详见 `da_assets/analysis_sop/20260618_DNU安装时间与分区迟到护栏SOP.md`。
- ROI_N / LTV_N：业务展示 `N` 天，底层 `date_diff <= N-1`。
- 留存：必须同时包含 `date_diff=0` 分母和目标 `date_diff=N`。
- organic：默认输出 `all` 和 `paid_only` 两版，除非用户明确只看单版。
- 自然量分摊给 UA 渠道：必须标为经营试算，不是真实归因；默认自然量池 `channel_category='自然'`、UA 池 `channel_category='Media Buy'`、权重为 `paid_dnu`，详见 `投放与ROI预估SQL协议.md`。
- 跨源：CK 与 MaxCompute 不直接 SQL join，应用层对齐或拆成两个查询。
- PII：不输出或落盘用户级 ID、设备 ID、IP、user_agent、token。
- 素材：`ads_market_material_metric_di` 只支持前端效率，不能单表算 ROI。
- 点位：先小窗口验证，再扩大历史窗口。

### 6. 结果校验

SQL 跑通后，先做 sanity check，再写业务解释。

必查项：

- 行数是否为 0；如果为 0，先解释可能是过滤过窄、数据未到、join key 错或口径不匹配。
- 分母是否为 0，如 cost、registers、shows、clicks、cohort users。
- 日期窗口是否成熟，ROI / 留存是否超过可观察窗口。
- SDK 和 AF 差异是否异常大。
- organic / preinstall 是否改变结论。
- `campaign_name` 是否存在前导空格或 id/name 混用。
- 素材字段是否为空或聚合为“其他”。
- 点位事件样本量和渗透率是否足够。

### 7. 输出模板

第一层分析输出固定包含：

```text
问题识别：
口径与参数：
数据新鲜度：
使用资产：
SQL / 查询说明：
主要事实：
拆解解释：
风险与不确定性：
需要 DA / UA / 业务拍板的部分：
下一步：
```

输出边界：

- 可以输出风险候选、观察对象、异常拆解。
- 不输出“必须停投 / 必须放量 / 必须降预算”，除非用户明确授权且阈值已结构化。
- 需要人拍板时标 `needs_decision`。

## 当前已知硬口径

- MI ROI 真实段默认使用折后消耗 `cost_zhe`。
- MI 默认回收源为 `sdk`，`af` 作为对照。
- MI 默认 CPI / LTV 分母为 `total_registers`。
- ROI_N / LTV_N 的 N 是业务展示天数；底层最大 `date_diff=N-1`，如 ROI7 取 `date_diff <= 6`。
- organic 固定输出 `all` 与 `paid_only` 两版。
- ROI360 蓝底是预估值；真实值未返回时可以使用蓝底预估，但必须标注 `roi_source=forecast_blue` 或 `mixed`，不能伪装成真实回收。
- 安装/激活用户数分母禁止用 wide 表；用 AF ODS install 去重。

## 与待确认问题的关系

> 原 `TODO/下周给DA的问题.md` 和 `TODO/下周给UA的问题.md` 已于 2026-07-14 归档清理。

- DA 已处理结论见 `knowledge/agent_knowledge/policies/DA问题已处理结论_20260628.md`。
- UA 待确认的业务判断逻辑、动作边界、点位测试经验等，记录在 `TODO/语义层待补清单.md` 和 `TODO/ai_hive待回填/`。
- 本协议吸收两边答案后升级，成为第一层分析 agent 的执行规程。
