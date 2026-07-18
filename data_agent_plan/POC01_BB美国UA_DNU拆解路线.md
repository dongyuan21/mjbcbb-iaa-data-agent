# POC-01：BB 美国 UA DNU 下滑 media_source 贡献拆解路线

> 状态：route_poc
> 更新时间：2026-06-18
> POC 类型：只读 DataAgent 路线打穿
> live_sql_executed：true（历史验证窗口复跑）
> 事实边界：本文件验证自然语言问题如何路由、召回、过门禁和输出；历史窗口复跑结果不等于当前实时结论。

## 1. 输入问题

```text
BB 美国 UA DNU 下滑主要来自哪些 media_source？
```

## 2. POC 目标

验证未来 DataAgent 能否从一个自然语言问题走完以下路线：

```text
自然语言问题
  -> 任务识别
  -> 参数抽取
  -> 检索路由
  -> 语义定锚
  -> verified SQL 命中
  -> freshness gate
  -> 只读查询 / 或 snapshot 阻断
  -> 结构化回答
  -> 资产回写判断
```

本 POC 不验证自动投放动作，不判断是否应该放量、停投、降预算。

## 3. 任务识别

| 项 | 结论 |
|---|---|
| task_type | `roi_or_campaign_analysis` / `dnu_drop_attribution` |
| 分析目标 | DNU 下滑来源贡献拆解 |
| 是否需要 SQL | 是 |
| 是否优先 verified SQL | 是 |
| 是否需要 freshness | 是 |
| 是否需要 owner 决策 | 否；本题只做来源贡献拆解 |
| 是否可能触发后续 owner 问题 | 是；若追问“是否人为控量”，Google Ads 可查 `ods_market_google_ads_config_wide_hi` 辅助判断，最终仍需 UA 判断 |

依据：

- `knowledge/agent_knowledge/policies/第一层分析Agent协议.md`
- `AGENT_RETRIEVAL_MAP.yaml`

## 4. 参数抽取

从输入问题抽取：

```yaml
product: kcolb tsalb
country: US
segment: UA
metric: DNU
grain: media_source
analysis_intent: drop_attribution
freshness_required: true
```

需要默认或确认的参数：

| 参数 | POC 默认 | 说明 |
|---|---|---|
| 包体 | `com.kcolb.juggle` | 来自已验证 SQL 的 BB GP 口径 |
| baseline_window | `2026-05-17 ~ 2026-05-23` | 来自历史 verified SQL |
| anomaly_window | `2026-05-24 ~ 2026-05-30` | 来自历史 verified SQL |
| organic | 排除 | 该 SQL 只看 UA media_source |
| preinstall | 排除 | 该 SQL 排除预装媒体名单 |
| 数据源 | MaxCompute | `hungry_studio.dwd_market_appsflyer_activation_push_data_di` |

如果用户问“当前最新窗口”，必须补 `active_date_range` / `compare_window`，并重跑 freshness。

## 5. 检索路线

DataAgent 应按顺序读取：

```text
AGENT_RETRIEVAL_MAP.yaml
knowledge/agent_knowledge/policies/第一层分析Agent协议.md
knowledge/agent_knowledge/semantic_contract/model.json
da_assets/index.yaml
da_assets/verified_sql/vsql_20260613_bb_us_ua_media_source_dnu_delta.md
ai_hive/agent_knowledge/tables/dwd_market_appsflyer_activation_push_data_di.yaml
ai_hive/engineering_artifacts/freshness_snapshot.json
```

当 media_source / campaign 下钻结果定位到 `googleadwords_int` 的 campaign、ad_group 或 ad 下降时，追加读取：

```text
da_assets/verified_sql/vsql_20260618_google_ads_config_change_monitoring.md
ai_hive/agent_knowledge/tables/ods_market_google_ads_config_wide_hi.yaml
```

可选读取：

```text
TODO/工具建设待办.md
TODO/语义层待补清单.md（原 TODO/下周给UA的问题.md 已于 2026-07-14 归档）
```

可选读取只用于判断后续是否需要广告平台操作日志或 UA 解释，不参与本题的默认事实结论。

## 6. 语义定锚

本题必须固定以下口径：

