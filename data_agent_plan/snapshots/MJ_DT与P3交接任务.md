# 交接任务：MJ/DT 历史点位复盘验证 + 缺表补齐 + P3 收尾

> 交接日期：2026-06-13  
> 执行模式：建议新会话按本文逐步执行。  
> 重要原则：不要直接跑全量 MJ/DT 历史点位复盘大 SQL；先拆小窗口验证。

## 背景

当前 Data Agent 语义底座已经完成：

- `ai_hive` 已覆盖 95 张 MaxCompute 表。
- 用户增长 Topic 的 P0/P1/P2 表卡已补齐。
- `ai_ck` 已覆盖 ClickHouse/MI ROI360 相关表和指标语义。
- DA 资产中已有第一批 verified SQL。
- `MJ/DT 历史点位复盘` 已作为原始材料和 SOP 入库：
  - `da_assets/raw/2026-06-13_MJ_DT历史点位复盘手工材料.md`
  - `da_assets/analysis_sop/MJ_DT历史点位复盘SOP.md`

但 MJ/DT 复盘 SQL 依赖的 `ods_appsflyer_block_collection_in_app_events_report_di` 目前只通过 MaxCompute 探查确认存在，尚未进入 `ai_hive` 正式表卡。

## 任务目标

本轮执行三件事：

1. 补 `ods_appsflyer_block_collection_in_app_events_report_di` 表卡。
2. 拆小验证 MJ/DT 历史点位复盘 SQL。
3. 补用户增长 Topic P3 两张低优先级表卡。

## 任务一：补 `ods_appsflyer_block_collection_in_app_events_report_di` 表卡

### 目标

把 DT / Block Collection AF ODS 表纳入 `ai_hive`，用于后续历史点位复盘。

### 已知信息

表名：

```text
hungry_studio.ods_appsflyer_block_collection_in_app_events_report_di
```

已通过 MaxCompute 查到：

- 表存在。
- 字段数：105。
- 分区：`dt`, `hour`。
- 结构与 `ods_appsflyer_all_in_app_events_report_di` / `ods_appsflyer_nova_collection_in_app_events_report_di` 类似。
- 关键字段包括：
  - `customer_user_id`
  - `bundle_id`
  - `app_id`
  - `media_source`
  - `campaign`
  - `af_c_id`
  - `af_adset`
  - `af_adset_id`
  - `af_ad`
  - `af_ad_id`
  - `event_name`
  - `event_time`
  - `install_time`
  - `appsflyer_id`
  - `event_revenue_usd`

### 执行步骤

1. 用 `maxcompute-dataworks` 或 PyODPS 只读拉 schema。
2. 新增表卡：

```text
ai_hive/agent_knowledge/tables/ods_appsflyer_block_collection_in_app_events_report_di.yaml
```

3. 表卡建议：
   - `documentation_status: complete`
   - `layer: ods`
   - `domain: [appsflyer, attribution, events, block_collection, dt]`
   - `partitions: dt, hour`
   - `query_rules.must_filter: [dt, hour]`
   - PII 列至少包含：`appsflyer_id`, `customer_user_id`, `idfa`, `advertising_id`, `ip`, `user_agent`
4. 更新：
   - `tools/scripts/rebuild_ai_hive_catalog.py`：给该表设置合适优先级，建议 `P2` 或 `P3`。如果本轮直接用于 MJ/DT 复盘，可先设 `P2`。
   - `ai_hive/agent_knowledge/catalog.yaml`
   - `ai_hive/export/RAG召回包.md`
   - `ai_hive/同步报告.md`

### 验收

- 表卡能被 YAML 解析。
- `catalog.yaml` 能看到该表。
- `RAG召回包.md` 已包含该表。
- 不保存任何用户级样例值。

## 任务二：MJ/DT 历史点位复盘 SQL 拆小验证

### 目标

不要直接执行完整大 SQL。先拆成 3 条小 SQL，验证链路可跑通：

1. 激活 cohort 小样本。
2. 事件渗透率。
3. 事件用户 ARPU / 留存。

### 推荐验证范围

先选一个产品、一个国家、一个短窗口：

