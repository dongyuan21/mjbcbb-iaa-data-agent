# SQL 写作链候选表 intake backlog

> 状态：needs_intake  
> 创建日期：2026-06-19  
> 用途：记录 SQL 写作链资料中出现、但当前不能直接当作已治理表卡使用的候选表。本文是待办清单，不是默认事实来源。

## 使用边界

- 只有进入 `ai_hive/agent_knowledge/catalog.yaml` 和 `ai_hive/agent_knowledge/tables/`，并通过表卡质量门禁后，候选表才能作为稳定表卡召回。
- 未入表卡前，SQL 只能在 schema probe / dry-run / 小窗口验证后作为 `candidate_sql` 输出。
- 表名即使来自 DA 认证资料，也不能替代字段、分区、join、PII、freshness 和 example query 治理。

## 当前候选表

| 主题 | 候选表 | intake 要点 |
|---|---|---|
| 白名单主题 | `acme_studio.dwd_b-b_all_white_event_unique_data_hi` | 与当前 GP / iOS 白名单表卡关系待确认；必须写明 `app_name`、`event_name`、分区。 |
| 白名单主题 | `acme_studio.dwd_kcolb_collection_all_white_event_unique_data_hi` | DT 共享白名单事件表；需补 app_name、event_name、PII 和 freshness。 |
| 用户属性主题 | `acme_studio.dim_kcolb_collection_all_user_ha` | DT 用户属性快照；需补分区、hour、join key 和 PII。 |
| 用户属性主题 | `acme_studio.dim_kcolb_collection_all_user_label_da` | DT 用户标签天级表；需确认与用户属性表关系。 |
| 用户属性主题 | `acme_studio.dim_nova_collection_all_user_label_da` | nova 系用户标签天级表；需确认和 `*_label_ha` 的粒度差异。 |
| 用户行为主题 | `acme_studio.dws_b-b_gp_user_multi_dim_di` | BB GP 用户日行为聚合；需补指标字段族和分区。 |
| 用户行为主题 | `acme_studio.dws_b-b_ios_user_multi_dim_di` | BB iOS 用户日行为聚合；需补指标字段族和分区。 |
| 用户行为主题 | `acme_studio.dws_kcolb_collection_all_user_multi_dim_hi` | DT 用户行为聚合；需补 `app_name`、hour、收入字段族。 |
| 留存主题 | `acme_studio.dws_b-b_gp_new_user_retention_hi` | BB GP 新用户留存；需确认全量快照和 business date 字段。 |
| 留存主题 | `acme_studio.dws_b-b_ios_new_user_retention_hi` | BB iOS 新用户留存；需确认全量快照和 business date 字段。 |
| 留存主题 | `acme_studio.dws_kcolb_collection_all_user_retention_da` | DT 留存；需补 app_name、分区和 retention day 字段。 |
| 留存主题 | `acme_studio.dws_nova_collection_all_user_retention_da` | nova 系留存；需补 app_name、分区和 retention day 字段。 |
| 实验方案主题 | `acme_studio.dws_b-b_all_new_abtest_user_multi_dim_hi` | BB 实验用户多维；需补方案字段、实验时间和 join key。 |
| 实验汇总主题 | `acme_studio.dws_b-b_all_new_abtest_user_way_agg_hi` | BB 新双端实验用户方案汇总；需补全量快照、hour、收入单位、is_locked / pici 字段边界。 |
| 方案留存主题 | `acme_studio.dws_b-b_all_new_abtest_user_retention_hi` | BB 新双端实验留存明细；需补 is_ab、retention_days、active_date、收入单位和新旧表替代关系。 |
| 实验方案主题 | `acme_studio.dws_kcolb_collection_all_new_abtest_user_multi_dim_hi` | DT 实验用户多维；需补 app_name、方案字段和 hour。 |
| 方案留存主题 | `acme_studio.dws_b-b_gp_new_abtest_active_join_user_ab_retention_hi` | BB GP 方案留存；需确认人均留存天数和 RR 口径。 |
| 方案留存主题 | `acme_studio.dws_b-b_ios_new_abtest_active_join_user_ab_retention_hi` | BB iOS 方案留存；需确认人均留存天数和 RR 口径。 |
| 方案留存主题 | `acme_studio.dws_kcolb_collection_all_new_abtest_user_retention_hi` | DT 方案留存；需确认 app_name 和 retention 字段。 |
| 实验汇总主题 | `acme_studio.dws_kcolb_collection_all_new_abtest_user_way_agg_hi` | DT 方案汇总表；需确认已聚合周期、字段含义和适用实验类型。 |
| 投放主题 | `acme_studio.ads_market_nova_nebula_ad_detail_di` | nova 系投放明细；需补 app_name / bundle_id 过滤和 campaign 粒度。 |
| ROI 预估主题 | `hs_user_growth.ads_pg_ma0j_blest_launch_revenue_predict_v1` | 预估表；需确认产品适用范围、预测版本、真实/预估边界。 |
| 局粒度主题 | `acme_studio.dws_b-b_ios_kcolb_action_game_di` | BB iOS 局表；需补 game_id / session / 局结束口径。 |
| 轮维度主题 | `acme_studio.dws_b-b_gp_kcolb_action_round_di` | BB GP 轮表；需明确仅在局表不够时使用。 |
| 轮维度主题 | `acme_studio.dws_b-b_ios_kcolb_action_round_di` | BB iOS 轮表；需明确仅在局表不够时使用。 |
| 出块维度主题 | `acme_studio.dwd_b-b_gp_kcolb_action_kcolb_di` | BB GP 出块表；高扫描风险，需补分区和限制条件。 |
| 出块维度主题 | `acme_studio.dwd_b-b_ios_kcolb_action_kcolb_di` | BB iOS 出块表；高扫描风险，需补分区和限制条件。 |
| MB 解析主题 | `acme_studio.dws_nova_ma0j_gp_parsed_board_game_click_di` | MB GP 点击解析明细；需补 grain、PII、game_mode、is_formal。 |
| MB 看板主题 | `acme_studio.ads_nova_nebula_all_ab_with_dimension_and_media_type_hi` | MB 看板聚合层；需确认维度、分区、指标口径。 |
| 实验配置主题 | `acme_studio.dim_nova_nebula_all_ab_plan_conf_ha` | MB / nova 实验配置；需补 hour、方案字段。 |
| AB 标记主题 | `acme_studio.dim_b-b_all_new_ab_title_mark_realtime` | AB 方案特性表；需确认实时表权限、join key 和适用场景。 |
| 模型特征主题 | `acme_studio.dws_b-b_gp_user_feature_v1_da` | BB GP 用户特征；需补特征语义、label 泄漏风险。 |
| 模型特征主题 | `acme_studio.dws_b-b_ios_user_feature_v1_da` | BB iOS 用户特征；需补特征语义、label 泄漏风险。 |
| AF ODS 主题 | `acme_studio.ods_appsflyer_locker_sync_data_installs_mc_di` | AF 标准安装 ODS；需补字段、PII、dt 和日扫描风险。 |
| AF ODS 主题 | `acme_studio.ods_appsflyer_locker_sync_data_post_attribution_installs_di` | AF 归因后安装；需补 conversion_type、reinstall 口径。 |
| 成本主题 | `acme_studio.dwd_market_api_spend_di` | 媒体 API spend DWD 表；需确认与当前 `ods_market_api_spend_di` / spend 表卡的层级和字段差异。 |
| 汇率配置主题 | `acme_studio.dim_market_config_currency_usd_di` | 汇率配置候选；需补币种、日期字段和 cost_zhe/USD 换算边界。 |
| 媒体配置主题 | `acme_studio.dim_market_dsp_media_source_list_da` | DSP media_source 配置候选；需确认和 channel mapping / media_source 标准化关系。 |
| 埋点元数据主题 | `acme_studio.dim_cs_data_origin_event_bgd_games_project` | 产品/项目表；需补 game_id / app_id / os join 规则。 |
| 埋点元数据主题 | `acme_studio.dim_cs_data_origin_event_bgd_bi_os_user_attr` | 用户属性定义表；需补产品过滤和字段映射。 |
| 实验配置主题 | `acme_studio.dim_nova_nebula_all_syh_ab_plan_conf_ha` | nova / MB 实验配置补录候选；需补 hour、方案字段和适用产品。 |
| 实验配置主题 | `acme_studio.dim_sudoku_all_ab_plan_conf_ha` | Sudoku 实验配置候选；需确认是否纳入当前 Data Agent 产品范围。 |
| 实验中间层主题 | `acme_studio.dws_nova_collection_all_abtest_user_multi_dim_middle_data_hi` | nova 系实验用户多维中间层；需确认和正式宽表的取数边界。 |
| 实验中间层主题 | `acme_studio.dws_nova_nebula_gp_abtest_user_multi_dim_middle_data_hi` | nova/MB GP 实验用户多维中间层；需确认产品、app_name 和中间层可用性。 |