| 概念 | 口径 |
|---|---|
| DNU | AF activation / install 口径，按 `distinct_id` 去重 |
| UA | 排除 organic 与预装媒体名单 |
| 粒度 | `media_source` |
| 对比方式 | baseline vs anomaly |
| 贡献 | 每个 media_source 的 DNU delta 占总 delta 比例 |
| 明细保护 | 不输出 `distinct_id` |

禁止误用：

- 不把该 SQL 当作媒体后台 install。
- 不把该 SQL 输出解释为“UA 一定主动控量”。
- 不把历史验证窗口解释为当前实时窗口。

## 7. verified SQL 命中

命中资产：

```text
da_assets/verified_sql/vsql_20260613_bb_us_ua_media_source_dnu_delta.md
```

命中原因：

- 标题和问题均为 BB 美国 UA DNU 下滑 media_source 贡献拆解。
- 状态为 `verified`。
- 已包含 bundle、国家、baseline / anomaly window、预装和 organic 排除规则。
- 已记录 MaxCompute 小窗口验证结果。

## 8. Freshness Gate

目标表：

```text
hungry_studio.dwd_market_appsflyer_activation_push_data_di
```

正式执行当前窗口前必须做：

```text
1. 使用 maxcompute-dataworks helper 执行 SELECT 1。
2. 对目标表执行轻量 max(dt) probe。
3. 重跑 tools/scripts/probe_freshness.py。
4. 重跑 eval/agent_regression/run_regression.py。
5. 输出 live_probe 与 snapshot 的区别。
```

本 POC 当前状态：

```yaml
freshness_mode: target_table_live_probe
connectivity_verified_this_run: true
target_table_latest_dt: "2026-06-18"
current_window_conclusion_allowed: "true_for_2026-06-17_vs_2026-06-10_to_2026-06-16"
route_validation_allowed: true
```

因此，本文件已经验证历史窗口路线可以落到只读 SQL 执行，并补充了昨日当前窗口版本；其他窗口仍需重新 probe 和替换参数。

## 9. 执行策略

如果用户要求复盘历史验证窗口：

```text
复用 verified SQL，可直接执行。
```

如果用户要求当前窗口：

```text
必须先刷新 freshness，再替换 baseline_window / anomaly_window。
```

如果用户追问“是不是人为控量导致”：

```text
本 SQL 只能证明 media_source 贡献拆解。
若下降定位到 Google Ads campaign/ad_group/ad，可查 hungry_studio.ods_market_google_ads_config_wide_hi 的操作记录辅助判断。
Meta / AppLovin 等其他媒体仍需平台 change log 或 UA owner 补操作记录。
```

## 10. 预期回答模板

```text
问题识别：
这是 DNU 下滑 media_source 贡献拆解问题，默认走 MaxCompute verified SQL。

口径与参数：
产品=BB GP，国家=US，分群=UA，排除 organic 与预装媒体。

数据新鲜度：
本轮未实时 probe，只能引用历史验证或 snapshot；当前窗口结论需刷新 freshness。

使用资产：
da_assets/verified_sql/vsql_20260613_bb_us_ua_media_source_dnu_delta.md

主要事实：
历史验证窗口中，DNU 缺口主要集中在 googleadwords_int、applovin_int 等 media_source。

风险与不确定性：
该结果说明 media_source 缺口贡献，不等于广告平台操作归因。

下一步：
若要判断是否 UA 主动控量，Google Ads 先查 ods_market_google_ads_config_wide_hi；其他媒体需平台 change log 或向 UA owner 补操作记录。
```

## 11. 历史验证样例

以下来自 `vsql_20260613_bb_us_ua_media_source_dnu_delta.md` 的历史验证摘要，只能作为 POC 样例，不代表当前事实：

| media_source | baseline_dnu | anomaly_dnu | delta | contribution |
|---|---:|---:|---:|---:|
| `googleadwords_int` | 144792 | 94719 | -50073 | 约 68.7% |
| `applovin_int` | 45682 | 27266 | -18416 | 约 25.3% |
| `unityads_int` | 7844 | 5722 | -2122 | 约 2.9% |
| `moloco_int` | 14706 | 13331 | -1375 | 约 1.9% |
| `Facebook Ads` | 2693 | 1346 | -1347 | 约 1.8% |

