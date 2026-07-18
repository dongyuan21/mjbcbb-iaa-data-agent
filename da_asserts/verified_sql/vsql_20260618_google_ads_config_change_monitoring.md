# Google Ads 配置变更监控

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260618_google_ads_config_change_monitoring` |
| 状态 | verified |
| 来源 | `../../ai_hive/agent_knowledge/tables/ods_market_google_ads_config_wide_hi.yaml` |
| 适用场景 | Google Ads campaign / ad_group / ad / criterion / budget 操作记录概览、campaign 级变更汇总、重点字段变更监控 |
| 数据源 | `h-s.ods_market_google_ads_config_wide_hi` |
| 最后验证 | 2026-06-18 |

## 原始问题

> 让 Agent 能稳定回答“某天/某小时 Google Ads 哪些配置或 campaign 被改了”，并默认召回已验证 SQL，而不是临时猜表或输出敏感明细。

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | `dt` 与 `hour` 为 MaxCompute 分区；查询必须同时过滤 `dt` 和 `hour`，可用 `hour BETWEEN '${hour_start}' AND '${hour_end}'` 做小时范围。 |
| 粒度 | change_event 行级宽表；`event_hash` 是单条 change_event 的去重键。 |
| 维度 | `customer_id`、`customer_short_name`、`campaign_id`、`campaign_name`、`change_event_change_resource_type`、`change_event_resource_change_operation`。 |
| 指标 | 变更行数、`event_hash` 去重数、涉及账户数、涉及 campaign/ad_group/ad 数、变更时间范围、重点字段命中数。 |
| 过滤 | 默认必须限制 `dt` 和 `hour`；不要无分区扫全表。 |
| 依赖表 | `h-s.ods_market_google_ads_config_wide_hi`。 |
| PII / 敏感边界 | 不输出 `change_event_user_email`、`change_event_old_resource`、`change_event_new_resource`；raw JSON 只可库内解析，不进 Agent 默认输出。 |
| 与语义层关系 | 当前作为 verified SQL 默认召回资产；语义层若新增 Google Ads 配置变更任务，可引用本资产和 `../../ai_hive/agent_knowledge/tables/ods_market_google_ads_config_wide_hi.yaml`。 |

## SQL

### 1. 小时操作类型分布

```sql
SELECT
  dt,
  hour,
  change_event_change_resource_type,
  change_event_resource_change_operation,
  COUNT(*) AS change_cnt,
  COUNT(DISTINCT event_hash) AS distinct_event_hash,
  COUNT(DISTINCT customer_id) AS customer_cnt,
  COUNT(DISTINCT campaign_id) AS campaign_cnt,
  MIN(change_event_change_date_time) AS min_change_time,
  MAX(change_event_change_date_time) AS max_change_time
FROM h-s.ods_market_google_ads_config_wide_hi
WHERE dt = '${dt}'
  AND hour BETWEEN '${hour_start}' AND '${hour_end}'
GROUP BY
  dt,
  hour,
  change_event_change_resource_type,
  change_event_resource_change_operation
ORDER BY change_cnt DESC
LIMIT 200;
```

### 2. Campaign 维度变更汇总

```sql
SELECT
  customer_id,
  customer_short_name,
  campaign_id,
  campaign_name,
  change_event_change_resource_type,
  change_event_resource_change_operation,
  COUNT(*) AS change_cnt,
  COUNT(DISTINCT ad_group_id) AS ad_group_cnt,
  COUNT(DISTINCT ad_id) AS ad_cnt,
  MIN(change_event_change_date_time) AS min_change_time,
  MAX(change_event_change_date_time) AS max_change_time
FROM h-s.ods_market_google_ads_config_wide_hi
WHERE dt = '${dt}'
  AND hour BETWEEN '${hour_start}' AND '${hour_end}'
  AND campaign_id IS NOT NULL
  AND campaign_id != ''
GROUP BY
  customer_id,
  customer_short_name,
  campaign_id,
  campaign_name,
  change_event_change_resource_type,
  change_event_resource_change_operation
ORDER BY change_cnt DESC
LIMIT 200;
```

### 3. 重点字段变更监控

```sql
SELECT
  change_event_change_resource_type,
  change_event_resource_change_operation,
  SUM(CASE WHEN INSTR(LOWER(COALESCE(change_event_changed_fields, '')), 'amountmicros') > 0 THEN 1 ELSE 0 END) AS budget_amount_change_cnt,
  SUM(CASE WHEN INSTR(LOWER(COALESCE(change_event_changed_fields, '')), 'status') > 0 THEN 1 ELSE 0 END) AS status_change_cnt,
  SUM(CASE WHEN INSTR(LOWER(COALESCE(change_event_changed_fields, '')), 'headline') > 0 THEN 1 ELSE 0 END) AS headline_change_cnt,
  SUM(CASE WHEN INSTR(LOWER(COALESCE(change_event_changed_fields, '')), 'description') > 0 THEN 1 ELSE 0 END) AS description_change_cnt,
  SUM(CASE WHEN change_event_change_summary IS NOT NULL AND change_event_change_summary != '' THEN 1 ELSE 0 END) AS summarized_change_cnt,
  COUNT(*) AS change_cnt
FROM h-s.ods_market_google_ads_config_wide_hi
WHERE dt = '${dt}'
  AND hour BETWEEN '${hour_start}' AND '${hour_end}'
GROUP BY
  change_event_change_resource_type,
  change_event_resource_change_operation
ORDER BY change_cnt DESC
LIMIT 200;
```

## 预期输出

- 小时操作类型分布：按 `dt × hour × change_resource_type × operation` 输出变更量、去重 event 数、涉及账户/campaign 数和变更时间范围。
- Campaign 维度变更汇总：按账户、campaign、变更对象类型、操作类型输出变更量，并聚合涉及 ad_group/ad 数。
- 重点字段变更监控：汇总预算金额、状态、标题、描述等重点字段是否在 `FieldMask` 中出现。

## 风险与陷阱

- 本表是 change_event 驱动，不是 Google Ads 当前全量配置快照；`COUNT(*)` 表示变更事件数，不表示对象总量。
- 生产宽表按 DataWorks 口径使用配置字段；Agent 直接按宽表字段查询即可，不额外要求 as-of 复盘。
- `campaign_name`、`ad_group_name`、`ad_type` 等补维字段可能为空，尤其是 `CAMPAIGN_CRITERION` 类变更；分析时以 resource type/operation 分组解释。
- 禁止输出 `change_event_user_email`、`change_event_old_resource`、`change_event_new_resource`；需要字段级排查时在库内解析聚合后再输出。
- 大窗口查询仍必须带 `dt` 和 `hour` 范围；不要无分区扫全表。

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-18 | Codex | verified | MaxCompute `SELECT 1` PASS；`dt=2026-06-18/hour=15` 三段 SQL 均已用外层聚合验证且不输出邮箱/raw JSON 明细：小时操作分布返回 10 行、`change_cnt=466`、`distinct_event_hash=466`；campaign 汇总返回 21 行、`change_cnt=331`；重点字段监控返回 10 行、`change_cnt=466`、预算字段命中 4、状态字段命中 30。目标表同小时已验证源/目标均 466 行，双向 `event_hash` anti-join 为 0，schema smoke 通过。 |
