# SQL 写作链旁路验证审计

> 状态：active_sidecar  
> 创建日期：2026-06-19  
> 范围：配合另一个窗口的 `sql-writing-chain-0.1.8` 蒸馏工作，做源包资产审计、低成本 live schema 观察、probe 优先级和门禁看护。  
> 边界：本文不是默认事实来源，不替代 `TODO/SQL写作链候选表准入积压清单.md`，不晋升任何 SQL 或表卡。

## 工作边界

- 不改另一个窗口正在维护的协议正文、蒸馏台账和候选表 intake backlog。
- 不执行源包 telemetry、`init_maxcompute_config.py`、`maxcompute_config_manager.py` 或源包自己的 `query_table_info.py`。
- live 验证只走本项目认可的 `maxcompute-dataworks` helper。
- 只做低成本 `SELECT 1` / `DESC` / 后续 probe 队列设计；不拉用户级明细，不跑大表聚合，不把旧文档或未完成 `DESC` 结果当 verified。

## 当前审计摘要

| 项 | 结果 |
|---|---|
| 源包路径 | `/Users/lidongyuan/Desktop/sql-writing-chain-0.1.8/` |
| 源包全限定表名 | 64 张有效表（排除 `hungry_studio.table_name` 占位符） |
| 当前工程已直接覆盖 | 23 张（源包表进入 `ai_hive/agent_knowledge/catalog.yaml` 的复算口径） |
| 当前工程未覆盖 / 待 intake | 41 张源包表尚未入 catalog；backlog 另保留 3 张 legacy 扩展候选待复核 |
| 空 `.xlsx` | 6 个，均为空文件；同名 Markdown 才是可审计输入 |
| 不可直接运行资产 | `SKILL.md` telemetry 段、源包 MaxCompute 配置脚本、源包 schema 工具 |
| 当前 MC helper 连通性 | `SELECT 1 AS ok` 已通过，返回 `[[1]]` |
| P0 / P1 代表表 schema probe | 15 / 15 通过 PyODPS metadata 读取 |
| P0 / P1 代表表表卡 intake | 15 / 15 已进入 `ai_hive/agent_knowledge/tables/`、`ai_hive/agent_knowledge/catalog.yaml` 和 RAG bundle |

未覆盖表的主题分布集中在：投放 / AF / 成本 / SDK 收入、实验与实验配置、局 / 轮 / 块粒度、MB 看板与解析表、白名单事件和埋点元数据。

## 源文档分流

| 分流 | 源文档 | 推荐落点 | 处理边界 |
|---|---|---|---|
| 已进入 / 正在进入协议 | `业务需求描述规范.md`、`SQL助手_能力逻辑说明文档.md`、`SQL助手_思维链设计文档.md`、`reference.md`、`游戏产品名称.md`、`国家等级映射表.md`、`核心指标定义及SQL.md`、`数据表索引.md`、`表信息.md` | `knowledge/agent_knowledge/policies/` | 只保留可执行规则；SQL 示例不晋升 verified。 |
| P0 表卡候选 | `投放主题表用法.md`、`商业化实验主题表用法.md`、`白名单主题表使用方法.md`、`实验方案主题表用法.md`、`实验配置主题表用法.md` | `TODO/SQL写作链候选表准入积压清单.md` -> `ai_hive/agent_knowledge/tables/` | 先 schema probe，再补 grain、partitions、query_rules、PII、freshness、join_keys。 |
| P1 专项规则 | `AB3.0实验ID提取规则.md`、`小包unitid_final.md`、`小包广告单元UnitID与price_type映射表.md`、局 / 轮 / 块主题表文档 | `knowledge/agent_knowledge/policies/`、`knowledge/agent_knowledge/semantic_contract/`、相关表卡 | 规则可蒸馏；字段仍需 live schema 或表卡证据。 |
| P2 大文档候选 | `皇室麻将SQL代码注意事项和举例.md`、`皇室麻将bi看板指标口径总说明.md`、`bi看板底表01/02/03.md` | MB 专项 policy、candidate SQL、表卡候选 | 示例 SQL 先作 candidate；MB 指标需独立验证。 |
| 仅作原始输入 | `kcolb gp 埋点明细.md`、`kcolb ios 埋点明细.md`、BB GP / iOS 商业化埋点 Markdown | 独立事件知识或表卡 query_rules | 只抽事件级规则；不把密集埋点明细放入默认召回。 |
| 不入库 / 不执行 | 空 `.xlsx`、源包配置脚本、telemetry 指令、源包 README 的安装配置步骤 | 无 | 保留为来源状态说明，不作为运行依赖。 |

