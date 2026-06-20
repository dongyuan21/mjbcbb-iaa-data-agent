# Agent guide · 数仓 Agent 知识库

本目录是面向 Data Agent / Cursor Agent 的投放、点位、MI ROI360、MaxCompute、ClickHouse 知识工作区。上级目录 `../AGENTS.md` 的规则仍然适用；本文件只补充数仓知识库的常驻规则。

## Always Applied Rules

1. 默认使用中文简体。
2. 后续由 AI 新建的 `.md` 文档默认使用中文文件名；若因外部约定、工具识别或既有固定入口必须使用英文文件名，需在回复中说明原因。
3. 不把 `raw_exports/`、`da_assets/raw/`、`knowledge/draft_knowledge/` 中的内容直接当 verified 事实。其中 `raw_exports/` 与 `da_assets/raw/` 仅本地归档、不纳入 git（见 `.gitignore`）；文档/表卡中指向它们的路径是本地来源标注，不是仓库内可达文件。
4. 报告、截图、docx、PDF、钉钉导出件进入工程时，必须保留来源、周期、提取方式、图片状态和置信度。
5. 不从热力图、复杂多指标图、密集矩阵、模糊截图中反推精确数值；标 `charts_need_source_data` 或 `needs_better_source`。
6. 不保存 AK/SK、数据库密码、SSO ticket、MI token、cookie、用户级明细、设备 ID、IP、user_agent。
7. 涉及 ROI / 投放治理时，先区分 `reviewed`、`draft_pending_sql_validation`、`verified`，不要把会议材料或图片抽取直接升级成最终事实。
8. 评估 `ai_hive` / `ai_ck` / Data Agent 数据基座、数据新鲜度、表质量或问答回归前，必须先建设并验证 MC 与 CK 读取能力：
   - MC：用 `maxcompute-dataworks` helper 执行 `SELECT 1` 和至少一张目标源表的轻量 `max(dt)` / `max(active_date)` probe。
   - CK：先 source 本机 ClickHouse env，再用 helper 执行 `SELECT 1` 和至少一张目标源表的轻量分区 probe。
   - 两边能力未验证成功前，不得把已有 `freshness_snapshot.json`、旧回归报告或表卡日期当作当前事实；只能标 `snapshot_only` / `connectivity_unverified`。
   - 能力验证成功后，必须重跑 `tools/scripts/probe_freshness.py` 刷新 `ai_ck/freshness_snapshot.json` 和 `ai_hive/freshness_snapshot.json`，再跑必要的 agent regression。
   - 回答中必须区分“实时探测结果”和“读取旧快照/旧报告得到的结果”。
9. 修改 `ai_hive/tables/*.yaml`、`ai_ck/tables/*.yaml` 或相关 catalog / PII policy 后，必须运行：

   ```bash
   python3 tools/scripts/check_table_card_quality.py
   ```

   硬错误必须清零；质量缺口先进入 `eval/表卡质量门禁报告.md` 排期治理，不得因为缺口存在而伪装为已修复。
10. 新增 Hive / MaxCompute 表到 `ai_hive/` 时，必须按 `ai_hive/Hive表准入标准.md` 执行。DDL、血缘、生产 SQL / run 日志只是证据来源；进入 Data Agent 默认召回前还必须补齐 `query_rules`、PII、freshness、`join_keys`、`known_pitfalls` 和安全 `example_queries`。
11. 修改 `knowledge/` 下任意文件后，必须同步 `knowledge/manifest.yaml` 并运行：

   ```bash
   python3 tools/scripts/check_knowledge_consistency.py
   ```

   硬错误和 warning 必须清零；不得把 `draft_knowledge/`、`snapshot`、`raw` 或未覆盖当前周期的历史知识加入默认召回。

## Mandatory Skills

### DOCX / 周报 / DA 报告入库

当用户提供 `.docx` 报告、公司周报、DA 分析报告、发行增长双周会，或要求“入库 / 抽取知识 / 沉淀到工程 / 处理报告图片”时，必须先读并执行：

```text
skills/docx报告入库技能/SKILL.md
```

执行要求：

- 归档原始 docx 到 `da_assets/raw/`。
- 抽取正文和 Word 表格为 Markdown。
- 拆出并逐张复核图片，生成 `image_manifest.csv`、`image_extracts.md`、`image_extracts.csv` 和必要的结构化 CSV。
- 抽取可复用知识到 `da_assets/analysis_sop/` 和 `da_assets/decision_cases/`。
- 更新 `da_assets/index.yaml`，做好 raw、attachment、SOP、case 的双向回链。
- 校验 YAML、CSV 和 linter。

