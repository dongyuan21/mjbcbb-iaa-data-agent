# 数据底座维护 Harness

状态：`validated_ck_hive_sql_knowledge_semantic_once`

本文是全局数据底座维护 harness 的待办草案，暂不迁入 `tools/runbooks/`。当前 `ai_ck/` 与 `ai_hive/` 都已有 adapter 分层和维护流程，并已用一次低风险 Hive 表卡变更、一次 CK schema drift、一次 candidate SQL live revalidation、一次 verified SQL 正向晋升、一次 knowledge 默认召回正向变更、一次业务语义 / semantic governance 变更验证分流、live probe、freshness、schema 基线和回归链路；后续还需要用会改变 Hive / CK 深卡、join、默认选表或 PII 边界的真实变更验证后，再考虑迁入正式 runbook。

## 目标

把 `ai_ck`、`ai_hive`、`semantic_contract`、`knowledge`、`da_assets`、`eval` 的维护关系收成一套统一流程：

- 变更来了先判断影响范围。
- 脚本负责结构检查、连通、新鲜度、回归。
- Agent 负责把证据整理成可召回知识。
- 人只拍板业务阈值、官方口径、canonical、join 证据不足等高风险事项。

## 当前状态

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| `ai_ck/` | `adapter_ready` | 已有 `README.md` 三层分工、`agent_manifest.yaml` asset layers、`CK维护流程.md` |
| `ai_hive/` | `adapter_ready` | 已有 `README.md` 三层分工、`agent_manifest.yaml` asset layers、`Hive维护流程.md` |
| `knowledge/agent_knowledge/semantic_contract/` | `partial_ready` | 已有 build / compose 回归，但全局维护触发条件还需和表卡层对齐 |
| `knowledge/` | `validated_default_recall_once` | 已有 manifest、一致性门禁和一次低风险默认召回正向晋升验证 |
| `da_assets/` | `partial_ready` | verified SQL / SOP / case 已有边界，需和底层表卡更新联动 |
| `eval/` | `ready_as_gate` | 已有多个门禁和回归入口，可作为 harness 验收层 |

## 先不迁入 runbook 的原因

- CK / Hive adapter 已就绪，低风险 Hive 表卡 freshness 变更、一次 CK schema drift、一次 candidate SQL live revalidation、一次 verified SQL 正向晋升、一次 knowledge 默认召回正向晋升和一次 semantic governance 变更已验证通过；但会改变 Hive / CK 默认选表、join 或 PII 边界的深卡变更还没经过真实变更验证。
- Hive 的准入、PII、catalog 和 freshness 比 CK 更接近事实源；全局 harness 需要保留更保守的 Hive 边界。
- 全局 harness 一旦放进 `tools/runbooks/`，会被理解成当前正式流程；现在先保留为待办设计。

## 待补内容

### P0：用真实变更验证全局分流

前置已完成：

- `ai_hive/README.md` 分层重写。
- `ai_hive/Hive维护流程.md` 已新增。
- `ai_hive/agent_manifest.yaml` 已增加 `asset_layers` 和维护读取顺序。
- `2026-06-20` 低风险真实变更已通过：给 `ai_hive/agent_knowledge/tables/dim_market_campaign_s2s_event_map_da.yaml` 补 `freshness`，live probe MC / CK 同名映射表，刷新 `ai_hive` / `ai_ck` freshness snapshot，跑表卡、检索、语义模型和 Agent 回归。

本次已验证：