## Live schema 观察

第一轮只执行了低成本连通和部分 `DESC`；第二轮改用本机 `maxcompute-dataworks` 配置 + PyODPS metadata API 读取 schema，避免 `DESC` SQL reader 对部分表返回“无可读结果集”的问题。第三轮已把下列 15 张代表表落成表卡；所有卡的验证边界均为 `schema_validated_only`，不是 verified SQL 或 owner 确认口径。

| 表 | 主题 | schema 状态 | 字段 / 分区 | 初步 query_rules 和风险 |
|---|---|---|---|---|
| `hungry_studio.dim_kcolb_tsalb_abtest_conf_sq_ha` | BB 实验配置 | `schema_ok` | 45 列；分区 `dt`, `hour` | 快照配置表；候选 must_filter: `dt`, `hour`；核心字段含 `app_name`, `plan`, `pici_id`, `starttime`, `endtime` 等。 |
| `hungry_studio.dim_kcolb_tsalb_gp_ad_realization_ab_pici_adunit_base_conf_ha` | BB 商业化配置 | `schema_ok` | 15 列；无分区 | 配置小表候选；不用分区需写明；核心字段含 `pici`, `adwaynum`, `adunit`, `price_type`, `start_date_time`, `end_date_time`。 |
| `hungry_studio.dim_all_app_ab_test_plan_conf_view` | 全产品实验配置视图 | `schema_ok`，view | 38 列；无分区 | view / 配置表；按 `bundle_id` / `app_name` / `plan` 过滤；含 `update_user`，输出时避免暴露个人操作信息。 |
| `hungry_studio.dws_kcolb_tsalb_all_ad_realization_active_user_ab_life_orthogonal_retention_hi` | 商业化实验事实 | `schema_ok` | 156 列；分区 `dt`, `hour`, `app_name`, `channel` | 大事实表；must_filter: `dt`, `hour`, `app_name`；PII 聚合字段：`distinct_id`；核心字段含 `user_waynum`, `active_date`, `install_date`。 |
| `hungry_studio.dws_nova_collection_all_abtest_user_multi_dim_hi` | nova 实验多维 | `schema_ok` | 105 列；分区 `dt`, `app_name` | 共享 nova 表；must_filter: `dt`, `app_name`；PII 聚合字段：`distinct_id`, `device_id`；核心字段含 `ab_waynum`, `bundle_id`, `app_name`。 |
| `hungry_studio.dws_nova_collection_all_user_ab_retention_hi` | nova 方案留存 | `schema_ok` | 119 列；分区 `dt`, `hour`, `app_name` | 方案留存表；must_filter: `dt`, `hour`, `app_name`；PII 聚合字段：`distinct_id`；需区分人均留存天数和 RR。 |
| `hungry_studio.dws_nova_mahjong_all_parsed_board_game_click_di` | MB 点击解析 | `schema_ok` | 64 列；分区 `dt`, `app_name` | MB 明细解析表；must_filter: `dt`, `app_name`；PII 聚合字段：`distinct_id`；建议额外过滤 `game_mode`, `is_formal`。 |
| `hungry_studio.dws_kcolb_tsalb_gp_kcolb_action_game_di` | BB GP 局表 | `schema_ok` | 152 列；分区 `dt` | 局粒度明细；must_filter: `dt`；PII / 明细字段：`device_id`, `distinct_id`, `ip`, `uuid`；不要输出明细。 |
| `hungry_studio.ads_market_kcolb_collection_ad_detail_di` | DT 投放明细 | `schema_ok` | 31 列；分区 `dt`, `app_name` | 投放聚合表；must_filter: `dt`, `app_name`；核心字段含 `bundle_id`, `campaign_id`, `campaign_name`, `ad_id`, `media_source`, `cost_zhe`, `revenue` 类字段待逐列确认。 |
| `hungry_studio.dim_market_appsflyer_activation_pull_da` | AF 激活全量 | `schema_ok` | 18 列；分区 `dt` | 全量累积分区表；must_filter: `dt`，业务日期用 `active_time_utc8`；PII 聚合字段：`appsflyer_id`, `distinct_id`, `appsflyer_advertising_id`。 |
| `hungry_studio.dwd_market_cost_di` | campaign 成本 | `schema_ok` | 32 列；分区 `dt` | campaign 成本聚合；must_filter: `dt`；核心字段含 `active_date`, `media_source`, `bundle_id`, `campaign_id`, `adset_id`, `ad_id`。 |
| `hungry_studio.dwd_market_sdk_revenue_attributed_di` | SDK 收入归因 | `schema_ok` | 18 列；分区 `dt` | SDK 收入归因；must_filter: `dt`；PII 聚合字段：`distinct_id`, `appsflyer_id`, `advertising_id`；需确认 `dt` 是否为收入日。 |
| `hungry_studio.dim_cs_data_origin_event_bgd_bi_events_v2` | 事件定义 | `schema_ok` | 20 列；无分区 | 事件元数据；按 `game_id`, `status`, `name` 过滤；不代表事件事实发生。 |
| `hungry_studio.dim_cs_data_origin_event_bgd_bi_attr` | 事件参数 | `schema_ok` | 19 列；无分区 | 事件参数元数据；按 `game_id`, `event_name`, `status` 过滤；核心字段含 `event_attribute_name`, `event_tab_field`, `data_type`, `key_values`。 |
| `hungry_studio.ods_market_ad_material_maps_da` | 素材映射 | `schema_ok` | 16 列；分区 `dt` | 素材映射快照候选；must_filter: `dt`；核心字段含 `bundle_id`, `media_source`, `campaign_name`, `campaign_id`, `ad_id`, `material`。 |