## 12. 成功标准

本 POC 路线视为通过，当且仅当：

- 能正确识别为 DNU 下滑归因问题。
- 能路由到 `第一层分析Agent协议.md` 和 `AGENT_RETRIEVAL_MAP.yaml`。
- 能命中 verified SQL，而不是重新发明 SQL。
- 能识别目标 MaxCompute 表和 freshness 要求。
- 能区分历史验证、snapshot 和 live probe。
- 能输出贡献拆解，但不越权判断“人为控量”或投放动作。
- 能说明后续回写路径。

## 13. 回写路径

| 情况 | 回写 |
|---|---|
| 当前窗口 SQL 执行成功且稳定 | 更新或新增 `da_assets/verified_sql/` |
| 分析流程可复用 | 更新 `da_assets/analysis_sop/` |
| 追问到人为控量并拿到操作日志 | 新增 `da_assets/decision_cases/` |
| 缺广告平台操作日志能力 | 更新 `TODO/工具建设待办.md` |
| 缺 UA 解释 | 更新 `TODO/语义层待补清单.md`（原 `TODO/下周给UA的问题.md` 已归档） |

## 14. 下一步

POC-01 的下一步不是改业务口径，而是做一次 live execution：

```text
1. 用户给定当前 anomaly_window 和 baseline_window。
2. 验证 MC connectivity。
3. 刷新 freshness。
4. 参数化 verified SQL。
5. 执行只读查询。
6. 按模板输出结果。
7. 将执行记录回写到 verified SQL 或 decision case。
```

## 15. 2026-06-18 Live Execution 记录

本次执行范围：

```yaml
execution_date: "2026-06-18"
execution_type: historical_window_rerun
live_connectivity_check: pass
target_table_probe: pass
target_table: hungry_studio.dwd_market_appsflyer_activation_push_data_di
target_table_latest_dt: "2026-06-18"
sql_source: da_assets/verified_sql/vsql_20260613_bb_us_ua_media_source_dnu_delta.md
baseline_window: "2026-05-17 ~ 2026-05-23"
anomaly_window: "2026-05-24 ~ 2026-05-30"
current_window_conclusion: false
```

连通性与目标表探测：

```text
SELECT 1 AS ok -> ok
SELECT max(dt) FROM hungry_studio.dwd_market_appsflyer_activation_push_data_di WHERE dt >= '2026-05-01' -> 2026-06-18
```

复跑结果：

| media_source | baseline_dnu | anomaly_dnu | delta | delta_rate | contribution |
|---|---:|---:|---:|---:|---:|
| `googleadwords_int` | 144792 | 94719 | -50073 | -34.6% | 68.7% |
| `applovin_int` | 45682 | 27266 | -18416 | -40.3% | 25.3% |
| `unityads_int` | 7844 | 5722 | -2122 | -27.1% | 2.9% |
| `moloco_int` | 14706 | 13331 | -1375 | -9.3% | 1.9% |
| `Facebook Ads` | 2693 | 1346 | -1347 | -50.0% | 1.8% |
| `liftoff_int` | 442 | 11 | -431 | -97.5% | 0.6% |
| `simeji_int` | 220 | 159 | -61 | -27.7% | 0.1% |

解释边界：

- 本次证明 POC-01 的路由可以从自然语言问题落到 verified SQL 和只读查询。
- 结果仍是历史窗口复跑，不代表当前最新窗口。
- 本 SQL 只能说明 DNU 缺口按 media_source 的贡献，不证明 Google / Applovin 等媒体是否由 UA 主动控量。
- 若要判断人为控量，Google Ads 可查 `ods_market_google_ads_config_wide_hi` 的 change_event 操作记录；其他媒体仍需平台 change log 或 UA owner 操作记录。

## 16. 2026-06-18 当前窗口执行记录：昨日 vs 前 7 天日均

> 注意：本节是初版当前窗口查询，`dt` 只扫到 `2026-06-17`，低估了 2026-06-17 install cohort 的 T+1 迟到数据。当前窗口结论已被第 19 节修正；本节仅作为 POC 过程教训保留。

本次执行范围：