- 改 Hive 表卡会被 `maintain_data_base.py` 分流为 `NEEDS_AGENT`。
- MC / CK 读取能力可验证：两边 `dim_market_campaign_s2s_event_map_da` 的 `max(last_dt)` 均可读到 `2026-06-20`。
- Hive freshness 覆盖从 23 张扩到 24 张，新增映射表状态为 `dim_snapshot`。
- `check_table_card_quality.py`、`check_agent_retrieval_map.py`、`knowledge/engineering_artifacts/semantic_contract/build_model.py`、`knowledge/engineering_artifacts/semantic_contract/eval/compose_sql.py`、`eval/agent_regression/run_regression.py` 均通过。
- 顺手刷新 CK 产物时发现真实 schema drift，并留到 CK drift 场景单独处理。
- `2026-06-20` CK schema drift 已处理：live CK probe 证实当前需要同步的是 `assets_mysql_snapshot_prod`、`assets_mysql_snapshot_prod_local` 新增 `source`；早先记录的 `market_api_asset_spend_v1_local.spend_usd` 删除在当前 live schema 中不成立，因此未删除。
- CK drift 影响审计结论：本次只影响 CK schema baseline 和 profile；未发现 `ai_ck/agent_knowledge/tables/*.yaml` 深卡、`semantic_contract`、`da_assets/verified_sql` 或 Hive 运行时表卡依赖 `source` / `spend_usd` 的变更。
- `probe_ck_schema.py` 已新增机器可读 `ai_ck/engineering_artifacts/schema_exports/schema_drift.json`，`maintain_data_base.py` 会读取其 `NO_IMPACT` / `CHECK_ONLY` / `NEEDS_AGENT` / `BLOCKED` 状态辅助自动分流。
- `run_data_agent_healthcheck.py` 已用完整 MC / CK live probe、双源 freshness 和 Agent 回归验证通过；MaxCompute freshness 使用固定 `project/quota`，并把健康检查超时上限调到适配 24 张 Hive 表的完整刷新。
- `2026-06-20` verified SQL 正向晋升已处理：用户确认 `dim_market_new_return_device_attribution_da` 的 `device_id × dt` 非严格唯一是正常多行形态后，沉淀 `da_assets/verified_sql/vsql_20260620_new_return_device_attribution_aggregation.md`；只保留安全聚合 Step 2 / Step 4 / Step 5，最新分区为 `2026-06-20`，`total_rows=1,969,146,324`、`distinct_devices=1,965,752,398`，设备级样例和 `distinct_id` 展开样例没有进入默认召回。
- knowledge 默认召回负向验证已纳入 `check_knowledge_consistency.py` 报告：显式统计 default recall 允许项、never-default 状态项、`draft_knowledge/` 排除项和 snapshot 排除项；该负向门禁继续用于防止 draft / snapshot 漏入默认召回。
- `2026-06-20` knowledge 默认召回正向晋升已处理：用户确认采用低风险治理规则验证正向通道后，新增 `knowledge/agent_knowledge/policies/默认召回边界与晋升规则.md`，登记为 `default_recall=true`，并补 `K7` 回归用例；该规则只约束默认召回和晋升边界，不新增业务口径、join、指标或默认选表。
- `2026-06-20` semantic governance 真实变更已处理：用 Day0 ARPU / ROI 治理动作边界变更验证 `knowledge/agent_knowledge/policies/投放ROI治理政策.md`、`knowledge/agent_knowledge/semantic_contract/governance.yaml`、`knowledge/agent_knowledge/semantic_contract/model.json`、`da_assets/analysis_sop/20260620_Day0_ARPU_MI查询输出模板.md` 与 `tools/scripts/query_mi_roi360.py` 的联动；新增 `R10` 回归用例，确认 MI 快速预检与完整 DA 归因 SQL 分层、`<300 USD` 观察边界、头部 campaign / 素材 ROI 动作人审边界都能被 harness 捕获。

仍需用更高风险真实变更验证：

- 会改变深卡、join、默认选表或 PII 边界的 CK / Hive 变更是否影响 Hive 同源表、CK 表卡或语义层。
- 业务语义类新知识进入 `knowledge/agent_knowledge/catalog.yaml` 默认召回时，是否会触发 semantic / verified SQL / 表卡联动。

### P1：定义全局变更分流

