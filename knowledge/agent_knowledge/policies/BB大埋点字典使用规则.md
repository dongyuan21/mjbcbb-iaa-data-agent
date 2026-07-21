# BB 大埋点字典使用规则

> 状态：active  
> 创建日期：2026-06-19  
> 适用范围：Block Blast GP / iOS 大埋点明细字典中的事件名、参数名、端差异、PII 风险和白名单事件 SQL 使用边界。

## 使用边界

本文用于把大埋点字典作为“事件和参数候选线索”使用，不直接把字典整本加入默认事实。

可以作为当前默认规则使用：

- 判断 BB GP / iOS 埋点属于哪个事件族。
- 识别广告、玩法、AB、APM、支付、push、web / H5、waterfall / mediation 等字段族。
- 约束 PII、token、广告主 raw object、request id、postback 等高风险字段的输出边界。
- 提醒 GP / iOS 同名事件字段类型、大小写、必传性和枚举可能不同。

不能直接作为 verified 事实使用：

- 字典里的每个事件名、参数名、枚举值和字段类型。
- 未在目标白名单事件表中验证过的展开列。
- 未经小窗口验证的 `properties` JSON path。
- 任何用户级、设备级、token 级或广告主 raw object 明细。

字典线索进入 SQL 前，必须至少满足一种验证：

```text
event_metadata_confirmed
schema_probe_confirmed
small_window_json_confirmed
table_card_confirmed
```

否则输出 `event_or_field_candidate_only`。

## 字典规模和默认召回原则

大埋点字典是宽表格导出：

| 端 | 粗略事件规模 | 使用方式 |
|---|---:|---|
| GP | 约 1000+ 个事件名 | 只抽事件族、字段族和风险边界，不整本进默认召回。 |
| iOS | 约 700+ 个事件名 | 只抽事件族、字段族和风险边界，不整本进默认召回。 |

默认召回层只保留本文的规则。需要具体事件或参数时，优先走：

1. `特征工程与埋点元数据查询规则.md` 中的 CS 埋点元数据表。
2. BB 白名单事件表表卡。
3. 小窗口事件样本验证。
4. 大埋点字典作为候选线索。

## 事件族

| 事件族 | 常见前缀 / 事件 | 用途 | 注意 |
|---|---|---|---|
| 新广告链路 | `ad_load_start`、`ad_load_end`、`ad_show_ready`、`ad_show_start`、`ad_show_end`、`ad_click` | 三聚合 / 自建聚合 load、ready、show、click、关闭链路 | 字段在 GP / iOS 上可能类型不同，必须验证。 |
| cross / ADX 链路 | `*_cross`、`adx_sdk_ad_revenue`、`adx_no_inter_ad_model_received` | ADX / 直连 / 内推替换链路 | 必须区分 `s_ad_extra_platform`、network、ADX 和 MAX。 |
| 旧广告链路 | `s_ad_request_test`、`s_ad_load_success*`、`s_ad_show_action`、`s_ad_show_success`、`s_ad_show_fail`、`s_ad_click` | 旧 SDK 链路、ready、show、fail、click | 不能和新 `ad_*` 链路无说明混算。 |
| SDK 收入 | `appLovin_sdk_ad_revenue`、`admob_sdk_ad_revenue`、`hs_sdk_ad_revenue`、`adx_sdk_ad_revenue` | 展示收入回调、SDK 收入 | `revenue`、`ad_revenue`、`ecpm`、`pred_ecpm` 不能互换。 |
| mediation / waterfall | `hs_mediation_*`、`hs_waterfall_*`、`ir_waterfall_*`、`hs_bidding_*` | 聚合、waterfall、bidding 过程 | `platformunitid`、广告主对象和 request id 不输出明细。 |
| 玩法行为 | `game_*`、`g_game_*`、`block_*`、`puzzle_*` | 开局、结算、移动、复活、道具、主题、关卡、小游戏 | 优先使用局 / 轮 / 出块表或已治理解析表；事件表只作补充。 |
| AB / 模型 / 分流 | `abtest_*`、`block_abtest_info*`、`game_run_ab`、`usr_data_AB`、`game_*model*` | 实验方案、模型输出、分流状态 | 与 AB3.0、实验配置表和方案表交叉验证。 |
| APM / 技术诊断 | `s_apm_*`、`hs_apm_*`、`s_tech_*`、`cocos_*`、`s_UnityPro_*` | 性能、启动、网络、资源、崩溃诊断 | 只输出聚合指标；不要输出设备级诊断明细。 |
| 生命周期 / push | `ta_app_*`、`hs_app_*`、`s_app_*`、`s_push_*`、`usr_device_install` | 启动、安装、push token、前后台、权限 | token 和设备标识严格禁止输出。 |
| 支付 / 订阅 | `s_g_pay_success`、`s_create_order_success`、`s_verify_order_success`、`s_appreceipt`、`s_vip_upgrade` | IAP 支付、订单、订阅 | 订单 token、receipt、sku 明细需脱敏或聚合。 |
| web / H5 / 社媒 | `web_*`、`usr_data_socialmedia_*`、`ui_*` | H5 页面、活动、社媒、UI 行为 | `userEmail`、链接、作者 ID、视频 ID 等不要输出明细。 |

商业化链路的指标、事件族和收入边界仍以 `BB商业化埋点查询规则.md` 为主；本文补充完整大字典层面的风险边界。

## GP / iOS 端差异

GP 和 iOS 大埋点字典不能互相直接套字段：

