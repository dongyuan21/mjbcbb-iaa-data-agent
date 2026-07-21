# 皇室麻将 BI 看板查询规则

> 状态：active  
> 创建日期：2026-06-19  
> 适用范围：Mahjong Blast / 皇室麻将的解析表、白名单事件表、用户属性表、AB 实验看板底表和 BI 看板指标口径。

## 使用边界

本文用于 MB 查询选表、BI 看板口径解释和 SQL 审查，不直接提供 verified SQL。

可以作为当前默认规则使用：

- 判断 MB 查询优先走解析表、白名单事件表、用户属性表还是 BI 看板聚合层。
- 区分 `start_uv`、`install_game_join_uv`、`game_cnt`、广告收入、banner 和异常处理口径。
- 解释 01 / 02 / 03 三层 BI 底表的关系和每层产出。

不能直接作为 verified 事实使用：

- 未进入 `ai_hive/agent_knowledge/catalog.yaml` 和表卡的 MB 解析表、实验汇总表、留存表和看板聚合表。
- 底表 SQL 中的整段逻辑、临时中间表或 UDF 结果。
- 未经 schema probe / 小窗口验证的字段、分区、小时、收入单位和实验方案字段。

候选表未表卡化时输出：

```text
candidate_table_requires_intake
```

## 产品和表路由

MB 默认产品过滤：

| 端 | app_name | bundle_id |
|---|---|---|
| GP | `nova_mahjong_gp` | `com.nebula.mahjongtile` |
| iOS | `nova_mahjong_ios` | `com.nebula.mahjongtile.ios` |

表路由优先级：

| 场景 | 优先表 / 表族 | 状态 | 规则 |
|---|---|---|---|
| 局内解析、用户画像、实验字段拆解 | `hungry_studio.dws_nova_mahjong_all_parsed_board_game_click_di`、`hungry_studio.dws_nova_mahjong_gp_parsed_board_game_click_di` | candidate | 优先用于局内过程、画像和实验线索；需补表卡。 |
| 事件级行为、广告、收入、异常事件 | `hungry_studio.dwd_nova_collection_all_white_event_unique_data_hi` | 已有表卡 | 必须带 `dt`、`event_name`、`app_name`。 |
| 用户属性、设备、归因、画像补充 | `hungry_studio.dim_nova_collection_all_user_ha` | 已有表卡 | 必须带 `dt`、`hour`、`app_name`；不是单日新增表。 |
| AB 看板 01 层 | `hungry_studio.dws_nova_collection_all_abtest_user_multi_dim_hi` | candidate | 用户 × 日期 × 方案 × app × game_mode 的基础指标层。 |
| AB 看板 02 层 | `hungry_studio.dws_nova_collection_all_user_ab_retention_hi` | candidate | 拼实验配置、媒体、国家、年龄、设备等级等维度的留存明细层。 |
| AB 看板 03 层 | `hungry_studio.ads_nova_nebula_all_ab_with_dimension_and_media_type_hi` | candidate | 看板聚合层，直接服务 UV、PV、收入、局数、时长等看板指标。 |

选表原则：

- 能用 03 层解释看板指标时，不回扫事件表复算。
- 需要用户级留存、方案、维度拆分时，再看 02 层。
- 需要基础事件聚合或字段来源解释时，再看 01 层。
- 需要局内过程、操作数组、用户技能、画像快照时，优先看解析表。
- 只有解析表或看板层无法覆盖时，才回到白名单事件表。

## 常用过滤

MB 查询通常需要先在最内层统一过滤：

- `app_name = 'nova_mahjong_gp'` 或 `app_name = 'nova_mahjong_ios'`。
- `dt` 或看板分区日期；小时表必须同时带 `hour`。
- `event_name`，如果使用白名单事件表。
- `game_mode = 0`，当需求限定无尽模式或看板主模式时。
- `is_formal = true`，当需求限定正式服 / 正式局时。
- 版本过滤必须拆版本号做数值比较，不要直接按字符串比较。
- `install_day` 只在需求明确新用户 / 老用户或看板口径要求时使用；常见新用户线索为 `install_day <= 14`，老用户线索为 `install_day > 14`。

AB 实验场景：

- 优先从实验配置表补实验时间、方案号和下线状态；配置表不可用时再问用户。
- 同一分析里尽量统一使用同一版解析表或同一层看板表，避免把解析表、事件表和看板聚合层混成一个事实口径。
- 输出必须说明方案字段来源，如 `active_ab`、`way_id`、`ab_waynum`、`game_way_num`。

用户属性表注意：

- `dim_nova_collection_all_user_ha` 是小时快照全量用户属性表，不是当天新增用户表。
- 只写 `dt` 会扫多个小时分区并可能重复；必须补 `hour`。
- 用户画像字段只用于聚合或取最新有效记录，不输出 `distinct_id`、设备 ID、AF ID 等用户级明细。

## 麻将白名单事件

MB 看板不是读取所有事件。01 层从白名单事件进入多维指标层，常见事件包括：

| 事件 | 常见用途 |
|---|---|
| `ta_app_start`、`ta_app_end`、`ta_app_install` | 启动、结束、安装相关活跃线索。 |
| `g_user_data_AB`、`s_user_data_AB` | 实验和用户分组线索。 |
| `g_game_open`、`g_game_start`、`g_game_end` | 进入游戏、开局、结算和局数指标。 |
| `g_btn_click` | 按钮行为。 |
| `s_game_ad_revenue` | 当前 MB 广告收入主口径。 |
| `g_game_banner_revenue`、`hs_ad_banner_revenue` | banner 兼容字段；当前通常接近 0，需验证。 |
| `s_ad_show_success`、`s_ad_show_action`、`appLovin_sdk_ad_revenue` | 广告展示、action 和 SDK 收入线索。 |
| `s_crash_or_anr` | 异常用户线索。 |
| `s_g_pay_success`、`s_create_order_success`、`s_verify_order_success` | IAP 支付相关线索。 |

