# ai_ck — ClickHouse / MI 投放报表知识库

`ai_ck/` 是 ClickHouse / MI 报表层的 Data Agent 知识入口，用来回答三类问题：

- 查哪个 CK 表，按什么日期、粒度、字段过滤。
- MI 报表页面上的字段、指标、预估值如何映射到 CK 口径。
- 当前 CK 表卡、字段画像、样例、验证 SQL 和新鲜度快照在哪里。

边界：CK 是 MI / PGP 高频 OLAP 查询层，不替代 `../ai_hive/` / MaxCompute 事实源。正式训练、标签校验、规则发现仍以 ODPS / MC 为准。跨表指标先读 `../knowledge/agent_knowledge/semantic_contract/model.json`，不要只靠散文或单表字段拼 SQL。

## 用途分层规范

三层模型(`agent_knowledge` / `engineering_artifacts` / `audit_archive`)、manifest 约定和跨库归属规则的 canonical 定义见 [`../data_agent_plan/知识库三层结构规范.md`](../data_agent_plan/知识库三层结构规范.md)；本节只列 ai_ck 库各层的具体文件。

### Agent 用的知识层

这层是日常问答和 SQL 生成真正要用的材料。

| 位置 | 作用 | 使用方式 |
| --- | --- | --- |
| `agent_knowledge/catalog.yaml` | 机器可读表目录、优先级、领域标签、语义模型入口 | 选表和判断是否已纳入治理；状态类字段只是快照 |
| `agent_knowledge/数据地图.md` | CK 与 MI / MC 的关系、主链路说明 | 建立方向感，不替代表卡 |
| `agent_knowledge/tables/` | 完整表卡：粒度、日期字段、join、PII、query_rules、pitfalls | 命中核心表后读取；P0/P1 口径以这里为准 |
| `agent_knowledge/metrics/` | 指标、页面字段、安装激活、预估实现等跨表语义 | 问 ROI、LTV、留存、MI 页面字段时读取 |
| `agent_knowledge/table_profiles/INDEX.md` | 字段画像索引 | 非核心表先命中索引，再决定是否读单表画像 |
| `agent_knowledge/table_profiles/<table>.md` | 单表轻量字段画像 | 只回答“字段/表是否存在”，不替代表卡口径 |
| `agent_knowledge/MI_ROI360平台能力说明.md` | MI ROI360 看板能力说明 | 讨论页面能力、筛选器、导出、模板时读取 |

### 工程建设沉淀层

这层是把 CK 知识库建设起来时留下的中间产物和可复跑证据。它们服务脚本、门禁、表卡维护，不进入普通问答默认上下文。

| 位置 | 作用 | 谁会用 |
| --- | --- | --- |
| `agent_manifest.yaml` | 外部 Agent 挂载清单和召回边界 | Agent 平台 / 导出流程；不是表清单权威 |
| `engineering_artifacts/CK维护流程.md` | 新增 / 更新 CK 的维护 harness | Agent 和维护者在变更 `ai_ck` 时读 |
| `engineering_artifacts/ClickHouse表准入标准.md` | CK 表进入 Agent 的 L0-L3 准入规范 | Agent 和维护者 |
| `engineering_artifacts/queries/example_verification.json`、`engineering_artifacts/queries/示例查询验证报告.md` | 表卡 example SQL 的执行证明 | 回归和表卡验收 |
| `engineering_artifacts/queries/metric_sanity.json` | 主链路指标非空自检结果 | 回归和健康检查 |
| `engineering_artifacts/queries/verified/` | 少量可复用诊断 SQL | 排障、覆盖率验证；业务复盘 SQL 放 `../da_assets/verified_sql/` |
| `engineering_artifacts/schema_exports/` | `system.tables` / `system.columns` / `system.parts` 基线 | 字段画像生成、schema 漂移检测、物理键回填 |
| `engineering_artifacts/business_profiles/` | 安全样例行、P0 近 7 天聚合画像 | 建表卡、理解数据长相；不能当当前口径 |
| `engineering_artifacts/table_card_schema/` | 表卡模板和准入结构 | 新增 CK 表卡 |
| `engineering_artifacts/freshness_snapshot.json` | P0 表最新分区和延迟快照 | 新鲜度门禁；评估当前状态前必须刷新 |
| `engineering_artifacts/table_version_registry.yaml` | 多版本表活跃/停更登记 | 选择 canonical 表、淘汰旧版表 |

### 审计/归档层

这层只为追溯服务，不进默认召回。