- iOS 常见数数预置属性包括 `#lib`、`#simulator`、`#relaunched_in_background`，GP 不一定同样出现或同名。
- iOS 收入和广告事件中可能出现 `s_user_idfa`、`#simulator`、`postback`、`pg_*`、`meta_ad_revenue` 等字段；输出边界更严格。
- 同名字段类型可能不同，例如 `load_time` 可能是 string、double 或 long；`arm_id` 可能是 int 或 string。
- `load_status`、`is_ready`、`ad_type`、`s_ad_type`、`adFormat`、`ad_format`、`ad_unit_id`、`adUnitId` 的枚举和大小写不能自动合并。
- 旧链路里 iOS 存在 `s_ad_load_success_3670`、`s_ad_load_success_3730`、`s_ad_load_success_3820` 等版本化事件名，GP 端未必一致。
- iOS 的 `ad_close`、GP 的 `ad_show_end` / `ad_show_end_cross` 等关闭类事件不能只按名字近似合并。

跨端 SQL 必须分端 CTE 或分端字段映射，最后 `UNION ALL` 到统一列名；无法验证时输出 `cross_platform_field_mapping_pending`。

## 高风险字段

以下字段或字段族不得输出明细：

| 字段族 | 例子 | 风险 |
|---|---|---|
| push / token | `fcmToken`、`s_push_token`、`s_header_token`、`old_access_token` | token / 凭证。 |
| 设备 / 用户标识 | `distinct_id`、`deviceId`、`device_id`、`s_user_idfa`、IDFA / GAID、`uuid` | 用户或设备级标识。 |
| 会话 / 请求标识 | `session_id`、`load_id`、`round_id`、`s_ad_series_id`、`x-request-id`、`pg_request_id`、`alg_request_id` | 链路排查 ID，不能对外明细。 |
| 支付 / 订单 | `s_pay_token`、`s_pay_order_token`、receipt、sku 明细 | 交易和订单敏感信息。 |
| 广告主 raw object | `advertiser_info`、`postback`、`adomain`、`bundle`、`crid` | 广告主原始对象和回传参数。 |
| 联系方式 / 链接 | `userEmail`、email、video link、作者 ID、视频 ID | 个人信息或外部内容链接。 |
| 平台单元 ID | `platformunitid` | 广告平台广告单元明细；只可聚合或内部 join。 |

如果确实需要链路排查，应只在库内使用这些字段做 join、去重或聚合，并在输出中写 `pii_aggregation_only`。

## 字段语义边界

广告收入和 eCPM：

- `revenue`、`ad_revenue`、`meta_ad_revenue` 是收入线索，但单位和归因来源必须验证。
- `s_ad_ecpm`、`ecpm`、`last_ecpm`、`s_lastsession_ecpmavg`、`pred_ecpm`、`pg_model_ecpm` 是 eCPM / 预测 / 历史值，不是收入。
- `abp_5_int`、`abp_5_rew`、`dir_r` 是广告价值或最近展示收入线索，不一定是展示回调收入。

广告单元和价格层级：

- `ad_unit_id`、`adUnitId`、`ad_placement`、`placement`、`platformunitid` 含义不同，不能直接互换。
- `role`、`ad_adunit_rprm`、`s_ad_adunit_level` 是广告位价值层级线索，不等同所有产品的 `price_type`。
- 小包价格层级必须使用 `小包广告单元映射.md`，不要从 BB 大字典的 `role` 直接推断。

广告格式和平台：

- `ad_type`、`s_ad_type`、`adFormat`、`ad_format` 常见枚举包括插屏、激励、banner，但命名随事件族和端变化。
- `s_ad_extra_platform`、`ad_network`、`networkName`、`platform`、`ad_platform` 不是同一个字段，需要逐事件确认。
- `ADX`、`MAX`、`AdMob`、`Moloco`、`Pangle`、`IronSource` 等来源要分列或分源说明。

链路关联：

- `load_id` 标识一次 load。
- `s_ad_series_id` 常用于串联广告链路。
- `session_id` 是会话线索。
- `round_id` 可用于一轮连续请求。

这些字段可以帮助链路排查，但不能直接输出用户级明细，也不能在没有唯一性验证时作为强 join key。

## 查询流程

写 BB 大埋点 SQL 时：

1. 先按需求判断是否已有聚合主题表、局 / 轮 / 出块表、商业化实验表或 verified SQL。
2. 只有聚合层不能覆盖时，才回白名单事件表。
3. 用 `SQL表路由协议.md` 确认 BB GP / iOS 表族和端过滤。
4. 用 `特征工程与埋点元数据查询规则.md` 或 schema probe 确认事件名、参数名和 Hudi 展开列。
5. 商业化链路同时遵守 `BB商业化埋点查询规则.md`。
6. 白名单事件 SQL 必须带 `dt`、`event_name`；共享表必须带 `app_name`。
7. 高风险字段只用于内部 join / 去重 / 聚合，不输出明细。

## 输出要求

输出 BB 大埋点查询时必须说明：

- 使用的事件族：新广告链路、旧广告链路、玩法、AB、APM、支付、push、web / H5 等。
- 端：GP、iOS 或双端；双端时说明字段映射方式。
- 字段来源：展开列、`properties` JSON、元数据表、表卡或小窗口验证。
- 收入和 eCPM 是否混用，以及单位是否验证。
- PII / token / request id / 广告主 raw object 是否已排除。
- 未验证字段标 `event_or_field_candidate_only` 或 `small_window_validation_required`。

## 维护规则

本文只沉淀大字典的使用规则和风险边界。具体事件和参数不逐项搬入默认召回；如果某个事件族被反复使用，应优先补充到 `ai_hive/agent_knowledge/tables/` 的 table card、`da_assets/candidate_sql/` 或 `da_assets/verified_sql/`，并保留 schema / 小窗口验证记录。
