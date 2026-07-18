# Verified SQL: 广告展示相关数据口径

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260613_ad_impression_metrics` |
| 状态 | verified |
| 来源 | 人工复制 SQL |
| 原始文件 | `../raw/2026-06-13_广告展示指标SQL手工材料.md` |
| 适用场景 | 广告展示、广告关闭、广告逃逸、广告点击、广告素材、广告主、广告收入明细抽取 |
| 负责人 |  |
| 最后验证 | 2026-06-13 |

## 原始问题

> 如何在 MaxCompute 里抽取皇室麻将、BB、BC 等产品的广告展示相关字段，包括广告逃逸、广告关闭、广告点击、广告素材 ID、广告主、广告域名、渠道、类型和收入。

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | 以 `dt` 分区过滤；部分 SQL 使用固定日期窗口，部分使用 `${dt}` 占位。 |
| 维度 | `dt`、`event_name`、`distinct_id`、`app_name` / `package_name`、广告渠道、广告类型、广告素材 ID、广告主、广告域名。 |
| 指标 | `escad_duration`、`revenue`、`s_ad_open_url_count`、`s_ad_storekit_count`、`s_ad_click_sum`、`s_ad_duration_sum`、`s_ad_enter_background_duration`、`s_ad_duration`、`s_ad_enter_background_count`、`adRevenue`。 |
| 过滤 | 广告关闭 `s_ad_close`、广告终止 `s_app_terminate_ad`、广告队列公共事件 `s_adq_common_event`；逃逸字段 `adescapetotal` 在来源中同时出现 `'true'` 和 `'1'` 两种写法。 |
| 依赖表 | `h-s.dwd_nova_collection_all_white_event_unique_data_hi`、`h-s.dwd_kcolb_tsalb_ios_white_event_unique_data_hi`、`h-s.dwd_kcolb_tsalb_gp_white_event_unique_data_hi`。 |
| 与语义层关系 | 可补入广告展示/变现漏斗字段口径；与 `da_assets/analysis_sop/20260423_LTV倍率下降归因SOP.md` 的 ARPDAU、曝光密度、广告收入拆解相关。 |

## SQL

### 1. 皇室麻将广告逃逸时长

用途：抽取 `nova_mahjong_ios` 在两个日期窗口内的广告终止逃逸事件，并计算扣除进入后台时长后的广告逃逸时长。

```sql
SELECT
  dt,
  event_name,
  properties,
  distinct_id,
  app_name AS app_name,
  CAST(GET_JSON_OBJECT(properties, '$.s_ad_duration_sum') AS DOUBLE)
    - CAST(GET_JSON_OBJECT(properties, '$.s_ad_enter_background_duration') AS DOUBLE) AS escad_duration,
  GET_JSON_OBJECT(properties, '$.s_ad_type') AS s_ad_type
FROM h-s.dwd_nova_collection_all_white_event_unique_data_hi
WHERE (
    (dt >= '2026-04-01' AND dt <= '2026-04-07')
    OR (dt >= '2026-01-01' AND dt <= '2026-01-07')
  )
  AND event_name = 's_app_terminate_ad'
  AND GET_JSON_OBJECT(properties, '$.adescapetotal') = 'true'
  AND app_name = 'nova_mahjong_ios';
```

### 2. BB iOS 广告关闭 / 逃逸事件基础抽取

用途：抽取 BB iOS 的 `s_ad_close` 和广告终止逃逸事件。

```sql
SELECT
  dt,
  event_name,
  properties,
  'kcolb_tsalb_ios' AS package_name,
  GET_JSON_OBJECT(properties, '$.adescapetotal') AS adescapetotal
FROM h-s.dwd_kcolb_tsalb_ios_white_event_unique_data_hi
WHERE dt = '${dt}'
  AND (
    event_name = 's_ad_close'
    OR (
      event_name = 's_app_terminate_ad'
      AND GET_JSON_OBJECT(properties, '$.adescapetotal') = '1'
    )
  );