统一状态：

| 状态 | 含义 |
| --- | --- |
| `NO_IMPACT` | 变更不影响默认召回、口径、join、当前可用性 |
| `CHECK_ONLY` | 只需要脚本刷新或门禁验证 |
| `NEEDS_AGENT` | 需要 Agent 更新表卡、语义层、知识层或 verified SQL |
| `BLOCKED` | 证据不足、连通失败、freshness 阻塞、需要人拍板 |

全局分流要回答：

- 改 CK 表是否影响 Hive 同源表。
- 改 Hive 表是否影响 CK 查询副本。
- 改表卡是否影响 `semantic_contract` 指标 / join。
- 新 verified SQL 是否需要抽象成 semantic metric / diagnostic。
- 新知识是否能进入 `knowledge/agent_knowledge/catalog.yaml` 默认召回。

### P1：统一执行入口

当前已有保守预检入口：

```bash
python3 tools/scripts/maintain_data_base.py
```

已具备能力：

- 读取 git diff 或指定变更对象。
- 判断影响层：`ai_ck` / `ai_hive` / `semantic_contract` / `knowledge` / `da_assets`。
- 输出 `NO_IMPACT` / `CHECK_ONLY` / `NEEDS_AGENT` / `BLOCKED`。
- 给出应跑脚本清单。
- 不自动改业务口径。

仍未具备：

- 不直接执行修复、live probe 或回归。
- 已经过一次低风险 Hive 表卡 freshness 变更、一次 CK schema drift、一次 candidate SQL live revalidation、一次 verified SQL 正向晋升、一次 knowledge 默认召回负向验证、一次低风险 knowledge 默认召回正向验证和一次 semantic governance 变更；尚未覆盖会改变 Hive / CK 默认选表、join 或 PII 边界的深卡变更。

### P2：把 TODO 升级为正式 runbook

前置条件：

- CK / Hive 都有各自 adapter 维护流程。
- 全局变更分流至少被一次真实变更验证。

迁移目标：

```text
TODO/数据底座维护Harness.md
  -> tools/runbooks/数据底座维护Harness.md
```

同时更新：

- `tools/runbooks/README.md`
- `AGENT_RETRIEVAL_MAP.yaml`
- `eval/agent_regression/run_regression.py` 或相关门禁

## 当前可复用基础

| 能力 | 已有位置 |
| --- | --- |
| CK adapter | `ai_ck/engineering_artifacts/CK维护流程.md` |
| CK 三层分工 | `ai_ck/README.md` |
| CK asset layers | `ai_ck/agent_manifest.yaml` |
| Hive adapter | `ai_hive/Hive维护流程.md` |
| Hive 三层分工 | `ai_hive/README.md` |
| Hive asset layers | `ai_hive/agent_manifest.yaml` |
| 表卡质量门禁 | `tools/scripts/check_table_card_quality.py` |
| 知识一致性门禁 | `tools/scripts/check_knowledge_consistency.py` |
| 检索路线图门禁 | `tools/scripts/check_agent_retrieval_map.py` |
| 语义模型回归 | `knowledge/engineering_artifacts/semantic_contract/build_model.py`、`knowledge/engineering_artifacts/semantic_contract/eval/compose_sql.py` |
| Agent 回归 | `eval/agent_regression/run_regression.py` |
| 健康检查 | `tools/scripts/run_data_agent_healthcheck.py` |
| 早期全局规则稿 | `tools/runbooks/数据资产更新自动化.md` |

## 决策边界

Agent 可以先做：

- 结构分层。
- 召回边界。
- 表卡 / manifest / README 一致性。
- 脚本门禁串联。
- TODO 和 blocker 显性化。

需要人确认：

- Hive 表进入默认召回的高风险优先级和 L3 晋升。
- 官方口径、默认指标、阈值、canonical 表版本。
- 高风险业务动作或投放治理动作。