```yaml
execution_date: "2026-06-18"
execution_type: current_window_yesterday_vs_7d_avg
live_connectivity_check: pass
target_table_probe: pass
target_table: hungry_studio.dwd_market_appsflyer_activation_push_data_di
target_table_latest_dt: "2026-06-18"
anomaly_day: "2026-06-17"
baseline_window: "2026-06-10 ~ 2026-06-16"
baseline_method: previous_7_day_average
current_window_conclusion: true
```

连通性与目标表探测：

```text
SELECT 1 AS ok -> ok
SELECT max(dt) FROM hungry_studio.dwd_market_appsflyer_activation_push_data_di WHERE dt >= '2026-06-01' -> 2026-06-18
```

查询口径：

- 产品：BB GP，`bundle_id = 'com.kcolb.juggle'`
- 国家：US
- 分群：UA，排除 organic 与预装媒体名单
- 指标：AF activation / install 口径 DNU，`COUNT(DISTINCT distinct_id)`
- 对比：2026-06-17 单日 vs 2026-06-10 ~ 2026-06-16 日均

结果：

| media_source | baseline_avg_dnu | yesterday_dnu | dnu_delta | delta_rate | contribution |
|---|---:|---:|---:|---:|---:|
| `googleadwords_int` | 14767.29 | 6673 | -8094.29 | -54.8% | 66.5% |
| `applovin_int` | 4187.86 | 2192 | -1995.86 | -47.7% | 16.4% |
| `moloco_int` | 2304.29 | 1354 | -950.29 | -41.2% | 7.8% |
| `tiktokglobal_int` | 855.43 | 178 | -677.43 | -79.2% | 5.6% |
| `unityads_int` | 456.71 | 159 | -297.71 | -65.2% | 2.5% |
| `Facebook Ads` | 158.86 | 99 | -59.86 | -37.7% | 0.5% |
| `snapchat_int` | 121.14 | 72 | -49.14 | -40.6% | 0.4% |

汇总判断：

- 昨日 UA DNU 约为 `10783`，前 7 天日均约为 `22952.57`，缺口约 `-12169.57`。
- 缺口主要来自 `googleadwords_int`，贡献约 `66.5%`；其次是 `applovin_int`，贡献约 `16.4%`。
- 本结果说明 media_source 层面的 DNU 缺口来源，不证明是否由 UA 主动控量、预算调整或 campaign 状态变更导致。

后续归因：

- 若要判断“人为控量 / 预算变化 / campaign 状态变化”，Google Ads 可查 `ods_market_google_ads_config_wide_hi`；AppLovin / Meta 等媒体仍需平台 change log。
- 若要降低单日波动影响，可以改为昨日 vs 同星期几上周、或最近 3 天 vs 前 7 天日均。

## 17. 2026-06-18 POC-01.1：Google / AppLovin campaign 下钻

> 注意：本节沿用第 16 节初版 `dt` 截止口径，已被第 19 节修正；不再作为当前窗口结论引用。

本次执行范围：

```yaml
execution_date: "2026-06-18"
execution_type: campaign_drilldown_yesterday_vs_7d_avg
live_connectivity_check: pass
target_table_probe: pass
target_table: hungry_studio.dwd_market_appsflyer_activation_push_data_di
target_table_latest_dt: "2026-06-18"
media_sources:
  - googleadwords_int
  - applovin_int
anomaly_day: "2026-06-17"
baseline_window: "2026-06-10 ~ 2026-06-16"
baseline_method: previous_7_day_average
campaign_fields:
  - campaign_id
  - campaign_name
cross_table_join: false
```

字段边界：

- 本次只在 `dwd_market_appsflyer_activation_push_data_di` 单表内按 `campaign_id` / `campaign_name` 聚合。
- 不使用 `campaign_id` 去 join 其他表；表卡中 campaign_id 等价 AF `af_c_id` 仍是待 DA / 数仓确认项。
- `media_delta_contribution` 是 campaign 对本 media_source 缺口的贡献，不是对全渠道缺口的贡献。

### Google campaign 缺口

`googleadwords_int` 昨日缺口约 `-8094.29` DNU。