因此：

- `start_uv` 不是只看 `ta_app_start`。
- `start_uv` 是命中 MB 白名单事件后的留存活跃口径。
- `install_game_join_uv` 更严格，只看 `g_game_open` / `g_game_start` / `g_game_end` 这类游戏行为。

## BI 三层表关系

| 层级 | 表 | 粒度 | 核心作用 |
|---|---|---|---|
| 01 | `dws_nova_collection_all_abtest_user_multi_dim_hi` | 用户 × 日期 × 方案 × app × game_mode | 从白名单事件聚合启动、广告、局数、时长、收入、异常等基础指标。 |
| 02 | `dws_nova_collection_all_user_ab_retention_hi` | 用户 × 方案 × 留存日 × 维度 | 拼实验配置、媒体、国家、用户价值、年龄、设备等级、来源和留存字段。 |
| 03 | `ads_nova_nebula_all_ab_with_dimension_and_media_type_hi` | 方案 × 维度 × app × game_mode | 看板聚合层，产出 UV、PV、收入、局数、时长、Bayes / 底板信息等指标。 |

03 层常见维度：

- `game_way_num`、`game_way_type`、`game_way_type_alias`。
- `country_group`、`user_value`、`ab_install_day`、`source`。
- `game_mode`、`age_group`、`device_level`、`media_type`。
- `is_db` 用于识别底板组；底板指标参与 Bayes 计算，不等同普通实验组指标。

## 核心口径

核心指标公式以 `游戏核心指标口径语义.md` 的 MB 专项口径为准。本文补充以下看板解释：

| 指标 | 解释 |
|---|---|
| `start_uv / install_uv` | 人均活跃天；`start_uv` 是白名单事件活跃口径。 |
| `install_game_join_uv / install_uv` | 游戏对局率；比 `start_uv` 更接近真正游戏行为。 |
| `game_cnt` | 所有 `g_game_end`，包含“重新开始”。 |
| `retry_game_cnt` | `g_game_end` 且状态为重新开始；不要从 `game_cnt` 中默认剔除。 |
| `ad_revenue` | 当前主看 `s_game_ad_revenue` 汇总后的广告收入。 |
| `inter_ad_revenue` / `rewarded_ad_revenue` | 插屏 / 激励拆分收入。 |
| `banner_ad_revenue` / `banner_ad_pv` | 当前 MB 通常接近 0；出现非 0 先排查历史分区、脏数据或口径变更。 |
| `game_realtime / install_uv` | 人均结算时长。 |
| `game_realtime / game_cnt` | 人均单局时长。 |
| `s_crash_or_anr_uv` | 异常用户分子；异常率分母需要确认是 `install_uv` 还是 `start_uv`。 |

综合提升率只作为看板候选评分说明：

```text
留存提升率 * 0.6 + 收入提升率 * 0.15 + 人均广次提升率 * 0.05 + 结算时长提升率 * 0.15 + 结算局数提升率 * 0.05
```

使用综合提升率时必须说明：

- 单项提升率是实验组相对底板均值。
- 权重是否仍为当前业务确认口径。
- 不把该分数直接作为自动推全 / 下线决策。

## 异常值处理

对齐 MB 看板时，需确认以下异常处理是否写入 SQL：

| 字段 | 处理 |
|---|---|
| 插屏收入 | 单方案、人天、模式粒度大于 5 时按 5 计。 |
| 激励收入 | 单方案、人天、模式粒度大于 5 时按 5 计。 |
| `game_cnt` | 大于 300 时记为 0。 |
| `game_score` | 大于 1000000 时记为 0。 |
| 单局结算时长 | 大于 24 小时记为 0；大于 2 小时封顶为 2 小时。 |

如果用户要求“和看板一致”，必须说明异常处理是否已确认；未确认时输出 `needs_metric_validation`。

## SQL 生成和审查要求

生成或审查 MB SQL 时必须说明：

- route_taken：解析表、白名单事件表、用户属性表、BI 01 / 02 / 03 层。
- data_source：表卡、catalog、semantic policy、schema probe 或 candidate table。
- 产品过滤：`app_name`、端、`bundle_id` 是否一致。
- 时间过滤：`dt`、`hour`、实验起止时间、`process_dt` / `process_hour` 是否是生产调度字段。
- 活跃口径：`start_uv` 还是 `install_game_join_uv`。
- 收入口径：是否含 banner，收入单位和 eCPM 倍率是否已验证。
- 异常处理：收入、局数、分数、时长是否已处理。
- PII 边界：不输出 `distinct_id`、设备 ID、AF ID、原始 `properties` 或用户级明细。

底表 SQL 只能作为生产口径线索。要把其中某段 SQL 晋升为可复用 SQL，必须先拆成 `da_assets/candidate_sql/`，再按 `da_assets/SQL晋升治理.md` 做小窗口验证和晋升。

## 维护规则

本文只维护 MB 查询和 BI 看板口径边界。候选表的 grain、partitions、query_rules、PII、freshness、join_keys、known_pitfalls 和 example_queries 必须回到 `ai_hive/agent_knowledge/tables/` 一表一卡治理；待补清单见 `TODO/SQL写作链候选表准入积压清单.md`。