| 位置 | 作用 | 处理原则 |
| --- | --- | --- |
| `audit_archive/table_profiles_raw_dump/` | `_local`、temp、test、staging、dist、replica、停更旧表画像 | 仅 schema 漂移和历史追溯用 |
| `audit_archive/同步报告.md` | 建设/同步过程记录 | 人读审计，不作为当前事实 |
| `audit_archive/来源索引.md` | 说明各类证据从哪里来 | 追溯来源，不替代 live probe |
| `audit_archive/数仓市场全库表清单.md` | 基于历史 schema 导出的全库说明 | 人读背景；当前选表仍回到 `agent_knowledge/catalog.yaml` / 表卡 |
| `../术语解释/数仓市场领域知识总结.md` | `shucang_market` 领域、表域和命名习惯解释 | 概念背景；不能替代当前 schema / freshness / 表卡 |

简化判断：

- `agent_knowledge/tables/` 负责“这张表怎么查”，不能被 profile 替代。
- `agent_knowledge/table_profiles/` 负责“库里有哪些表和字段”，可以减少无关表卡进入上下文；这就是它存在的主要价值。
- `agent_knowledge/metrics/` 负责“指标/页面是什么意思”。
- `engineering_artifacts/queries/` 负责“表卡示例和诊断 SQL 有没有真跑过”，不是给日常问答直接召回的材料。

## ROI360 命名边界

这里必须区分三个说法：

| 说法 | 含义 | 推荐文档 |
| --- | --- | --- |
| MI ROI360 看板 | MI 页面 `投放分析 -> 通用报表 -> ROI报表(360)`，是一套可配置报表系统，包含筛选器、维度、指标、rows / summary、导出、模板和预估展示 | `agent_knowledge/MI_ROI360平台能力说明.md`、`agent_knowledge/metrics/MI_ROI360页面字段字典.md` |
| ROI360 指标 | 单个指标字段，展示名 `ROI360`，字段通常是 `roi_359`，表示 360 日累计回收 / 折后消耗 × 100 | `agent_knowledge/metrics/ROI360指标语义.md`、`agent_knowledge/metrics/ROI预估实现说明.md` |
| ROI360 主链路 | 为复现 MI ROI360 看板而使用的 CK spend、SDK/AF revenue、retention、forecast、campaign mapping 等表链路 | `agent_knowledge/catalog.yaml`、`agent_knowledge/tables/*.yaml`、`../knowledge/agent_knowledge/semantic_contract/model.json` |

写文档时，`MI ROI360` 默认指看板/页面；`ROI360 指标` 才指单个指标。只写 `ROI360` 容易混淆，除历史文件名外应尽量补上“看板”“指标”或“主链路”。

判断 `ROI360 指标` 时还要同时说明：

- `revenue_source`：默认常见为 `sdk`，`af` 是 AppsFlyer 回收对照口径。
- 是否预估：蓝底 `#E0FFFF` 表示预估值；非蓝底才是已返回真实段。
- `forecast_version`：不同包体可能不是同一套预估版本，不能写成统一默认。
- 成熟度：请求日期超过已成熟回收窗口时，不应把缺失或预估当劣化。

## Agent 读法

1. 先读 `README.md`、`agent_knowledge/catalog.yaml`、`agent_knowledge/数据地图.md`。
2. 查核心表时读对应 `agent_knowledge/tables/*.yaml`；非核心表先从 `agent_knowledge/table_profiles/INDEX.md` 找到字段画像。
3. 涉及 ROI / LTV / 留存 / MI 页面字段时，补读 `agent_knowledge/metrics/` 下对应文档。
4. 涉及跨表拼接时，先读 `../knowledge/agent_knowledge/semantic_contract/model.json` 的 metric 和 join 契约。
5. 涉及当前新鲜度、回归或表质量结论时，必须区分实时探测和旧快照。

## 硬规则

- 不记录、输出或提交 ClickHouse / MI / SSO / token / AK / SK / cookie。
- CK 查询必须带日期范围；消耗/回收优先用 `active_date`，留存同时看 `dt`、`active_date`、`date_diff`。
- `campaign_name` 可能有前导空格；传给 MI 或精确 join 时不能 trim。
- 当前 MI 兼容查询仍以 `campaign_name` 为主，`campaign_id` 作为稳定兜底键，切换前要有 MI 侧实证。
- `engineering_artifacts/freshness_snapshot.json` 是快照，不是实时事实；评估当前状态前要刷新。
- CK 表诊断 SQL 放 `ai_ck/engineering_artifacts/queries/verified/`；可复用业务 SQL 放 `../da_assets/verified_sql/`。

## 刷新入口

新增或更新 CK 表、口径、schema drift 时，先读 `engineering_artifacts/CK维护流程.md`，再决定是脚本刷新、Agent 改知识层，还是需要人确认。

所有命令都在数仓根目录执行：

```bash
cd /Users/<dev>/acme-studio/点位/数仓
bash tools/scripts/refresh_ai_ck.sh
```

单项脚本和连通说明见 `tools/runbooks/ClickHouse连通与新鲜度探测.md`。新增或删除 curated profile 后，重跑 `python3 tools/scripts/build_ai_ck_profile_index.py` 刷新 `agent_knowledge/table_profiles/INDEX.md`。