| rank | campaign_id | campaign_name | baseline_avg_dnu | yesterday_dnu | dnu_delta | delta_rate | media_delta_contribution |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `23665242237` | `US-LH015-3.0--ARO-XH-260319-通用词` | 8181.57 | 3416 | -4765.57 | -58.3% | 58.9% |
| 2 | `23734855655` | `US-008-tachi-XH-260408-素材测试` | 957.71 | 385 | -572.71 | -59.8% | 7.1% |
| 3 | `23790512821` | `US-LH015-3.0-ARO-XH-260423-品类APP` | 634.71 | 136 | -498.71 | -78.6% | 6.2% |
| 4 | `23679559825` | `US-LH015-3.0--ARO-XH-260320-体育专项` | 568.86 | 163 | -405.86 | -71.4% | 5.0% |
| 5 | `23670585536` | `US-LH015-3.0--ARO-XH-260319-游戏大词` | 349.14 | 7 | -342.14 | -98.0% | 4.2% |
| 6 | `23908328308` | `US-035-HK-XH-TachiPer020-横-260602` | 743.71 | 465 | -278.71 | -37.5% | 3.4% |
| 7 | `23670525041` | `US-LH015-3.0--ARO-XH-260319-核心竞品` | 1440.00 | 1217 | -223.00 | -15.5% | 2.8% |

判断：

- Google 缺口高度集中，第一名 campaign 贡献约 `58.9%` 的 Google 缺口。
- `游戏大词`、`PUR-HK`、`DA_s1/s2` 等 campaign 出现接近归零式下降；Google Ads 下一跳应查 `ods_market_google_ads_config_wide_hi`，对齐预算 / 状态 / 出价 / 素材等变更。

### AppLovin campaign 缺口

`applovin_int` 昨日缺口约 `-1995.86` DNU。

| rank | campaign_id | campaign_name | baseline_avg_dnu | yesterday_dnu | dnu_delta | delta_rate | media_delta_contribution |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `c94938e310bdede9d77df0df57d6b364` | `Juggle-WW-ROAS-D28-RC-CPMM` | 3599.86 | 1853 | -1746.86 | -48.5% | 87.5% |
| 2 | `4f12a05e6ca0acc6335369d3cd9b21aa` | `Juggle-WW-ROAS-D28-RC-CPM匀速-土耳其` | 211.57 | 76 | -135.57 | -64.1% | 6.8% |
| 3 | `dd3de3fad223cc641770e2b2e0180de4` | `Juggle-WW-ROAS-D28-RC-CPM匀速-测试自动化-安卓` | 279.43 | 170 | -109.43 | -39.2% | 5.5% |
| 4 | `0b905ffb6ed94f7cbd3dc9d9014c7836` | `Juggle-WW-ROAS-D28-RC-CPM匀速-玩法测-260605` | 30.14 | 4 | -26.14 | -86.7% | 1.3% |
| 5 | `a41d59e29858226fe30c180928287ed7` | `Juggle-WW-ROAS-D28-RC-CPIbiding-260318` | 37.43 | 21 | -16.43 | -43.9% | 0.8% |

判断：

- AppLovin 缺口极度集中，第一名 campaign 贡献约 `87.5%` 的 AppLovin 缺口。
- 这一步只能证明 campaign 层 DNU 下降集中度，不能证明 AppLovin 平台是否发生预算、状态、出价或流量策略变更。

### POC-01.1 结论

- Google：主要看 `US-LH015-3.0--ARO-XH-260319-通用词`，其次看素材测试、品类 APP、体育专项、游戏大词。
- AppLovin：主要看 `Juggle-WW-ROAS-D28-RC-CPMM`。
- 下一跳若要做“原因归因”，Google Ads 已可接 `ods_market_google_ads_config_wide_hi`；AppLovin 等媒体仍需平台 change log。当前只读数仓链路已经到 campaign 层。

## 18. 2026-06-18 POC-01.2：主因 campaign 日趋势与 adset 下钻

> 注意：本节沿用第 16 节初版 `dt` 截止口径，已被第 19 节修正；不再作为当前窗口结论引用。

本次执行范围：