```

### 3. iOS 广告展示明细字段抽取

用途：抽取广告收入、打开 URL / StoreKit / 点击 / 时长、广告主、广告域名、渠道、类型、素材 ID 等字段。

```sql
SELECT
  dt,
  CAST(GET_JSON_OBJECT(properties, '$.revenue') AS DOUBLE) AS revenue,
  CAST(GET_JSON_OBJECT(properties, '$.s_ad_open_url_count') AS INT) AS s_ad_open_url_count,
  CAST(GET_JSON_OBJECT(properties, '$.s_ad_storekit_count') AS INT) AS s_ad_storekit_count,
  CAST(GET_JSON_OBJECT(properties, '$.s_ad_click_sum') AS INT) AS s_ad_click_sum,
  CAST(GET_JSON_OBJECT(properties, '$.s_ad_duration_sum') AS DOUBLE) / 1000 AS s_ad_duration_sum,
  CAST(GET_JSON_OBJECT(properties, '$.s_ad_enter_background_duration') AS DOUBLE) / 1000 AS s_ad_enter_background_duration,
  CAST(GET_JSON_OBJECT(properties, '$.s_ad_duration') AS DOUBLE) / 1000 AS s_ad_duration,
  CAST(GET_JSON_OBJECT(properties, '$.s_ad_enter_background_count') AS DOUBLE) AS s_ad_enter_background_count,
  CASE
    WHEN GET_JSON_OBJECT(properties, '$.s_ad_data_js') IS NOT NULL
      AND GET_JSON_OBJECT(properties, '$.s_ad_data_js') != ''
    THEN GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_ad_data_js'), '$.ad_appStore_identifier')
  END AS ad_appStore_identifier1,
  CASE
    WHEN GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk') IS NOT NULL
      AND GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk') != ''
    THEN GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk'), '$.itunes_id')
  END AS ad_appStore_identifier2,
  CASE
    WHEN GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk') IS NOT NULL
      AND GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk') != ''
    THEN GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk'), '$.bidBundle')
  END AS ad_appStore_identifier3,
  CASE
    WHEN GET_JSON_OBJECT(properties, '$.s_ad_data_js') IS NOT NULL
      AND GET_JSON_OBJECT(properties, '$.s_ad_data_js') != ''
    THEN
      CASE
        WHEN GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_ad_data_js'), '$.open_redirectUrl') IS NOT NULL
          AND GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_ad_data_js'), '$.open_redirectUrl') != ''
        THEN PARSE_URL(GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_ad_data_js'), '$.open_redirectUrl'), 'HOST')
        ELSE GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_ad_data_js'), '$.adomain')
      END
  END AS adomain,
  CASE
    WHEN GET_JSON_OBJECT(properties, '$.s_ad_data_js') IS NOT NULL
      AND GET_JSON_OBJECT(properties, '$.s_ad_data_js') != ''
    THEN GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_ad_data_js'), '$.app_Name')
  END AS app_Names,
  CASE
    WHEN GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk') IS NOT NULL
      AND GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk') != ''
    THEN
      CASE
        WHEN GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk'), '$.click_url') IS NOT NULL
          AND GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk'), '$.click_url') != ''
        THEN PARSE_URL(GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk'), '$.click_url'), 'HOST')
        ELSE GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk'), '$.ad_domain')
      END
  END AS ad_domain,
  event_name,
  GET_JSON_OBJECT(properties, '$.s_ad_source') AS s_ad_source,
  GET_JSON_OBJECT(properties, '$.s_ad_type') AS s_ad_type,
  CASE
    WHEN GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk') IS NOT NULL
      AND GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk') != ''
    THEN GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_ad_data_json_4_safedk'), '$.ad_format_type')
  END AS ad_format_type,
  CASE
    WHEN GET_JSON_OBJECT(properties, '$.s_ad_create_id') IS NOT NULL
      AND GET_JSON_OBJECT(properties, '$.s_ad_create_id') != ''
    THEN GET_JSON_OBJECT(properties, '$.s_ad_create_id')
  END AS s_ad_create_id
FROM (
  SELECT
    dt,
    event_name,
    properties,
    app_name AS package_name,
    GET_JSON_OBJECT(properties, '$.adescapetotal') AS adescapetotal,
    distinct_id
  FROM h-s.dwd_nova_collection_all_white_event_unique_data_hi
  WHERE dt = '${dt}'
    AND (
      event_name = 's_ad_close'
      OR (
        event_name = 's_app_terminate_ad'
        AND GET_JSON_OBJECT(properties, '$.adescapetotal') = '1'
      )
    )
    AND app_name = 'block_crush_ios'
) AS tmp;
```

### 4. BC 广告队列公共事件

用途：从 BC 的广告队列公共事件中抽取广告 ID、App ID、包名、广告域名、广告主、素材 ID、收入、渠道、类型。

```sql
SELECT
  dt,
  event_name,
  distinct_id,
  GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_adq_key_common_content'), '$.s_ad_id') AS s_ad_id,
  NULLIF(GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_adq_key_common_more_info'), '$.appId'), '') AS appId,
  NULLIF(GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_adq_key_common_more_info'), '$.packageName'), '') AS packageName,
  NULLIF(GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_adq_key_common_more_info'), '$.adDomain'), '') AS adDomain,
  NULLIF(GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_adq_key_common_more_info'), '$.advertisedContent'), '') AS advertisedContent,
  COALESCE(GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_adq_key_common_content'), '$.adCreateId'), '') AS s_ad_create_id,
  CAST(GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_adq_key_common_content'), '$.adRevenue') AS FLOAT) AS adRevenue,
  COALESCE(GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_adq_key_common_content'), '$.s_adq_network_name'), '') AS s_ad_source,
  COALESCE(GET_JSON_OBJECT(GET_JSON_OBJECT(properties, '$.s_adq_key_common_content'), '$.s_adq_ad_type'), '') AS s_ad_type
FROM (
  SELECT
    event_name,
    properties,
    distinct_id,
    app_name,
    dt
  FROM h-s.dwd_nova_collection_all_white_event_unique_data_hi
  WHERE dt = '2026-04-07'
    AND app_name IN ('', 'block_crush_gp')
    AND event_name = 's_adq_common_event'
) AS tmp;
```

## 预期输出

输出粒度为事件明细级，通常包含 `dt`、事件、用户匿名 ID、包体、广告字段和收入字段。后续做分析时应先聚合到日期、产品、渠道、广告类型、素材或广告主维度，避免直接保存或传播用户级明细。

## 风险与陷阱

- 4 段完整 SQL 已完成小样本语法和字段验证；BB GP 只有表名，当前仅完成表级 smoke test。
- `distinct_id` 是用户级 ID，结果输出不应进入长期 agent 知识库，只能保留聚合摘要。
- `adescapetotal` 在不同产品中可能有 `'true'` 和 `'1'` 两种取值，需按表实查确认。
- `s_ad_duration_sum` 等字段在部分 SQL 中除以 1000 转成秒，皇室麻将 `escad_duration` 未除以 1000，单位需复核。
- BB GP 只有表名，缺少字段映射和事件过滤。
- `kcolb_tsalb_ios` 与 `block_crush_ios` 同段出现，需复核是否为包体命名或复制错误。

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-13 | AI | verified | 使用 MaxCompute helper 执行带分区和 `LIMIT 5` 的小样本验证；未保存用户级明细输出。 |

### 2026-06-13 验证明细

| 验证项 | 结果 | 说明 |
|---|---|---|
| 皇室麻将广告逃逸时长 | pass | `return_code=0`，返回 5 行；`escad_duration` 和 `s_ad_type` 可解析。 |
| BB iOS 广告关闭 / 逃逸事件基础抽取 | pass | `return_code=0`，返回 5 行；`s_ad_close` 数据可查。 |
| iOS 广告展示明细字段抽取 | pass | `return_code=0`，返回 5 行；`revenue`、时长、`s_ad_source`、`s_ad_type`、`ad_format_type`、素材 ID 可解析。 |
| BC 广告队列公共事件 | pass | `return_code=0`，返回 5 行；`s_adq_key_common_content` / `s_adq_key_common_more_info` 嵌套字段可解析。 |
| BB GP 表级 smoke test | table_smoke_only | `return_code=0`，`h-s.dwd_kcolb_tsalb_gp_white_event_unique_data_hi` 在 `dt='2026-04-07'` 可查；来源只给表名，未形成完整 SQL。 |