```text
产品：DT Android
bundle_id: com.hungrystudio.mahjong
国家：US
安装日期窗口：2026-03-01 ~ 2026-03-03
行为观察截止：2026-03-10
```

如果 DT 数据量或字段不稳定，可改用：

```text
产品：MJ Android
bundle_id: com.nebula.mahjongtile
国家：US
安装日期窗口：2026-03-01 ~ 2026-03-03
```

### SQL 拆小验证

本节原候选 SQL 已被 `da_assets/verified_sql/vsql_20260613_mj_dt_historical_point_review_small_window.md` 取代；交接文档不再维护第二份可执行 SQL，避免与 verified 模板漂移。

已沉淀的 verified 模板覆盖 3 段链路：

1. 激活 cohort 小样本：验证 `dwd_market_appsflyer_activation_push_data_di` 能取到 cohort，验证去预装、国家、bundle、install_date 口径，只输出聚合。
2. 事件渗透率：验证 `ods_appsflyer_block_collection_in_app_events_report_di` 能与 cohort 对齐，输出 `event_users / cohort_users` 的 `penetration_rate`。
3. 事件用户 ARPU / 留存：验证事件触发用户能否 join 到行为聚合表，先算 D1 / D7 的收入和留存，不直接做完整 D30。

复用该模板时必须遵守分区护栏：

- `install_time_window` 是业务 cohort 窗口。
- `activation_dt_scan_window` 是激活表 `dt` 分区扫描窗口；历史小窗口至少 T+1，当前窗口必须扫到 `latest_partition`。
- `event_dt_window` 和 `behavior_dt_window` 是观察窗口，不能替代激活迟到分区扫描。
- 若未纳入 T+1 或 `latest_partition`，只能标 `partial_partition_scan`，不能作为完整 cohort 结论。

### 执行注意

- 如果 DT 表/字段不通，先换成 MJ Android：
  - AF 事件表：`ods_appsflyer_nova_collection_in_app_events_report_di`
  - 行为表：`dws_nova_collection_all_user_multi_dim_hi`
  - app_name：`nova_mahjong_gp`
  - bundle_id：`com.nebula.mahjongtile`
- 如果 SQL 仍然慢，继续缩到单日 `install_date='2026-03-01'`。
- 不要输出 `distinct_id`、`customer_user_id`、`appsflyer_id` 明细。

## 任务三：补 P3 两张低优先级表卡

P3 表：

```text
ods_market_api_adset_facebook_da
ods_market_api_creative_moloco_da
```

### 执行步骤

1. 从 `raw_exports/schema_probe_snapshots/user_growth_topic_schema_probe.json` 读取 schema。
2. 生成表卡：
   - `ai_hive/agent_knowledge/tables/ods_market_api_adset_facebook_da.yaml`
   - `ai_hive/agent_knowledge/tables/ods_market_api_creative_moloco_da.yaml`
3. 在 `tools/scripts/rebuild_ai_hive_catalog.py` 标为 `P3`。
4. 重建：
   - `ai_hive/agent_knowledge/catalog.yaml`
   - `ai_hive/export/RAG召回包.md`
5. 更新：
   - `ai_hive/用户增长Topic表知识.md`
   - `ai_hive/同步报告.md`

### 验收

- `ai_hive` 覆盖用户增长 Topic 55 张表全部完成。
- 表卡 YAML 可解析。
- `catalog.yaml` 和 `同步报告.md` 表数一致。

## 总体验收

完成后应有：

- `ods_appsflyer_block_collection_in_app_events_report_di` 表卡。
- 3 条 MJ/DT 小窗口验证 SQL，至少 2 条执行成功。
- P3 两张表卡。
- `ai_hive/agent_knowledge/catalog.yaml` / `RAG召回包.md` 更新。
- 不保存任何用户级明细或 PII。

## 完成后的下一步

如果小 SQL 跑通：

1. 将成功 SQL 写入 `da_assets/verified_sql/`。
2. 把 `MJ_DT历史点位复盘SOP.md` 从 `draft_sql_needed` 推进到 `copied_unverified` 或 `verified`。
3. 再考虑是否逐步扩大窗口到完整 2026-01-01 至 2026-03-31。