```yaml
execution_date: "2026-06-18"
execution_type: top_campaign_daily_trend_and_adset_drilldown
live_connectivity_check: pass
target_table_probe: pass
target_table: hungry_studio.dwd_market_appsflyer_activation_push_data_di
target_table_latest_dt: "2026-06-18"
date_window: "2026-06-10 ~ 2026-06-17"
top_campaigns:
  googleadwords_int:
    - "23665242237"
    - "23734855655"
    - "23790512821"
    - "23670585536"
  applovin_int:
    - "c94938e310bdede9d77df0df57d6b364"
    - "4f12a05e6ca0acc6335369d3cd9b21aa"
    - "dd3de3fad223cc641770e2b2e0180de4"
cross_table_join: false
```

### 主因 campaign 日趋势

Google 主因 campaign：

| campaign | 06-10 | 06-11 | 06-12 | 06-13 | 06-14 | 06-15 | 06-16 | 06-17 | 观察 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `US-LH015-3.0--ARO-XH-260319-通用词` | 7270 | 7305 | 8032 | 9954 | 9815 | 7618 | 7277 | 3416 | 06-17 单日断崖式下降 |
| `US-008-tachi-XH-260408-素材测试` | 1071 | 912 | 868 | 893 | 1009 | 1066 | 885 | 385 | 06-17 明显下降 |
| `US-LH015-3.0-ARO-XH-260423-品类APP` | 755 | 709 | 655 | 584 | 450 | 734 | 556 | 136 | 06-17 明显下降 |
| `US-LH015-3.0--ARO-XH-260319-游戏大词` | 895 | 789 | 388 | 196 | 95 | 44 | 37 | 7 | 之前已持续下滑，06-17 接近归零 |

AppLovin 主因 campaign：

| campaign | 06-10 | 06-11 | 06-12 | 06-13 | 06-14 | 06-15 | 06-16 | 06-17 | 观察 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `Juggle-WW-ROAS-D28-RC-CPMM` | 3449 | 3902 | 3677 | 3454 | 3664 | 3648 | 3405 | 1853 | 06-17 单日明显下降 |
| `Juggle-WW-ROAS-D28-RC-CPM匀速-土耳其` | 234 | 226 | 184 | 203 | 168 | 215 | 251 | 76 | 06-17 明显下降 |
| `Juggle-WW-ROAS-D28-RC-CPM匀速-测试自动化-安卓` | 182 | 256 | 292 | 331 | 319 | 296 | 280 | 170 | 06-17 下降但相对较缓 |

### Google 主 campaign adset 下钻

`US-LH015-3.0--ARO-XH-260319-通用词` 昨日缺口约 `-4765.57` DNU。

| rank | adset_id | adset_name | baseline_avg_dnu | yesterday_dnu | dnu_delta | delta_rate | campaign_delta_contribution |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `194347599773` | `260319-通用词-创意组21` | 2861.00 | 1070 | -1791.00 | -62.6% | 37.6% |
| 2 | `196072674204` | `260319-通用词-创意组2` | 2835.43 | 1117 | -1718.43 | -60.6% | 36.1% |
| 3 | `196072679964` | `260319-通用词-创意组16` | 583.14 | 20 | -563.14 | -96.6% | 11.8% |
| 4 | `194347764373` | `260319-通用词-创意组18` | 184.29 | 13 | -171.29 | -93.0% | 3.6% |
| 5 | `195203813740` | `260319-通用词-创意组1` | 257.71 | 102 | -155.71 | -60.4% | 3.3% |
| 6 | `198014164441` | `260319-通用词-创意组11` | 165.29 | 33 | -132.29 | -80.0% | 2.8% |

判断：

- Google 主 campaign 不是单个 adset 独占下滑；创意组 21 和创意组 2 合计贡献约 `73.7%`，创意组 16 贡献约 `11.8%`。
- 下滑像是 campaign 内多组同步回落，其中部分组接近归零；Google Ads 应继续查 `ods_market_google_ads_config_wide_hi` 判断同窗口是否发生状态、预算、出价、素材或学习策略相关变更。

### AppLovin 主 campaign adset 下钻

| adset_id | adset_name | baseline_avg_dnu | yesterday_dnu | dnu_delta | campaign_delta_contribution |
|---|---|---:|---:|---:|---:|
| `NaN` | `_DEFAULT` | 3599.86 | 1853 | -1746.86 | 100.0% |