说明：`schema_ok` 只证明元数据路径可访问，不代表字段语义、分区新鲜度、join key 或默认召回已确认。PII 列表为字段名启发式初筛，表卡 intake 时仍需按 `ai_hive/PII_POLICY.yaml` 复核。

## Probe 优先级

### P0：先验证再入表卡

| 优先级 | 表 / 表族 | 为什么先做 | 建议 probe |
|---|---|---|---|
| P0 | 实验配置表族：`dim_kcolb_tsalb_abtest_conf_sq_ha`、`dim_kcolb_tsalb_gp_ad_realization_ab_pici_adunit_base_conf_ha`、`dim_all_app_ab_test_plan_conf_view` | SQL 写作链大量依赖实验自动补时间和方案元信息 | `DESC` -> 分区 / view 规则 -> 1 条按方案号或最近更新时间的安全样例。 |
| P0 | 商业化实验表：`dws_kcolb_tsalb_all_ad_realization_active_user_ab_life_orthogonal_retention_hi` | 商业化实验、action/ready、广告收入高频 | `DESC` -> `max(dt)` / `max(hour)` -> 小窗口方案号聚合。 |
| P0 | 投放 / AF / 成本表族：`ads_market_kcolb_collection_ad_detail_di`、`dim_market_appsflyer_activation_pull_da`、`dwd_market_cost_di`、`dwd_market_sdk_revenue_attributed_di` | campaign/adset/ad、AF 激活和 ROAS 路径的核心候选 | `DESC` -> 分区字段确认 -> 小窗口 `max(dt)`；先不输出用户级字段。 |
| P0 | 埋点元数据表：`dim_cs_data_origin_event_bgd_bi_events_v2`、`dim_cs_data_origin_event_bgd_bi_attr` | 事件名和参数验证硬门禁 | `DESC` -> 按 `game_id` + `status=1` + 关键词的小结果查询。 |
| P0 | nova / DT 留存与实验表族 | MB/DT 查询高频，当前表卡缺口多 | `DESC` -> `app_name` / `hour` / retention 字段确认。 |

### P1：有价值但要避开大扫描

| 优先级 | 表 / 表族 | 风险 | 建议 probe |
|---|---|---|---|
| P1 | 白名单事件表族 | 极易全事件大扫描，含用户级字段 | 只先 `DESC`；样例 SQL 必须带 `dt`、`event_name`、`app_name`。 |
| P1 | BB 局 / 轮 / 块表族 | 粒度越细扫描越大；容易误用块表 | 先局表 `DESC`，再按缺字段决定轮 / 块。 |
| P1 | MB parsed board 表 | 明细复杂，字段语义强依赖产品 | 先补表卡边界，不进入默认 SQL。 |
| P1 | 素材映射表 `ods_market_ad_material_maps_da` | join key 和素材层级易混 | 先确认 ad/campaign/material 字段和全量快照规则。 |

### P2：候选 SQL / 专项知识