## 差异复核说明

- 2026-06-19 用源包文本复算全限定表名：64 张有效表，另有 `acme_studio.table_name` 占位符已排除。
- 其中 23 张已进入当前 `ai_hive/agent_knowledge/catalog.yaml`，41 张源包表尚未入 catalog。
- 上表保留 3 张本轮文本抽取未命中的 legacy 扩展候选：`acme_studio.dim_b-b_all_new_ab_title_mark_realtime`、`acme_studio.dim_kcolb_collection_all_user_label_da`、`acme_studio.dws_b-b_all_new_abtest_user_multi_dim_hi`；后续需复核是否仍属于 SQL 写作链 intake 范围。

## 本轮已完成 intake

> 完成日期：2026-06-19  
> 验证边界：以下表已进入 `ai_hive/agent_knowledge/tables/` 与 `ai_hive/agent_knowledge/catalog.yaml`，并通过 `check_table_card_quality.py`；状态是 `schema_validated_only`，不等于 verified SQL 或 owner 确认口径。

| 主题 | 已入表卡 | 落点 |
|---|---|---|
| 实验配置主题 | `acme_studio.dim_b-b_abtest_conf_sq_ha` | `ai_hive/agent_knowledge/tables/dim_b-b_abtest_conf_sq_ha.yaml` |
| 商业化配置主题 | `acme_studio.dim_b-b_gp_ad_realization_ab_pici_adunit_base_conf_ha` | `ai_hive/agent_knowledge/tables/dim_b-b_gp_ad_realization_ab_pici_adunit_base_conf_ha.yaml` |
| 实验配置主题 | `acme_studio.dim_all_app_ab_test_plan_conf_view` | `ai_hive/agent_knowledge/tables/dim_all_app_ab_test_plan_conf_view.yaml` |
| 商业化实验主题 | `acme_studio.dws_b-b_all_ad_realization_active_user_ab_life_orthogonal_retention_hi` | `ai_hive/agent_knowledge/tables/dws_b-b_all_ad_realization_active_user_ab_life_orthogonal_retention_hi.yaml` |
| 实验方案主题 | `acme_studio.dws_nova_collection_all_abtest_user_multi_dim_hi` | `ai_hive/agent_knowledge/tables/dws_nova_collection_all_abtest_user_multi_dim_hi.yaml` |
| 方案留存主题 | `acme_studio.dws_nova_collection_all_user_ab_retention_hi` | `ai_hive/agent_knowledge/tables/dws_nova_collection_all_user_ab_retention_hi.yaml` |
| MB 解析主题 | `acme_studio.dws_nova_ma0j_all_parsed_board_game_click_di` | `ai_hive/agent_knowledge/tables/dws_nova_ma0j_all_parsed_board_game_click_di.yaml` |
| 局粒度主题 | `acme_studio.dws_b-b_gp_kcolb_action_game_di` | `ai_hive/agent_knowledge/tables/dws_b-b_gp_kcolb_action_game_di.yaml` |
| 投放主题 | `acme_studio.ads_market_kcolb_collection_ad_detail_di` | `ai_hive/agent_knowledge/tables/ads_market_kcolb_collection_ad_detail_di.yaml` |
| AF 激活主题 | `acme_studio.dim_market_appsflyer_activation_pull_da` | `ai_hive/agent_knowledge/tables/dim_market_appsflyer_activation_pull_da.yaml` |
| 成本主题 | `acme_studio.dwd_market_cost_di` | `ai_hive/agent_knowledge/tables/dwd_market_cost_di.yaml` |
| SDK 收入主题 | `acme_studio.dwd_market_sdk_revenue_attributed_di` | `ai_hive/agent_knowledge/tables/dwd_market_sdk_revenue_attributed_di.yaml` |
| 埋点元数据主题 | `acme_studio.dim_cs_data_origin_event_bgd_bi_events_v2` | `ai_hive/agent_knowledge/tables/dim_cs_data_origin_event_bgd_bi_events_v2.yaml` |
| 埋点元数据主题 | `acme_studio.dim_cs_data_origin_event_bgd_bi_attr` | `ai_hive/agent_knowledge/tables/dim_cs_data_origin_event_bgd_bi_attr.yaml` |
| 素材映射主题 | `acme_studio.ods_market_ad_material_maps_da` | `ai_hive/agent_knowledge/tables/ods_market_ad_material_maps_da.yaml` |

## 下一步处理

1. 剩余候选表继续按 P0 / P1 需求做 `DESC` 或 PyODPS schema probe。
2. 对可用表补 `ai_hive/agent_knowledge/tables/*.yaml`，写清 grain、partitions、query_rules、join_keys、PII、freshness 和 example_queries。
3. 跑 `python3 tools/scripts/check_table_card_quality.py`，硬错误清零后再从本 backlog 移除。