判断：

- AppLovin 在当前激活表里没有可用的 adset 细分解释力，主 campaign 缺口全部落在 `_DEFAULT`。
- 下一步要么查更细的 `ad_id / ad_name`，要么接 AppLovin 平台侧 campaign / creative / bid / budget 变更记录。

### POC-01.2 结论

- 06-17 的 Google 和 AppLovin 主因 campaign 都呈现单日明显下挫，Google `游戏大词` 则更像之前已开始持续衰退。
- Google 主 campaign 的下滑进一步集中在创意组 21、创意组 2、创意组 16。
- AppLovin 在当前表 adset 层不可继续下钻，应改查 ad / creative 或平台 change log。
- 只读数仓链路已经从 media_source 下钻到 campaign 和 adset；Google Ads 可继续接操作记录辅助归因，其他媒体仍需平台 change log 或 owner 记录。

## 19. 2026-06-18 修正版：纳入 T+1 迟到分区后的当前窗口结论

修正原因：

```text
初版当前窗口查询使用 dt BETWEEN '2026-06-10' AND '2026-06-17'。
目标表 latest dt = 2026-06-18，说明 2026-06-17 install cohort 可能有 T+1 迟到数据。
因此修正版保留 install_time 过滤到 2026-06-17，但 dt 扫到 2026-06-18。
```

修正后执行范围：

```yaml
execution_date: "2026-06-18"
execution_type: corrected_current_window_yesterday_vs_7d_avg
target_table: hungry_studio.dwd_market_appsflyer_activation_push_data_di
target_table_latest_dt: "2026-06-18"
spend_check_table: hungry_studio.ads_market_tj_ad_spend_active_v2
spend_check_table_latest_dt: "2026-06-17"
install_time_window: "2026-06-10 ~ 2026-06-17"
dt_scan_window: "2026-06-10 ~ 2026-06-18"
anomaly_day: "2026-06-17"
baseline_window: "2026-06-10 ~ 2026-06-16"
baseline_method: previous_7_day_average
live_validation: pass
current_window_conclusion: true
supersedes:
  - section_16
  - section_17
  - section_18
```

复核记录：

```text
2026-06-18 Codex live validation
- MC SELECT 1: PASS
- activation target latest dt: 2026-06-18
- spend check table latest dt: 2026-06-17
- 修正版 media/campaign/adset/ad 明细已按 dt_scan_window 复跑
- 第 16~18 节保留为错误口径过程记录，不再作为当前窗口结论引用
```

### 修正版 media_source 结果

修正后，昨日 UA DNU 为 `20574`，前 7 天日均约 `22952.57`，缺口约 `-2378.57`。这与初版 `-12169.57` 有明显差异，初版主要是漏扫迟到分区造成的低估。

贡献率口径：media_source 贡献以整体修正后缺口 `-2378.57` 为分母；campaign 贡献以对应 media_source 缺口为分母。低频媒体或 campaign 的缺失日期按 0 处理，避免只对出现日期取均值而高估 baseline。

| media_source | baseline_avg_dnu | yesterday_dnu | dnu_delta | delta_rate | contribution |
|---|---:|---:|---:|---:|---:|
| `googleadwords_int` | 14767.29 | 13307 | -1460.29 | -9.9% | 61.4% |
| `tiktokglobal_int` | 855.43 | 275 | -580.43 | -67.9% | 24.4% |
| `applovin_int` | 4187.86 | 3896 | -291.86 | -7.0% | 12.3% |
| `unityads_int` | 456.71 | 307 | -149.71 | -32.8% | 6.3% |
| `moloco_int` | 2304.29 | 2390 | +85.71 | +3.7% | -3.6% |

修正后判断：

- 昨日确实低于前 7 天日均，但不是断崖式大跌。
- 主要缺口仍来自 `googleadwords_int`，但幅度从初版 `-8094.29` 修正为 `-1460.29`。
- `tiktokglobal_int` 成为第二缺口来源，贡献约 `24.4%`。
- `applovin_int` 缺口较小，修正后不再是主要问题。

### 修正版 Google / AppLovin campaign 结果

