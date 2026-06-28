# ai_hive — MaxCompute 表卡知识库

`ai_hive/` 是 Data Agent 的 MaxCompute / Hive 表卡入口，负责回答：

- 应该查哪张 MaxCompute 表。
- 表的粒度、日期、分区、PII 和扫描护栏是什么。
- 哪些 join、口径和示例 SQL 有证据，哪些仍需人工确认。

边界：`ai_hive/` 更接近事实源，不把 schema 覆盖等同于默认可信口径。正式复盘、指标解释和 SQL 生成必须按 `engineering_artifacts/Hive表准入标准.md` 的 L1 / L2 / L3 边界使用。当前数据新鲜度、表质量或问答回归结论必须 live probe / 刷新快照后再说，不能把旧 `engineering_artifacts/freshness_snapshot.json` 当实时事实。

## 用途分层规范

三层模型(`agent_knowledge` / `engineering_artifacts` / `audit_archive`)、manifest 约定和跨库归属规则的 canonical 定义见 [`../data_agent_plan/知识库三层结构规范.md`](../data_agent_plan/知识库三层结构规范.md)；本节只列 ai_hive 库各层的具体文件。

### Agent 用的知识层

| 位置 | 作用 | 使用方式 |
| --- | --- | --- |
| `agent_knowledge/catalog.yaml` | 机器可读表目录、层级、优先级、表卡路径 | 用来选表；不是 freshness 或 verified 证明 |
| `agent_knowledge/数据地图.md` | MaxCompute 与 CK / 语义层 / verified SQL 的关系 | 建立方向感，不替代表卡 |
| `agent_knowledge/tables/*.yaml` | 单表深表卡：grain、partition、query_rules、PII、join、pitfalls、example SQL | 命中表后读取；P0/P1 也不能绕过证据 |
| `agent_knowledge/PII_POLICY.yaml` | PII 列名和行为规则的 canonical 源 | 生成 SQL 和输出前必须遵守 |
| `agent_knowledge/口径决策记录.md` | 达成率、安装/激活分母、campaign 映射等已沉淀决策 | 只在相关主题命中时读取 |

### 工程建设沉淀层

| 位置 | 作用 | 谁会用 |
| --- | --- | --- |
| `engineering_artifacts/Hive表准入标准.md` | Hive/MaxCompute 表进入 Agent 的 L0-L3 准入规范 | Agent 和维护者 |
| `engineering_artifacts/Hive维护流程.md` | 新增 / 更新 Hive 表时的 adapter 流程 | Agent 和维护者 |
| `engineering_artifacts/table_card_schema/TABLE_TEMPLATE.yaml` | 新建表卡模板 | 新表准入 |
| `engineering_artifacts/discovered_tables.yaml` | `sync_ai_hive_schema.py` 的批量同步种子和补充元数据 | schema 同步脚本 |
| `engineering_artifacts/freshness_snapshot.json` | 由 `tools/scripts/probe_freshness.py` 刷新的 MaxCompute 新鲜度快照 | 新鲜度门禁；评估当前状态前必须刷新 |

### 审计 / 归档层

| 位置 | 作用 | 处理原则 |
| --- | --- | --- |
| `audit_archive/evidence/` | 被当前口径记录或表卡引用的结构化证据、DDL、smoke test | 只支撑对应记录，不直接默认召回 |
| `audit_archive/来源索引.md` | 审计证据目录说明和使用边界 | 追溯来源，不替代表卡 / verified SQL / live probe |

已清理掉的历史产物：

- `export/RAG召回包.md`：可由脚本临时导出，不再作为仓库事实源维护。
- `queries/open_decisions_explore.sql`：一次性探索 SQL，结论已沉淀到 `agent_knowledge/口径决策记录.md` 和 `audit_archive/evidence/`。
- `sources/`：历史来源件不进默认召回；如需追溯放 `audit_archive/`。
- 旧的主题散文不替代表卡。选表回到 `agent_knowledge/catalog.yaml` / `agent_knowledge/tables/*.yaml`；跨源 ROI/设备解释回到 `agent_knowledge/数据地图.md`、`knowledge/agent_knowledge/semantic_contract/`、`ai_ck/agent_knowledge/metrics/` 和 `da_assets/verified_sql/`。
- `sync_report*.json`、`同步报告.md`：历史同步报告，不作为当前入口。
- `DataWorks手工补数清单.md`、`用户增长Topic表知识.md`：建设期清单，已由表卡、catalog 和准入规范承接。

## 当前覆盖状态

以 `agent_knowledge/catalog.yaml` 和 `agent_knowledge/tables/*.yaml` 为准：

| 项 | 当前值 |
| --- | ---: |
| catalog 表数 | 119 |
| 表卡数 | 119 |
| 层级分布 | ods 29 / dwd 25 / dim 28 / dws 24 / ads 13 |
| 状态分布 | complete 114 / partial 3 / partial_verified 1 / verified 1 |
| 优先级分布 | P0 28 / P1 25 / P2 48 / P3 18 |

`complete` 表示表卡结构和基础材料完整，不自动等于 L3 verified。进入默认高频分析、语义层或 verified SQL 仍需要小窗口实跑、join smoke test、对账结果或 owner / DA / 数仓确认。

## Agent 读法

1. 先读 `README.md`、`agent_knowledge/catalog.yaml`、`agent_knowledge/数据地图.md`。
2. 达成率、安装分母、campaign 映射补读 `agent_knowledge/口径决策记录.md`；ROI/MI 或设备资产问题转读 `ai_ck/agent_knowledge/metrics/`、`knowledge/agent_knowledge/semantic_contract/`、`da_assets/verified_sql/` 和命中表卡。
3. 命中表后只读对应 `agent_knowledge/tables/<table>.yaml`，不要把整个 `agent_knowledge/tables/` 塞进上下文。
4. 写 SQL 前检查 `query_rules.must_filter`、PII、日期字段、known_pitfalls。
5. 涉及当前新鲜度、表质量或回归结论时，按 AGENTS.md 先验证 MC/CK 读取能力并刷新 freshness snapshot。

## 维护入口

常规结构检查：

```bash
python3 tools/scripts/check_table_card_quality.py
```

表卡 schema 批量同步仍走脚本：

```bash
python3 tools/scripts/sync_ai_hive_schema.py --wave all --merge
python3 tools/scripts/enrich_ai_hive_from_discovered.py
python3 tools/scripts/rebuild_ai_hive_catalog.py
```

涉及当前数据状态时才刷新新鲜度：

```bash
source /Users/sere/yrgnuhstudio/cursor_friend_pack_system_env/fill_clickhouse_env_here.zsh
python3 tools/scripts/probe_freshness.py
```

## 硬规则

- 不保存或输出 AK/SK、数据库密码、SSO ticket、MI token、cookie、用户级明细、设备 ID、IP、user_agent。
- 大表必须带分区过滤；没有分区的维表要在表卡说明边界。
- `agent_knowledge/PII_POLICY.yaml` 是 PII 标注唯一真理源；表卡中的 PII 子集由脚本盖章。
- `join_keys` 必须有证据；证据不足写 TODO / 待确认。
- `engineering_artifacts/freshness_snapshot.json` 是快照；评估当前状态前必须刷新。
- raw / draft / historical evidence 只能作为线索，不能直接升级成 verified 事实。
