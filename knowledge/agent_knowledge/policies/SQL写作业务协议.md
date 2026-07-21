# SQL 写作业务协议

## 目录

- [适用边界](#适用边界)
- [需求写作规范](#需求写作规范)
- [产品与端标准化](#产品与端标准化)
- [场景标准化规则](#场景标准化规则) — 留存、游戏核心指标、实验、商业化、国家层级、投放 ROI、小包广告单元、AB3 实验 ID、模型特征
- [选表与字段证据](#选表与字段证据)
- [SQL 写作规范](#sql-写作规范)
- [输出规范](#输出规范)
- [验证和晋升](#验证和晋升)
- [维护](#维护)

> 状态：active  
> 创建日期：2026-06-18  
> 目的：把 DA 认证 SQL 写作资料中的业务认知、需求描述规范和输出规范沉淀为当前项目协议，避免 Agent 临场发挥。

## 适用边界

本文用于 MaxCompute / ODPS 业务 SQL、NL2SQL、SQL 修改和 SQL 审查。它规定“业务问题如何被标准化为可执行 SQL”，不直接晋升任何 SQL 结果为 verified。

可作为当前默认规则使用：

- 需求描述字段和缺失项追问。
- 产品、端、实验、商业化、留存、国家层级等语义标准化。
- 选表、字段证据、SQL 写作和输出说明的规范。

不可作为默认事实使用：

- reference 中的示例 SQL 执行结果。
- 未经过 live schema / dry-run / 小窗口验证的字段或 SQL。
- 任何用户级明细、设备 ID、IP、token、cookie、user_agent。

## 需求写作规范

用户需求优先按以下结构理解：

```text
业务目标：
产品名：
分端：
时间范围：
维度：
指标：
限制条件：
备注：
```

最小必填项：

| 字段 | 规则 |
|---|---|
| 产品名 | 尽量使用标准产品名；可由别名、表名、`app_name` 或上下文推断时不反问。 |
| 分端 | `GP / 安卓`、`iOS` 或双端；可从表名或 `app_name` 推断。 |
| 时间范围 | 固定日期或相对日期；实验场景缺失时优先查配置表补齐。 |
| 维度 | 明确结果展开粒度，如天、方案号、campaign、国家、session。 |
| 指标 | 使用业务指标名，避免只写“表现”“效果”“留存”等模糊词。 |

如果用户没有显式给指标，但场景明确，Agent 应先推荐或采用默认指标集，不要只反问“你要看什么指标”。

主动推荐规则：

- 场景、产品和端能唯一判断，且用户语气是“帮我跑一下 / 快速看下 / 出个数”等常规取数时，可直接采用默认指标集，并在回复中说明“先按默认指标集生成，后续可调整”。
- 场景能判断但不适合直接执行时，给出可勾选的紧凑指标集；用户回复“确认 / 可以 / OK / 就这些”即视为默认项确认。
- 用户已给出部分指标时，只补充常一起分析的相关指标，不展开完整模板。
- 场景无法判断时，只问最少缺口：产品 / 端、时间、维度、指标和必要限制条件。

常见默认指标集：

| 场景 | 默认维度 | 默认指标 |
|---|---|---|
| 产品实验 | 方案号、天 | DAU、人均留存天数、人均时长、人均局数、人均收入、不含 banner 的 ECPM |
| 商业化实验 | 方案号、天、`life_type` | 插屏 / 激励的 action、ready、展示 PV、收入、人均留存天数 |
| 大盘趋势 | 天 | DAU、新用户、RR1、人均时长、人均局数、人均收入、ECPM |
| 局 / 轮 / 块分析 | 天、`game_type` | 局均 combo、最大 combo、3 消、多消、清盘、死亡 / 怼死相关指标 |
| 广告链路 | 天 | 插屏 / 激励 load 成功率、action 率、ready 率、完播率，必要时补 ECPM 和人均收入 |

## 产品与端标准化

| 标准产品 | 常见别名 |
|---|---|
| block blast | BB、方块、老方块 |
| double tile | DT、方块麻将 |
| mahjong blast | MB、皇室麻将 |
| block crush | BC、木块 |
| jade mahjong | JM、jade麻将、国风麻将 |
| nova block | NB、block3D |
| MathCross | MC |

端别名：

| 标准端 | 常见别名 |
|---|---|
| GP / 安卓 | 安卓端、GP、GP端 |
| iOS | IOS、iOS端、苹果 |

推断原则：

- 表名包含 `gp` / `ios` 时，表名优先。
- `app_name` 与表索引能唯一命中时，直接推断。
- 产品能推断但端缺失时，大多数分析默认 GP；若出现 iOS 关键词则使用 iOS。
- 推断必须在回复中轻量说明，方便用户纠正。

## 场景标准化规则

### 留存

不要把“留存”原样带进 SQL 口径：

| 场景 | 默认改写 |
|---|---|
| 实验 / 方案号 / abtest / 组别 | 人均留存天数 |
| 大盘 / 分日趋势 / 留存率 | RR1；用户明确要求时补 RR3 / RR7 |
| 用户明确写出口径 | 严格按用户口径 |

SQL 别名、注释和输出说明都必须暴露留存口径。

### 游戏核心指标

涉及 DAU、新用户、RR1 / RR3、人均局数、人均时长、人均收入、ECPM、广告密度、插屏 / 激励链路指标时，先按 `游戏核心指标口径语义.md` 确定业务口径。

执行原则：

- BB、DT、MB 的收入字段族和活跃口径不同，不跨产品硬套字段名。
- 收入指标必须说明是否含 banner；ECPM 必须说明收入和 PV 分母是否含 banner。
- 局数指标必须说明开始局、结束局、结算局、成功 / 失败 / 重开局。
- MB 必须额外说明活跃口径、广告收入事件来源、异常值封顶 / 剔除规则。
- `游戏核心指标口径语义.md` 只提供语义，SQL 仍必须通过表卡、schema 或小窗口验证。

涉及皇室麻将 / Mahjong Blast / MB 解析表、AB 看板、`start_uv`、`install_game_join_uv`、`game_cnt`、banner 近似为 0、Bayes / 底板指标或 BI 01 / 02 / 03 层时，同时读取 `皇室麻将BI看板查询规则.md`。

涉及用户行为聚合、用户留存、用户画像 / 标签快照时，同时读取 `用户行为留存画像查询规则.md`，尤其要区分分区日期、业务日期、用户粒度和设备粒度。

### 实验类型

实验关键词包括：实验、方案号、abtest、AB测试、组别、实验效果、对照组、实验组、方案对比。

优先自动推断：

| 信号 | 实验类型 | 默认指标 |
|---|---|---|
| 留存、时长、局数、玩法、功能 | 产品实验 | 人均留存天数、人均局数、人均时长、人均收入、ECPM |
| 广告、商业化、变现、插屏、激励、action、ready、eCPM | 商业化实验 | 插屏/激励 action、ready、展示 pv、收入 |

如果方案号或批次缺少起止时间，不默认反问日期，优先查实验配置表补齐：

- BB 产品实验：`hungry_studio.dim_block_blast_abtest_conf_sq_ha`
- BB GP 商业化 / 算法实验：`hungry_studio.dim_block_blast_gp_ad_realization_ab_pici_adunit_base_conf_ha`
- DT / 其他产品：`hungry_studio.dim_all_app_ab_test_plan_conf_view`

配置表只负责补实验元信息；最终分析 SQL 仍需字段、分区和口径验证。

实验配置、方案效果表优先级、下线实验分区、BB / DT 差异和组别边界遵循 `实验配置与方案查询规则.md`。

### 商业化广告

商业化关键词包括：商业化、广告、变现、eCPM、收入、load、action、ready、插屏、激励、SDK 初始化、广告位、ADX。

涉及商业化链路、商业化实验、广告单元价格层级或广告收入时，先读 `商业化SQL协议.md`；涉及白名单事件表取数时，同时遵守 `白名单事件表查询协议.md`。

场景必须拆成三类：

| 子场景 | 标准指标 |
|---|---|
| 商业化实验 | 插屏 action 次数、插屏 ready 次数、插屏展示 pv、插屏收入、激励 action 次数、激励 ready 次数、激励展示 pv、激励收入 |
| 商业化链路 | app 启动数、广告初始化数、load 开始数、load 成功数、load 成功率、action 数、ready 数、action 到 ready 转化率、eCPM |
| 广告收入 | 广告收入、eCPM、展示 pv；按需求补广告格式或 ADX channel |

商业化埋点缺口不能猜事件名或参数。BB GP / iOS 商业化链路按 `BB商业化埋点查询规则.md` 判断事件族、端差异和字段证据。

涉及 BB GP / iOS 大埋点字典、非商业化事件、APM、push、支付、web / H5、玩法 UI 或端差异字段时，同时读取 `BB大埋点字典使用规则.md`；字典只作为候选线索，仍需元数据、表卡或小窗口验证。

### 国家层级

用户提到 T1 / T2 / T3、Tier 1 / Tier 2 / Tier 3、一级 / 二级 / 三级国家时：

- 必须使用本项目的 `国家等级映射.md`。
- SQL 使用 `country` 的 ISO 2 位码过滤，不用 `country_cn`。
- 多层级合并时取并集；排除层级时使用 `NOT IN` 或互补集合。
- 按国家层级分组时，用 `CASE WHEN country IN (...) THEN 'T1' ... END`。
- 不从记忆里硬编码国家列表。

### 投放和 ROI 预估

涉及 campaign、adset、ad、素材、AppsFlyer 激活、SKAN、消耗、成本、SDK 收入、ROAS / ROI 或 ROI 预估时，先读 `投放与ROI预估SQL协议.md`。

执行原则：

- 保留 `campaign_name` 原始字符串；`campaign_id` 只作为稳定 join fallback。
- 必须区分 `dt` 是全量快照、投放日期、收入日期还是预测分区。
- 必须说明成本是原始消耗、概率消耗还是折后消耗。
- 真实回收、预估回收、SKAN 聚合不能混成一个 ROI 口径。
- `opt_target` 是分类辅助维度，不自动导出停投 / 放量动作。

### 小包广告单元

小包场景涉及兜底 / 中价 / 高价 / high / mid / low 时：

- 必须使用 `小包广告单元映射.md` 和 `小包广告单元映射.csv` 取得 Clean Unit ID。
- 找不到匹配 Package / Ad Type / Role 时，输出 `mapping_missing` 或 `needs_owner_confirmation`，不要临时猜价格层级。
- 先按 Package 过滤小包产品，再用 Clean Unit ID 与事件属性里的 `ad_unit_id` 对齐。
- 不用通用商业化配置表的 `price_type` 替代小包价格层级。

### AB3.0 实验 ID

`fs` / `rv` / `ba` 开头的实验 ID 视为 AB Orthogonal 3.0：

- `fs` / insert = 插屏。
- `rv` / reward = 激励。
- `ba` / banner = banner。
- 从 `properties.s_ad_public_adwaynum_array` 的 JSON 数组里按 layer 提取方案号。
- SQL 的 WHERE、SELECT、GROUP BY 使用对应提取出的 `xxx_waynum`。
- 具体提取正则、旧格式实验和混合实验处理遵循 `AB3实验ID提取规则.md`。

### 模型特征与埋点元数据

涉及用户特征、模型输入、预测分、uplift label、相似人群 label、事件定义、参数定义、用户属性定义或 Hudi 字段映射时，先读 `特征工程与埋点元数据查询规则.md`。

执行原则：

- 模型特征表只用于特征解释、特征分布和模型输出分层，不替代 DAU、留存、收入、ROI 或广告链路事实表。
- `*_y_preds`、`*_uplift_label`、`gmm_similarity_label` 等字段是模型输出或标签，不当作已发生业务事实。
- `id`、`idfa`、`gaid` 等用户 / 设备标识只可内部聚合，不输出明细。
- 埋点元数据表只说明事件、参数或用户属性定义，不说明事件发生次数。
- `event_attribute_name` 是 JSON key，`event_tab_field` 是 Hudi 展开列线索；进入事实表 SQL 前仍需表卡或 live schema 确认。
- 元数据、静态文档和事实表 schema 冲突时输出 `field_definition_conflict`，不要自行合并字段。

## 选表与字段证据

选表优先级：

```text
verified_sql / confirmed policy
→ knowledge/agent_knowledge/semantic_contract/model.json
→ ai_hive / ai_ck 表卡
→ 本项目已蒸馏的 knowledge / semantic_contract / 表卡补充资料
```

选表时先按 `SQL表路由协议.md` 判断产品、端、主题和粒度，再回到 `ai_hive/agent_knowledge/catalog.yaml` / 表卡确认具体表是否已治理。

每条 SQL 生成前必须形成字段证据：

```text
需求项 → 映射字段 → 来源表 → 验证来源
```

合法验证来源：

- `ai_hive` / `ai_ck` 表卡。
- DDL / catalog / semantic model。
- 已进入本项目的 `knowledge/`、`knowledge/agent_knowledge/semantic_contract/`、`da_assets/` 或表卡资料。
- live schema / dry-run / 小窗口 SQL 结果。

禁止：

- 凭字段名猜语义。
- 因为某字段“看起来像”就参与指标计算。
- silently drop 用户要求的维度或指标。
- 把外部资料里的 SQL 示例当作已经跑通的 verified SQL。

如果候选表未进入 `ai_hive/agent_knowledge/catalog.yaml`，必须输出 `candidate_table_requires_intake`，并在 live schema 或小窗口验证前避免把它当成默认事实。

当主表无法覆盖全部维度和指标时，必须显式列出补充表和 JOIN key；无法找到有证据的 JOIN 时，输出 `待确认`。

## SQL 写作规范

基础规范：

- 全部表名使用全限定名。
- 大表必须带分区过滤，并下推到最内层 CTE / 子查询。
- 白名单事件表必须限制 `event_name`，共享表必须限制 `app_name`。
- 不使用 `SELECT *`。
- 除法分母用 `NULLIF(..., 0)`。
- BB + DT 联合输出使用 `UNION ALL` 并统一列别名。
- 不使用 `CROSS JOIN`；必要笛卡尔连接使用 `JOIN ... ON 1=1`，小表配 `MAPJOIN`。
- 不使用 `MAX_PT()` 作为偷懒分区选择；需要最新分区时先 probe 或按表卡规则说明。

MaxCompute 语法硬门控：

- 日期函数使用 MaxCompute 写法，例如 `date_add(date_expr, days_int)`、`DATEDIFF(date1, date2, 'dd')`、`date_format(date_expr, 'yyyy-MM-dd')`；不使用 MySQL `INTERVAL` 和 `%Y-%m-%d` 格式。
- 字符串和 JSON 使用 `SUBSTR`、`INSTR`、`REGEXP_EXTRACT`、`GET_JSON_OBJECT`；不使用 MySQL 专属函数替代。
- 非聚合字段必须出现在 `GROUP BY`；不要依赖 MySQL 宽松分组。
- 默认使用 `UNION ALL`，只有业务明确需要去重时才使用 `UNION`。
- 不使用临时表语法；读数 SQL 优先用 CTE，且 CTE 层数应与复杂度匹配。
- 需要笛卡尔小维表展开时，`JOIN ... ON 1=1` 必须配合小表 `MAPJOIN`，否则视为阻断风险。

全量快照表：

- `dt` 取最新可用分区或配置表对应快照分区。
- 用户日期范围作为业务字段过滤，如 `active_date`、`install_date`、`retention_date`。
- 有 `hour` 分区时取最终小时，例如 `hour='23'`。

局 / 轮 / 块粒度：

- 优先选择能覆盖需求的最粗粒度表：局表 > 轮表 > 块表。
- 只有局表无法覆盖轮级字段时才加轮表；只有轮表也无法覆盖块级字段时才加块表。
- 不能为了“更细”默认扫块表。
- Block Blast 局 / 轮 / 出块查询必须遵循 `局轮出块粒度查询规则.md`，尤其是 `game_type` 过滤、轮表累计字段和抽样表边界。

## 输出规范

对用户输出时不要展示内部六步推理链。最终回答需要包含：

- 需求理解或假设，简短说明即可。
- 可执行 SQL 或修改后的 SQL。
- 口径说明：日期、分区、指标、维度、关键过滤和 JOIN。
- 验证状态：是否 live schema、dry-run、小窗口跑过；未跑必须说明 `未验证` / `candidate_sql`。
- 性能风险：扫描窗口、白名单事件表、COUNT DISTINCT、JOIN 数量、是否 MAPJOIN。
- 待确认项：字段语义、JOIN key、实验类型、业务阈值或 owner 拍板。

交付节奏：

- 先用自然语言简短确认需求；如果缺关键字段，在这里停止并追问。
- 复杂 SQL 可以先给不超过 5 条的数据方案说明；简单 SQL 不需要单独解释方案。
- 最终 SQL 收口应只包含 SQL、必要说明和性能评估，不夹带内部推理、标准化模板、验证 checklist 或中间草稿。
- SQL 修改任务同样先确认改动意图，最终给修改后的 SQL、关键变化和性能评估。

SQL 审查时先列风险和缺陷，再给修复建议；不要先给泛泛总结。

## 验证和晋升

运行或晋升 SQL 时：

- 真实跑数、schema probe、dry-run、小窗口验证必须使用本仓库 `maxcompute-dataworks` 能力。
- 输出必须区分“实时探测结果”和“旧文档 / 旧快照 / reference 结果”。
- 未验证 SQL 只能作为 draft / candidate。
- 可复用 SQL 晋升必须遵守 `da_assets/SQL晋升治理.md`，补齐口径说明、依赖表、验证记录、风险与陷阱。

dry-run 和字段验证原则：

- 交付前优先做 live schema 和 dry-run；连接不可用时，只能给 `candidate_sql` 并说明验证缺口。
- dry-run 失败时按错误回退到选表、字段或语法修复，不把失败 SQL 当最终 SQL 输出。
- 包级安装说明、telemetry、独立 ODPS 配置脚本和本地个人配置不迁移为本项目运行依赖；本项目统一使用现有 `maxcompute-dataworks` helper 和仓库门禁。

## 维护

本文是项目内协议，不依赖外部资料运行。后续逐篇蒸馏 DA 认证资料时，只把稳定业务认知补进 `knowledge/`、`knowledge/agent_knowledge/semantic_contract/`、`da_assets/` 或表卡；外部原文仅作为处理输入，不作为 Agent 默认召回路径。

如果后续发现本协议与 `ai_hive` 表卡、verified SQL 或 live schema 冲突，以当前表卡、verified SQL、live schema 和业务 owner 确认为准，并记录冲突等待治理。
