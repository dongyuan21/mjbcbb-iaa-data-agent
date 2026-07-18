# 用户增长Topic 表缺口报告

> 来源：用户在 DataWorks 数据地图「用户增长Topic」手工贴入的 55 张表。  
> 对比对象：`ai_hive/agent_knowledge/catalog.yaml`。
> 探查方式：`maxcompute-dataworks` / PyODPS 只读读取 MaxCompute schema，不扫描业务数据。

## 总览

- Topic 表总数：**55**
- 当前 `ai_hive` 已收录：**3**
- 当前 `ai_hive` 未收录：**52**
- 未收录但在线存在：**52**
- 未收录且探查失败/不存在：**0**

## 已收录

| 表 | 说明 |
|---|---|
| `dim_market_campaign_s2s_event_map_da` | 已在 `ai_hive/agent_knowledge/catalog.yaml` |
| `dwd_market_meta_capi_push_ready_hi` | 已在 `ai_hive/agent_knowledge/catalog.yaml` |
| `dws_market_capi_user_hourly_metrics_wide_ha` | 已在 `ai_hive/agent_knowledge/catalog.yaml` |

## 缺口分类统计

| 分类 | 数量 |
|---|---:|
| MI/ROI事实与预估 | 11 |
| Meta CAPI/受众推送 | 5 |
| 产品设备/用户聚合 | 11 |
| 其他 | 1 |
| 媒体API/Campaign素材元数据 | 14 |
| 设备资产/用户资产 | 10 |

## 建卡优先级

### P0

| 表 | 分类 | 表说明 | 字段数 | 分区 | 日期字段候选 |
|---|---|---|---:|---|---|
| `ads_market_af_cohort_user_acquisition_v2` | MI/ROI事实与预估 | MI看板-AF留存 | 22 | dt | active_date, event_date, dt |
| `ads_market_device_ad_country_media_cost_revenue_retention_asa_da` | MI/ROI事实与预估 | 设备粒度 asa 渠道国家和广告维度消耗、收入、留存指标 | 52 | dt | install_date, dt |
| `ads_market_device_ad_country_media_cost_revenue_retention_da` | MI/ROI事实与预估 | 设备粒度国家和广告维度消耗、收入、留存指标 | 52 | dt | install_date, dt |
| `ads_market_device_country_media_cost_revenue_retention_da` | MI/ROI事实与预估 | 设备粒度国家和渠道维度消耗、收入、留存指标 | 39 | dt | install_date, dt |
| `ads_market_device_country_media_cost_revenue_retention_pre_roi_da` | MI/ROI事实与预估 | 设备粒度国家和渠道维度消耗、收入、留存、预估roi指标 | 50 | dt | install_date, dt |
| `ads_market_roi_pred_accuracy_da` | MI/ROI事实与预估 | 预估 ROI 与真实 ROI 对比快照，用于评估各时间节点模型预测精度 | 25 | dt | active_date, snapshot_date, dt |
| `ads_market_tj_ad_revenue_v2` | MI/ROI事实与预估 | MI看板-AF收入 | 27 | dt | active_date, revenue_date, dt |
| `ads_market_tj_ad_sdk_revenue_attributed_di` | MI/ROI事实与预估 | MI看板-数仓埋点收入 | 27 | dt | active_date, revenue_date, dt |
| `ads_market_tj_ad_spend_active_v2` | MI/ROI事实与预估 | MI看板-消耗+激活 | 33 | dt | active_date, dt |
| `dwd_market_roi_prediction_360_v6_da` | MI/ROI事实与预估 | v6模型BB sdk回收预估结果表 | 12 | dt | active_date, dt |
| `dwd_market_roi_prediction_sdk_360_da` | MI/ROI事实与预估 | xy_v6,xy_v5模型 sdk回收预估结果表 | 12 | dt | active_date, dt |

### P1

