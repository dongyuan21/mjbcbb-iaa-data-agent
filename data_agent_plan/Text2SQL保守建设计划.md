# Text2SQL 保守建设计划

> 状态：active_plan  
> 创建日期：2026-06-19  
> 范围：把新增 DA 认证 SQL 写作知识转成可审计的 Text2SQL 地基。  
> 边界：本文不定义自动 planner / runtime，不把候选 SQL 晋升为 verified，不替业务 owner 拍板。

## 核心判断

当前不适合直接做一个大而全的 Text2SQL 工程。更稳的路线是先把证据链压实：

```text
用户问题
  -> 需求标准化
  -> 场景 policy 命中
  -> 表路由和候选表状态
  -> 字段证据
  -> candidate SQL
  -> schema / dry-run / 小窗口验证
  -> candidate / verified / TODO 回写
```

Text2SQL 只能作为这个链路中的 SQL 草案生成环节，不能绕过表卡、语义层、verified SQL 和 freshness 门禁。

## 当前可用地基

| 地基 | 作用 |
|---|---|
| `knowledge/agent_knowledge/policies/SQL写作业务协议.md` | 需求标准化、场景识别、输出和验证边界 |
| `knowledge/agent_knowledge/policies/SQL表路由协议.md` | 产品、端、主题和粒度路由 |
| `knowledge/agent_knowledge/policies/游戏核心指标口径语义.md` | 核心指标和游戏指标语义 |
| 专项 policy | 商业化、白名单事件、AB3.0、小包、用户行为、局轮块、MB、埋点元数据 |
| `ai_hive/` / `ai_ck/` 表卡 | 字段、分区、PII、freshness、join 和 known pitfalls |
| `knowledge/agent_knowledge/semantic_contract/model.json` | 跨表实体、指标、维度和 join 契约 |
| `da_assets/verified_sql/` | 可优先复用的稳定 SQL |
| `da_assets/candidate_sql/` | 未晋升 SQL 的保守落点 |

## 不做事项

- 不做开放式“自然语言直接生成 SQL”。
- 不把 Text2SQL 放在 Data Agent 顶层入口。
- 不把源材料 SQL、截图、TODO、draft 或 candidate 当 verified。
- 不在字段证据不足时写完整 SQL；只输出缺口和验证计划。
- 不自动执行停投、放量、预算调整或业务阈值判断。
- 不为了速度跳过 freshness、PII、分区和字段存在性检查。

## 第一阶段：字段证据契约

所有新的 Text2SQL candidate SQL 必须先补字段证据。模板见：

```text
da_assets/Text2SQL字段证据模板.md
```

最小证据链：

```text
需求项 -> 指标/维度/过滤/JOIN -> 字段 -> 表 -> 证据来源 -> 验证状态
```

允许的证据来源从强到弱：

```text
verified_sql / confirmed policy
-> knowledge/agent_knowledge/semantic_contract/model.json
-> ai_hive / ai_ck 表卡
-> live schema / dry-run / 小窗口结果
-> knowledge policy
-> candidate_table_requires_intake
```

弱证据可以进入候选分析，但不能支撑 verified SQL。

## 第二阶段：候选表 intake

优先处理 `TODO/SQL写作链候选表准入积压清单.md` 中和高频场景直接相关的表。只做 schema_validated_only 也有价值，必须写清：

- grain
- partitions / hour / app_name
- query_rules.must_filter
- PII 和 aggregation_only 字段
- join_keys 及证据
- freshness / probe 方式
- known_pitfalls
- 安全 example query 或明确暂不提供

优先级：

| 顺序 | 主题 | 理由 |
|---|---|---|
| P0 | 实验配置、实验方案、方案留存 | 支撑“缺实验时间先补配置”的高频 Text2SQL |
| P0 | 白名单事件、商业化链路 | 新增知识密度高，风险也高，适合先压实证据 |
| P1 | 用户行为、留存、画像 | 覆盖大盘、实验和用户分层 |
| P1 | BB 局 / 轮 / 出块 | 下钻价值高，但扫描风险高 |
| P1 | MB BI 解析和看板层 | 规则密集，适合专项治理 |
| P2 | ROI 预估和投放补充表 | 和现有 UA / ROI 语义层合流 |

## 第三阶段：保守 candidate SQL

只在字段证据足够时写 candidate SQL。候选 SQL 必须包含：

- 业务问题和适用范围。
- 字段证据表。
- 依赖表、分区、`app_name` / `event_name` / `hour` 等必需过滤。
- SQL 文本。
- 验证状态：未跑、schema_probe、dry_run_passed、small_window_verified。
- 风险与陷阱：PII、freshness、口径未拍板、候选表未 intake、跨源限制。

晋升仍遵守：

```text
da_assets/SQL晋升治理.md
```

## 第一条保守切片

建议先做：

```text
实验配置补元信息 + 商业化实验候选 SQL
```

原因：

- 需求标准化清楚：产品、端、方案号、时间、指标。
- 规则已经进入 `实验配置与方案查询规则.md`、`商业化SQL协议.md` 和 `白名单事件表查询协议.md`。
- 表卡已覆盖部分核心配置 / 实验表，可继续补 P0 缺口。
- 容易形成字段证据和验证报告。
- 失败时可以明确输出 `candidate_table_requires_intake`、`field_requires_validation` 或 `small_window_validation_required`。

## 验收线

进入下一阶段前，至少满足：

- 新 candidate SQL 都有字段证据。
- 不再出现“字段凭名字猜语义”的 SQL。
- 新增 / 修改表卡通过 `python3 tools/scripts/check_table_card_quality.py`。
- 修改 `knowledge/` 后通过 `python3 tools/scripts/check_knowledge_consistency.py`。
- 修改路由后通过 `python3 tools/scripts/check_agent_retrieval_map.py` 和 agent regression。
- `rg` 检查默认召回中没有源包路径、源包运行脚本或 telemetry 依赖。
- 全量回归中 Text2SQL 路由不把 candidate / TODO / raw 当 verified。

## 产物清单

| 产物 | 落点 |
|---|---|
| Text2SQL 保守建设计划 | `data_agent_plan/Text2SQL保守建设计划.md` |
| 字段证据模板 | `da_assets/Text2SQL字段证据模板.md` |
| 候选表 backlog | `TODO/SQL写作链候选表准入积压清单.md` |
| 候选 SQL | `da_assets/candidate_sql/` |
| verified SQL | `da_assets/verified_sql/` |
| 新表卡 | `ai_hive/agent_knowledge/tables/` / `ai_ck/agent_knowledge/tables/` |
| 新业务规则 | `knowledge/agent_knowledge/policies/` |
| 语义契约 | `knowledge/agent_knowledge/semantic_contract/` |