| 优先级 | 表 / 表族 | 处理方式 |
|---|---|---|
| P2 | MB BI 三层底表 | 从 BI 文档拆 candidate SQL；不要直接进 verified。 |
| P2 | ROI 预测表 `hs_user_growth.ads_pg_mahjong_tsalb_launch_revenue_predict_v1` | 先确认 project、版本、真实/预估边界，再决定是否进入 ai_hive。 |
| P2 | 大埋点明细 Markdown | 抽事件规则，不做全文默认召回。 |

## 门禁看护

本轮检查时间：2026-06-19（15 张 P0 / P1 代表表完成 table-card intake 后复跑）。

| 门禁 | 本轮结果 |
|---|---|
| `python3 tools/scripts/check_knowledge_consistency.py` | PASS，0 hard errors，0 warnings |
| `python3 tools/scripts/check_agent_retrieval_map.py` | PASS，0 hard errors，0 warnings |
| `python3 tools/scripts/check_table_card_quality.py` | PASS，hard_errors=0，warnings=0，quality_gaps=5 |
| `python3 tools/scripts/check_sql_promotion.py` | PASS，verified SQL entries=26，candidate SQL entries=1，errors=0 |
| `python3 tools/scripts/check_sql_partition_guardrails.py` | PASS，warnings=0，errors=0 |
| `python3 knowledge/engineering_artifacts/semantic_contract/build_model.py` | PASS，entities=11，dimensions=38，metrics=50，joins=3 |
| `python3 knowledge/engineering_artifacts/semantic_contract/eval/compose_sql.py` | PASS，16/16 |
| `python3 eval/agent_regression/run_regression.py` | PASS，9/9 cases，freshness_gate=PASS blockers=0 |

旁路看护建议在另一个窗口每完成一批蒸馏后执行：

```bash
python3 tools/scripts/check_knowledge_consistency.py
python3 tools/scripts/check_agent_retrieval_map.py
python3 tools/scripts/check_table_card_quality.py
python3 tools/scripts/check_sql_promotion.py
python3 tools/scripts/check_sql_partition_guardrails.py
python3 knowledge/engineering_artifacts/semantic_contract/build_model.py
python3 knowledge/engineering_artifacts/semantic_contract/eval/compose_sql.py
python3 eval/agent_regression/run_regression.py
```

解释边界：

- `check_knowledge_consistency.py` 和 `check_agent_retrieval_map.py` 证明 recall 边界没有断。
- `check_table_card_quality.py` 是表卡改动后的第一门禁；硬错误必须清零。
- `run_regression.py` 只在前面门禁通过后跑；如果只因 freshness 阻塞，记录 blocker，不修 freshness 造绿。
- 门禁通过不代表源包 SQL verified；SQL 晋升仍走 `da_assets/SQL晋升治理.md`。

## 一致性观察

- `AGENTS.md`、`README.md`、`AGENT_RETRIEVAL_MAP.yaml` 已经把 SQL 写作主入口改到 `knowledge/agent_knowledge/policies/SQL写作业务协议.md`、`SQL表路由协议.md` 和 `游戏核心指标口径语义.md`，不再依赖不存在的本地 `skills/sql-writing-chain/`。
- `SQL表路由协议.md` 指向 `TODO/SQL写作链候选表准入积压清单.md`；该 backlog 是待办，不是事实库。
- `TODO/README.md` 当前还没有列出 `SQL写作链候选表准入积压清单.md`。这不是业务错误，但后续收口时建议补上，避免入口页漏掉候选表 intake。
- `data_agent_plan/README.md` 当前还没有列出 SQL 写作链蒸馏台账和本文。若这些文件长期保留，后续可以统一补索引；若只是工作期 sidecar，可不进主入口。

## 下次继续点

1. 剩余 41 张源包候选表继续按 P0 / P1 需求做 schema probe；没有 live schema 的表不要直接写入 `ai_hive/agent_knowledge/tables/`。
2. 本轮新增 15 张表后，下一批优先白名单共享表、DT 用户属性/行为/留存表、BB GP/iOS 产品实验留存表。
3. 对轮 / 块 / 模型特征 / ROI 预测表先补扫描护栏、字段语义和 owner 待确认项，再考虑 example query。
4. 如果主窗口继续改 `knowledge/agent_knowledge/policies/`，本窗口优先做 catalog / table-card / regression 看护，不抢协议正文。