| 表 | 分类 | 表说明 | 字段数 | 分区 | 日期字段候选 |
|---|---|---|---:|---|---|
| `ads_market_material_metric_di` | 其他 | 广告消耗指标素材映射表 | 19 | dt | active_date, dt |
| `dim_market_material_unique_info_da` | 设备资产/用户资产 | 素材去重明细表 | 16 | dt | cost_date, created_at, updated_at, dt |
| `dwd_market_meta_audience_push_log_all_hi` | Meta CAPI/受众推送 |  | 11 | dt, audience_id | dt |
| `dwd_market_meta_audience_push_ready_all_di` | Meta CAPI/受众推送 |  | 6 | dt, audience_id, if_init | dt |
| `dwd_market_meta_capi_push_log_all_hi` | Meta CAPI/受众推送 | Meta CAPI S2S 推送结果明细日志表（事件粒度，外部表） | 11 | dt, hour | dt |
| `dwd_market_meta_capi_push_log_hi` | Meta CAPI/受众推送 | Meta CAPI S2S 推送结果明细日志表（事件粒度，外部表） | 11 | dt, hour | dt |
| `dwd_market_meta_capi_push_ready_all_hi` | Meta CAPI/受众推送 | Meta CAPI S2S 待推送事件数据准备表 | 25 | dt, hour | created_at, dt |
| `ods_market_api_ad_applovin_da` | 媒体API/Campaign素材元数据 | 通过applovin managerment api 的 creative set 接口拉取的全量 creative set | 14 | dt | created_at, dt |
| `ods_market_api_ad_facebook_da` | 媒体API/Campaign素材元数据 | 通过facebook ads api拉取的全量ad | 21 | dt | dt |
| `ods_market_api_ad_google_da` | 媒体API/Campaign素材元数据 | 通过google ads api拉取的ad | 17 | dt | dt |
| `ods_market_api_ad_tiktok_da` | 媒体API/Campaign素材元数据 | TikTok Ads 数据表（ODS 层）- 来自 TikTok Marketing API | 53 | dt | dt |
| `ods_market_api_ad_unity_da` | 媒体API/Campaign素材元数据 | 通过unity managerment api 的 creative pack 接口拉取的全量 creative pack | 13 | dt | dt |
| `ods_market_api_spend_di` | 媒体API/Campaign素材元数据 | 从媒体拉取的原始消耗数据 | 21 | dt, version | dt |
| `ods_market_applovin_campaign_da` | 媒体API/Campaign素材元数据 | applovin campaign元数据 | 17 | dt | created_at, updated_at, dt |
| `ods_market_google_campaign_da` | 媒体API/Campaign素材元数据 |  | 13 | dt | start_date, end_date, dt |
| `ods_market_meta_campaign_da` | 媒体API/Campaign素材元数据 |  | 28 | dt | dt |
| `ods_market_moloco_campaign_da` | 媒体API/Campaign素材元数据 | Moloco Ads Management API - Campaign 元数据（ODS层） | 25 | dt | created_at, updated_at, dt |
| `ods_market_tiktok_campaign_da` | 媒体API/Campaign素材元数据 | tiktok campaign元数据 | 21 | dt | dt |
| `ods_market_unity_campaign_da` | 媒体API/Campaign素材元数据 | Unity Ads Management API - Campaign 元数据（ODS层） | 18 | dt | created_at, updated_at, dt |

### P2

| 表 | 分类 | 表说明 | 字段数 | 分区 | 日期字段候选 |
|---|---|---|---:|---|---|
| `ads_market_device_dau_behavior_di` | 设备资产/用户资产 | 日活行为宽表，以活跃日期为主轴，支持日龄分桶和前向留存统计 | 42 | dt | activity_date, dt |
| `dim_kcolb_tsalb_all_device_da` | 设备资产/用户资产 | 方块 双端 设备天级全量表 | 18 | dt, app_name | install_date, first_active_date, last_active_date, dt |
| `dim_kcolb_tsalb_all_new_or_return_device_da` | 设备资产/用户资产 | 方块 双端 设备天级全量新设备和回流设备表 | 7 | dt, app_name | new_device_date, return_device_date, dt |
| `dim_kcolb_collection_all_device_da` | 设备资产/用户资产 | 方块小包设备天级全量标签表 | 19 | dt, app_name | install_date, first_active_date, last_active_date, dt |
| `dim_kcolb_collection_all_new_or_return_device_da` | 设备资产/用户资产 | 方块小包 双端 设备天级全量新设备和回流设备表 | 8 | dt, app_name | new_device_date, return_device_date, dt |
| `dim_market_appsflyer_attribution_by_device_id_da` | 设备资产/用户资产 | 设备id-AF归因表 每天一个快照 | 18 | dt | dt |
| `dim_nova_collection_all_device_da` | 设备资产/用户资产 | 星云设备天级全量标签表 | 19 | dt, app_name | install_date, first_active_date, last_active_date, dt |
| `dim_nova_collection_all_new_or_return_device_da` | 设备资产/用户资产 | 星云 双端 设备天级全量新设备和回流设备表 | 8 | dt, app_name | new_device_date, return_device_date, dt |
| `dwd_market_new_return_device_sdk_revenue_di` | 设备资产/用户资产 | 设备粒度SDK收入表(含AF归因) | 18 | dt | sdk_install_date, sdk_return_date, dt |
| `dws_kcolb_tsalb_all_device_id_active_retention_da` | 产品设备/用户聚合 |  | 128 | dt, app_name | anchor_date, activity_date, dt |
| `dws_kcolb_tsalb_all_device_install_retention_da_v2` | 产品设备/用户聚合 | 方块720 留存(按device_id重新归一) v2版本 | 31 | dt, app_name | install_date, active_date, dt |
| `dws_kcolb_tsalb_all_device_multi_dim_di` | 产品设备/用户聚合 | 方块 双端 设备天级事件聚合表 | 154 | dt, app_name | new_device_date, return_device_date, dt |
| `dws_kcolb_tsalb_all_user_multi_dim_hi` | 产品设备/用户聚合 | 方块 双端 用户天级事件聚合表 | 146 | dt, app_name | dt |
| `dws_kcolb_collection_all_device_id_active_retention_da` | 产品设备/用户聚合 | 方块小包多应用设备级活跃留存 | 53 | dt, app_name | anchor_date, activity_date, dt |
| `dws_kcolb_collection_all_device_install_retention_da_v2` | 产品设备/用户聚合 | 方块小包全量设备安装留存表V2版本 | 39 | dt, app_name | install_date, active_date, dt |
| `dws_kcolb_collection_all_device_multi_dim_di` | 产品设备/用户聚合 | 方块小包多应用设备级事件聚合 | 63 | dt, app_name | new_device_date, return_device_date, dt |
| `dws_nova_collection_all_device_id_active_retention_da` | 产品设备/用户聚合 | 星云双端多应用设备级活跃留存表 | 104 | dt, app_name | anchor_date, activity_date, dt |
| `dws_nova_collection_all_device_install_retention_da_v2` | 产品设备/用户聚合 | 星云全量设备安装留存表v2版本 | 41 | dt, app_name | install_date, active_date, dt |
| `dws_nova_collection_all_device_multi_dim_di` | 产品设备/用户聚合 | 星云双端多应用设备级事件聚合表 | 113 | dt, app_name | new_device_date, return_device_date, dt |
| `dws_nova_collection_all_user_multi_dim_hi` | 产品设备/用户聚合 |  | 116 | dt, app_name | dt |

