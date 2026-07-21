# BB 商业化埋点查询规则

> 状态：active  
> 创建日期：2026-06-19  
> 适用范围：Block Blast GP / iOS 白名单事件表中的商业化埋点查询，包括广告初始化、load、ready、show、click、show end、ADX / MAX 收入和 banner session。

## 使用边界

本文用于生成或审查 BB 商业化链路 SQL，不直接提供 verified SQL。

可以作为当前默认规则使用：

- 判断 BB GP / iOS 商业化链路应使用哪些事件族。
- 区分旧 `s_*` 埋点、新 `ad_*` 三聚合 / 自建聚合埋点和收入回调事件。
- 约束广告格式、广告单元、network、load 状态、ready 状态、收入和 eCPM 字段的混用风险。

不能直接作为 verified 事实使用：

- 未经表卡确认的列级字段是否已展开。
- 未经过 `properties` JSON 小窗口验证的参数路径。
- 大埋点字典中的每个参数枚举值；枚举只作为候选，进入 SQL 前要验证。

## 数据入口

优先使用已进入 `ai_hive/` 的 BB 白名单事件表卡：

| 端 | 表卡入口 |
|---|---|
| GP | `ai_hive/agent_knowledge/tables/dwd_block_blast_gp_white_event_unique_data_hi.yaml` |
| GP | `ai_hive/agent_knowledge/tables/dwd_block_blast_gp_white_event_offline_di.yaml` |
| GP | `ai_hive/agent_knowledge/tables/dwd_block_blast_gp_white_event_offline_history_di.yaml` |
| iOS | `ai_hive/agent_knowledge/tables/dwd_block_blast_ios_white_event_unique_data_hi.yaml` |
| iOS | `ai_hive/agent_knowledge/tables/dwd_block_blast_ios_white_event_offline_di.yaml` |
| iOS | `ai_hive/agent_knowledge/tables/dwd_block_blast_ios_white_event_offline_history_di.yaml` |

执行前必须继续读取表卡，确认：

- 当前任务应走实时、离线还是历史表。
- 目标字段是表列，还是需要从 `properties` JSON 提取。
- 是否存在端差异。iOS 表卡已记录部分 GP 专有列不在 iOS 展开列中，不能凭 GP 字段名直接套到 iOS。

## 事件族

BB 商业化埋点有两套常见事件族，不能不加说明地混在同一个指标里。

| 事件族 | 常见事件 | 适合场景 | 注意 |
|---|---|---|---|
| 旧 `s_*` 链路 | `s_moudle_ad_init`、`s_ad_request_test`、`s_ad_load_success` / `s_ad_load_success_test`、`s_ad_load_fail_test`、`s_ad_show_action`、`s_ad_show_fail`、`s_ad_show_success`、`s_ad_click` | 老版 SDK 链路、action / ready、老埋点字段校验 | GP / iOS 事件名和字段必传性不同，必须按端验证。 |
| 新 `ad_*` 链路 | `ad_load_start`、`ad_load_end`、`ad_show_ready`、`ad_show_start`、`ad_click`、`ad_show_end` | 三聚合 / 自建聚合 load、ready、展示、点击、关闭 | `load_status`、`is_ready`、`ad_type`、`ad_unit_id` 等字段进入 SQL 前需确认列或 JSON path。 |
| cross / ADX 链路 | `ad_load_start_cross`、`ad_load_end_cross`、`ad_click_cross`、`ad_show_end_cross`、`adx_sdk_ad_revenue` | ADX / 直连补充链路、内推替换、ADX 收入 | 必须过滤 `s_ad_extra_platform` 或 network 字段，不能与 MAX 回调收入混算。 |
| MAX 收入 | `appLovin_sdk_ad_revenue` | MAX 展示收入回调 | `revenue` 是收入；`adFormat`、`adUnitId`、`networkName` 字段命名大小写要按端验证。 |
| banner | `s_banner_session`、`s_banner_session_all` | banner session 和 banner eCPM 线索 | banner 字段多为方案相关线索，不自动等同展示收入事实。 |
| 竞价信息 | `s_ad_impression_bid` | MAX 多广告位比价、缓存、竞胜广告单元 | 多为数组 / object，需要 JSON 结构验证后再解析。 |

同一张报表里若必须同时展示旧链路和新链路，必须分列命名，例如 `legacy_action_cnt`、`ad_show_ready_cnt`，不要合并为一个 `ready_cnt`。

## 标准指标映射