| media_source | campaign | baseline_avg_dnu | yesterday_dnu | dnu_delta | delta_rate | media_delta_contribution |
|---|---|---:|---:|---:|---:|---:|
| `googleadwords_int` | `US-LH015-3.0--ARO-XH-260319-通用词` | 8181.57 | 7569 | -612.57 | -7.5% | 41.9% |
| `googleadwords_int` | `US-LH015-3.0-ARO-XH-260423-品类APP` | 634.71 | 216 | -418.71 | -66.0% | 28.7% |
| `googleadwords_int` | `US-LH015-3.0--ARO-XH-260319-游戏大词` | 349.14 | 12 | -337.14 | -96.6% | 23.1% |
| `googleadwords_int` | `US-LH015-3.0--ARO-XH-260320-体育专项` | 568.86 | 343 | -225.86 | -39.7% | 15.5% |
| `applovin_int` | `Juggle-WW-ROAS-D28-RC-CPMM` | 3599.86 | 3264 | -335.86 | -9.3% | 115.1% |
| `applovin_int` | `Juggle-WW-ROAS-D28-RC-CPM匀速-土耳其` | 211.57 | 82 | -129.57 | -61.2% | 44.4% |

修正后判断：

- Google 主 campaign `通用词` 仍是最大单点，但只是轻度低于前 7 天日均，不是断崖。
- Google `品类APP`、`游戏大词`、`体育专项` 更像需要关注的 campaign，其中 `游戏大词` 延续前几天持续衰退。
- AppLovin 主 campaign 修正后接近正常波动区间，`土耳其` campaign 更异常，但绝对量较小。

### 修正版 adset / ad 下钻

Google `通用词` campaign 内部：

| adset_name | baseline_avg_dnu | yesterday_dnu | dnu_delta | delta_rate |
|---|---:|---:|---:|---:|
| `260319-通用词-创意组16` | 583.14 | 30 | -553.14 | -94.9% |
| `260319-通用词-创意组21` | 2861.00 | 2432 | -429.00 | -15.0% |
| `260319-通用词-创意组2` | 2835.43 | 2482 | -353.43 | -12.5% |

AppLovin `Juggle-WW-ROAS-D28-RC-CPMM` 内部 top ad：

| ad_id | ad_name | baseline_avg_dnu | yesterday_dnu | dnu_delta |
|---|---|---:|---:|---:|
| `163078657` | `C4F42996...&PA_337` | 330.86 | 237 | -93.86 |
| `163078651` | `C4F42970...&PA_337` | 144.00 | 66 | -78.00 |
| `152515033` | `CAK704_zjl_US_50s&PA_369_1 (Cloned)` | 351.14 | 285 | -66.14 |

### spend / activation reconciliation

我进一步用 `ads_market_tj_ad_spend_active_v2` 做了 spend / shows / clicks / registers 对照。这个步骤的作用不是替代 activation 表，而是判断“投放量是否同步下降”。

关键发现：

- Google `通用词`：spend 表 registers 从前 7 天日均 `8095.14` 到昨日 `7231`，约 `-10.7%`；activation DNU 从 `8181.57` 到 `7569`，约 `-7.5%`。两边方向基本一致，属于轻度回落。
- Google `游戏大词`：spend / shows / clicks / registers 均接近归零，activation 也接近归零。这是更像真实投放量收缩的点。
- AppLovin `CPMM`：spend 表 registers 约 `-8.3%`，activation DNU 约 `-9.3%`，方向一致，非断崖。

### 修正版结论

- 初版“大幅断崖”结论作废；原因是未纳入 T+1 迟到分区。
- 修正后，6/17 BB US UA DNU 是轻度低于前 7 天日均，主要缺口来自 Google，其次 TikTok，AppLovin 只是小幅回落。
- 在 Google 内部，真正需要重点关注的是 `游戏大词` 的持续衰退、`品类APP` 的明显下滑，以及 `通用词` 内 `创意组16` 的异常低量。
- 下一步不应急着上升到“人为控量”判断；更合理的是把当前窗口 SQL 改成正式 SOP：`install_time` 用业务窗口，`dt` 扫到 latest partition 或至少 T+1。