### P3

| 表 | 分类 | 表说明 | 字段数 | 分区 | 日期字段候选 |
|---|---|---|---:|---|---|
| `ods_market_api_adset_facebook_da` | 媒体API/Campaign素材元数据 |  | 52 | dt | dt |
| `ods_market_api_creative_moloco_da` | 媒体API/Campaign素材元数据 | Moloco Creative 元数据（ODS层） | 27 | dt | created_at, updated_at, dt |

## P0 建议

优先补齐 MI/ROI 主链路和预估 ROI 表，这些与 `ai_ck` 的 ROI360 口径和 MI 页面字段最接近：

- `ads_market_af_cohort_user_acquisition_v2`：MI看板-AF留存
- `ads_market_device_ad_country_media_cost_revenue_retention_asa_da`：设备粒度 asa 渠道国家和广告维度消耗、收入、留存指标
- `ads_market_device_ad_country_media_cost_revenue_retention_da`：设备粒度国家和广告维度消耗、收入、留存指标
- `ads_market_device_country_media_cost_revenue_retention_da`：设备粒度国家和渠道维度消耗、收入、留存指标
- `ads_market_device_country_media_cost_revenue_retention_pre_roi_da`：设备粒度国家和渠道维度消耗、收入、留存、预估roi指标
- `ads_market_roi_pred_accuracy_da`：预估 ROI 与真实 ROI 对比快照，用于评估各时间节点模型预测精度
- `ads_market_tj_ad_revenue_v2`：MI看板-AF收入
- `ads_market_tj_ad_sdk_revenue_attributed_di`：MI看板-数仓埋点收入
- `ads_market_tj_ad_spend_active_v2`：MI看板-消耗+激活
- `dwd_market_roi_prediction_360_v6_da`：v6模型BB sdk回收预估结果表
- `dwd_market_roi_prediction_sdk_360_da`：xy_v6,xy_v5模型 sdk回收预估结果表

## 与现有 ai_ck 的关系

- `ads_market_tj_ad_spend_active_v2` 对应 CK `shucang_market.tj_ad_spend_active_v2`。
- `ads_market_tj_ad_sdk_revenue_attributed_di` 对应 CK SDK 回收链路。
- `ads_market_tj_ad_revenue_v2` 对应 CK AF 回收链路。
- `ads_market_af_cohort_user_acquisition_v2` 对应 CK `af_cohort_user_acquisition_v2` 留存链路。
- `ads_market_roi_pred_accuracy_da` 和 `dwd_market_roi_prediction_*` 可补足 forecast / ROI 预测准确性知识。

## 后续动作

1. 先为 P0 表生成 `ai_hive/agent_knowledge/tables/*.yaml` 表卡。
2. 更新 `ai_hive/agent_knowledge/catalog.yaml` 和 `ai_hive/export/RAG召回包.md`。
3. 将与 CK 同构的 ADS 表互链到 `ai_ck/agent_knowledge/tables/*.yaml`。
4. P1 再补媒体 API / campaign / 素材元数据表。