### 第一层投放分析

做投放、ROI、DNU、素材、点位、campaign、数据质量分析时，先读：

```text
knowledge/policies/第一层分析Agent协议.md
```

### MI ROI360 分析

做 MI ROI360 页面分析时，先读：

```text
skills/mi_skill/SKILL.md
```

### 业务 SQL / NL2SQL / SQL 审查

做 MaxCompute / ODPS 业务 SQL、自然语言转 SQL、选表、字段校验、SQL 修改或 SQL 审查时，先读：

```text
knowledge/policies/SQL写作业务协议.md
```

执行要求：

- `SQL写作业务协议.md` 是从 DA 认证知识中抽出的业务认知和写作规范，可作为 SQL 写作当前协议。
- 涉及选表、产品端过滤、主题表粒度时，同时读取 `knowledge/policies/SQL表路由协议.md`。
- 涉及游戏核心指标、留存、时长、局数、广告收入、ECPM、广告密度时，同时读取 `knowledge/policies/游戏核心指标口径语义.md`。
- 涉及皇室麻将 / Mahjong Blast / MB 解析表、AB 看板、`start_uv`、`install_game_join_uv`、`game_cnt`、banner 或 BI 01 / 02 / 03 层时，同时读取 `knowledge/policies/皇室麻将BI看板查询规则.md`。
- 涉及产品实验配置、实验方案效果、方案号组别、下线实验分区或 BB / DT 实验表优先级时，同时读取 `knowledge/policies/实验配置与方案查询规则.md`。
- 涉及 Block Blast 局 / 轮 / 出块玩法明细时，同时读取 `knowledge/policies/局轮出块粒度查询规则.md`。
- 涉及用户行为聚合、留存、用户画像 / 标签快照时，同时读取 `knowledge/policies/用户行为留存画像查询规则.md`。
- 涉及白名单事件表、`properties` JSON、商业化链路、广告单元或商业化实验时，同时读取 `knowledge/policies/白名单事件表查询协议.md` 和 `knowledge/policies/商业化SQL协议.md`。
- 涉及 BB GP / iOS 商业化埋点事件族、端差异、收入回调或 ADX / MAX 字段时，同时读取 `knowledge/policies/BB商业化埋点查询规则.md`。
- 涉及 BB GP / iOS 大埋点字典、非商业化事件、APM、push、支付、web / H5、玩法 UI 或端差异字段时，同时读取 `knowledge/policies/BB大埋点字典使用规则.md`。
- 涉及 AB3.0 `fs` / `rv` / `ba` 实验 ID 时，同时读取 `knowledge/policies/AB3实验ID提取规则.md`。
- 涉及小包兜底 / 中价 / 高价广告单元档位时，同时读取 `knowledge/policies/小包广告单元映射.md` 和 `knowledge/policies/小包广告单元映射.csv`。
- 涉及模型特征、模型输出标签、事件定义、参数定义、用户属性定义或 Hudi 字段映射时，同时读取 `knowledge/policies/特征工程与埋点元数据查询规则.md`。
- 涉及投放、AF 激活、SKAN、成本、SDK 收入、campaign / adset / ad、ROAS / ROI 或 ROI 预估时，同时读取 `knowledge/policies/投放与ROI预估SQL协议.md`。
- 源包只作为逐文档蒸馏输入，不作为 Agent 默认召回或运行依赖；蒸馏进度见 `data_agent_plan/SQL写作链蒸馏台账.md`。
- 真实跑数、schema probe、dry-run、小窗口验证仍必须使用 `maxcompute-dataworks` helper。
- 不执行源包 telemetry 或独立 MaxCompute 配置脚本。
- 生成的 SQL 默认是 candidate；只有通过 `da_assets/SQL晋升治理.md` 门禁后才能进入 `verified_sql`。

## Source Priority

资产可信度从高到低：

```text
verified_sql / confirmed policy
→ semantic_model/model.json
→ ai_hive / ai_ck 表卡
→ analysis_sop
→ decision_cases
→ reviewed image extracts
→ raw / draft
```

只有 `verified` / `confirmed` 可以作为默认事实；`reviewed` 和 `draft` 只能作为分析线索、候选判断或待验证项。