| 指标 | 推荐事件 | 标准过滤 / 字段 | 风险 |
|---|---|---|---|
| 广告初始化成功 | `s_moudle_ad_init` | `s_moudle_result`、`s_moudle_platform` | 字段常在 `properties`，需验证是否展开。 |
| load 开始 | `ad_load_start` 或 `s_ad_request_test` | 广告格式、广告单元、network | 旧 / 新事件不能混算。 |
| load 结束 | `ad_load_end` | `load_status`、`load_time`、`ad_unit_id` | iOS 是否展开 `load_status` 要看表卡；必要时取 JSON。 |
| load 成功 | `ad_load_end` | `load_status = '1'` | 旧链路可用 `s_ad_load_success(_test)`，但需单独命名。 |
| ready | `s_ad_show_action` 或 `ad_show_ready` | `s_ad_ready = 'ready'` 或 `is_ready = true` | `s_ad_show_action` 是调用 show 接口时的状态，不等同 show 成功。 |
| show 成功 | `s_ad_show_success` 或 `ad_show_start` / show success 回调 | `ad_type` / `s_ad_type`、场景、广告单元 | 和 ready 指标分开。 |
| click | `s_ad_click` 或 `ad_click` | 广告格式、广告单元、场景 | 不点击不上报，不能作为曝光分母。 |
| show end | `ad_show_end` | `end_type`、`show_time` | 关闭时长和展示成功分母需分别说明。 |
| MAX 收入 | `appLovin_sdk_ad_revenue` | `revenue`、`adFormat`、`adUnitId`、`networkName` | `revenue` 单位需验证；不要和 eCPM 字段相加。 |
| ADX 收入 | `adx_sdk_ad_revenue` | `revenue`、`ad_format` / `adFormat`、`s_ad_extra_platform` | 与 MAX 收入分源输出，必要时再合并。 |

## 字段标准化

| 语义 | 候选字段 | 规则 |
|---|---|---|
| 广告格式 | `s_ad_type`、`ad_type`、`adFormat`、`ad_format` | 先按事件族确认字段；输出统一枚举前必须说明映射。 |
| 广告单元 | `s_ad_unit`、`ad_unit_id`、`adUnitId`、`placement`、`ad_placement` | 这些字段含义不完全相同，不得直接互换。 |
| network / 平台 | `s_ad_extra_platform`、`networkName`、`network_name`、`ad_network`、`s_network` | 区分 MAX、ADX、Pangle、Moloco 等来源。 |
| 串联 / load 标识 | `s_ad_series_id`、`load_id`、`session_id`、`ad_alg_series_id` | 用于链路关联前必须确认唯一性和粒度。 |
| 方案号 | `s_ad_public_adwaynum`、`data_ad_waynum`、AB3 array 字段 | AB3.0 `fs` / `rv` / `ba` 遵循 `AB3实验ID提取规则.md`。 |
| 价格层级 | `role`、`ad_adunit_rprm`、配置表 `price_type`、小包 Clean Unit ID 映射 | 小包使用 `小包广告单元映射.md`；非小包配置表优先。 |

## 收入、eCPM 和地板价

必须区分以下字段家族：

| 家族 | 常见字段 | 说明 |
|---|---|---|
| 收入 | `revenue`、`ad_revenue` | 展示收入或回调收入，单位需验证。 |
| eCPM | `s_ad_ecpm`、`last_ecpm`、`s_lastsession_ecpmavg` | 不是收入，不能直接与 revenue 相加。 |
| 地板价 / 走廊价 | `corridor_floor`、`base_corridor_floor`、`alg_corridor_floor`、`corridor_ceil` | 用于价格策略分析，不是广告收入。 |
| 预测 / postback | `pred_ecpm`、`postback`、`algo_service`、`x-request-id` | 算法链路线索，不能当真实收入。 |
| 填充率历史 | `s_ad_unit1_fillrate_last7d` 等 | 比例刻度存在 0.5、50、25.5 等写法，必须小窗口验证后再统一。 |

## 端差异和字段验证

- GP 和 iOS 事件名相似，但字段必传性、字段名大小写和是否展开为列不同。
- iOS 表卡存在 GP 专有列缺失记录；需要的字段若未展开，使用 `GET_JSON_OBJECT(properties, '$.<field>')` 前必须先小窗口验证。
- `countryCode` / `country_code`、`networkName` / `network_name`、`adFormat` / `ad_format` 这类大小写差异不能自动合并。
- `s_ad_load_success` 和 `s_ad_load_success_test` 需要按端和版本确认，不要只凭名字近似合并。

## PII 和输出限制

以下字段不得输出明细：

- `distinct_id`、`device_id`、`s_user_idfa`、IDFA / GAID、IP、经纬度。
- `fcmToken`、push token、click URL、广告主 raw object、完整 `postback`。
- 用户级 `session_id` / `load_id` 明细。

这些字段只可用于内部 join、去重或聚合，并在输出中说明聚合边界。

## 与其他协议的关系

- 白名单表过滤和 JSON 提取遵循 `白名单事件表查询协议.md`。
- 商业化指标和 join 护栏遵循 `商业化SQL协议.md`。
- 大埋点字典、非商业化事件、APM、push、支付、web / H5 和端差异字段遵循 `BB大埋点字典使用规则.md`。
- 小包价格层级遵循 `小包广告单元映射.md`。
- AB3.0 实验遵循 `AB3实验ID提取规则.md`。
- 可复用 SQL 晋升遵循 `da_assets/SQL晋升治理.md`。
