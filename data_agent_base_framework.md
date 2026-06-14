# Data Agent 数据基座框架

> 展示用途：描述当前数仓 Agent 知识库如何支撑“只读分析型 Data Agent”，以及后续上层能力还需要怎么建设。  
> 脱敏原则：只展示架构、能力、状态和抽象流程，不暴露数据库凭据、Token、账号、用户级明细或广告平台操作人。

## 一句话定位

当前目录已经形成一个面向投放分析的 **Data Agent 基座层**：它把数据表、业务口径、语义模型、verified SQL、SOP、case、freshness 和回归测试组织成可被 Agent 召回和验证的知识底座。

现阶段适合启动 **只读 POC**：回答“发生了什么、怎么拆、风险在哪里、还缺什么确认”。  
还不适合启动自动动作：放量、停投、降预算、预算迁移等仍需要人类拍板和后验闭环。

## 总体框架

```mermaid
flowchart TB
  U["用户问题<br/>ROI / DNU / 素材 / 点位 / Campaign / 数据质量"]

  subgraph L0["基层：数据与知识基座（当前已具备）"]
    S1["数据源索引<br/>MaxCompute 表卡 / ClickHouse 表卡 / MI ROI360 口径"]
    S2["语义模型<br/>实体 / 指标 / 维度 / Join / 默认口径"]
    S3["证据资产<br/>verified SQL / analysis SOP / decision case / raw 引用"]
    S4["运行护栏<br/>freshness / 分区过滤 / PII 禁止 / 跨源 Join 禁止"]
    S5["回归验证<br/>semantic model eval / Agent R1-R8 regression"]
  end

  subgraph L1["中层：只读分析 Agent（当前可 POC）"]
    A1["问题分类"]
    A2["资产召回"]
    A3["SQL 生成或复用"]
    A4["数据成熟度检查"]
    A5["事实拆解与风险输出"]
  end

  subgraph L2["上层：决策与闭环 Agent（后续建设）"]
    D1["人类决策记录"]
    D2["广告平台操作日志"]
    D3["动作后验评估<br/>D+1 / D+3 / D+7"]
    D4["策略记忆与阈值库"]
    D5["可审计工作台"]
  end

  U --> A1
  A1 --> S2
  A1 --> S3
  S1 --> S2
  S2 --> A2
  S3 --> A2
  S4 --> A4
  A2 --> A3
  A3 --> A4
  A4 --> A5
  A5 --> D1
  D1 --> D3
  D2 --> D3
  D3 --> D4
  D4 --> S2
  D4 --> S3
  D5 --> D1
  D5 --> D2
  D5 --> D3
```

## 当前基层拆解

```mermaid
flowchart LR
  subgraph Data["1. 数据表与元数据"]
    MC["MaxCompute / Hive<br/>事实源、明细、训练与规则源"]
    CK["ClickHouse / MI<br/>ROI360、OLAP、页面口径"]
    Catalog["catalog / table YAML<br/>字段、分区、grain、join key、pitfall"]
  end

  subgraph Semantics["2. 语义与口径"]
    Entity["实体<br/>app / media / campaign / material / event"]
    Metric["指标<br/>cost / CPI / ROI / LTV / retention / ARPU"]
    Join["Join 契约<br/>同源 join、跨源应用层对齐"]
    Status["状态机<br/>verified / confirmed / draft / needs_decision"]
  end

  subgraph Evidence["3. 证据资产"]
    VSQL["verified SQL<br/>可复用查询"]
    SOP["analysis SOP<br/>标准拆解流程"]
    Case["decision case<br/>历史判断与后验"]
    Raw["raw / draft<br/>只作来源，不直接当事实"]
  end

  subgraph Guard["4. 执行护栏"]
    Fresh["freshness snapshot<br/>数据是否到齐"]
    Safety["安全规则<br/>不输出 PII / 不保存密钥"]
    Eval["回归测试<br/>语义模型 + Agent 场景"]
  end

  MC --> Catalog
  CK --> Catalog
  Catalog --> Entity
  Catalog --> Metric
  Entity --> Join
  Metric --> Join
  Join --> VSQL
  VSQL --> SOP
  SOP --> Case
  Raw --> SOP
  Fresh --> VSQL
  Safety --> VSQL
  Eval --> VSQL
```

## 当前可支持的问题

```mermaid
flowchart LR
  Agent["只读 Data Agent"]

  Agent --> ROI["ROI / 回收"]
  ROI --> ROI1["SDK vs AF"]
  ROI --> ROI2["ROI7 / ROI30 / ROI360"]
  ROI --> ROI3["预测偏差"]

  Agent --> DNU["DNU / 激活"]
  DNU --> DNU1["media_source 贡献"]
  DNU --> DNU2["UA / organic / preinstall 拆分"]
  DNU --> DNU3["baseline vs anomaly"]

  Agent --> Material["素材"]
  Material --> M1["CTR / CVR / IPM / CPI"]
  Material --> M2["冷启动初筛"]
  Material --> M3["疲劳候选"]

  Agent --> Point["点位"]
  Point --> P1["S2S 映射"]
  Point --> P2["事件渗透率"]
  Point --> P3["小窗口复盘"]

  Agent --> Campaign["Campaign"]
  Campaign --> C1["放量候选"]
  Campaign --> C2["观察名单"]
  Campaign --> C3["小样本风险"]

  Agent --> Quality["数据质量"]
  Quality --> Q1["freshness"]
  Quality --> Q2["分母口径"]
  Quality --> Q3["join key 风险"]
```

## 当前质量判断

| 模块 | 当前状态 | 评价 |
|---|---|---|
| 表卡与 catalog | 已覆盖主链路 | 可以支撑 Agent 找表、理解字段、识别分区和 join key |
| 语义模型 | 已有机器可读模型与回归 | 是基座最关键的加分项，减少临场拼口径 |
| verified SQL | 已沉淀一批高频问题 | 能支撑只读问答，但素材 ROI、点位扩窗还要补 |
| SOP / case | 已有流程和草稿 case | SOP 可用，case 还缺动作和后验闭环 |
| freshness | 已有 CK / MC 快照 | 能避免“数据未到当劣化”，但需要持续刷新 |
| 回归验证 | R1-R8 通过 | 具备 POC 入场条件 |
| 自动动作 | 暂未建设 | 正确，当前不应自动停投、放量或改预算 |

## 上层还需要建设什么

```mermaid
flowchart TB
  Base["当前基座层<br/>表卡 + 语义模型 + verified SQL + SOP + freshness + eval"]

  subgraph Need["上层建设重点"]
    H1["1. 决策闭环层<br/>记录问题、结论、人类决策、动作、后验"]
    H2["2. 阈值与策略层<br/>红线、达标线、冷启动、小样本、观察期"]
    H3["3. 外部操作日志层<br/>Google / Meta / AppLovin 等只读 change log"]
    H4["4. 分析工作台层<br/>一键复盘、证据链、可审计报告"]
    H5["5. 评估与监控层<br/>回归集扩展、口径漂移、freshness SLA"]
  end

  subgraph Outcome["目标形态"]
    O1["从问数到解释"]
    O2["从解释到候选动作"]
    O3["从候选动作到人类确认"]
    O4["从人类动作到后验学习"]
    O5["从单次分析到策略记忆"]
  end

  Base --> H1
  Base --> H2
  Base --> H3
  Base --> H4
  Base --> H5
  H1 --> O3
  H2 --> O2
  H3 --> O1
  H4 --> O4
  H5 --> O5
```

## 建设优先级

### P0：先把只读 POC 跑稳

1. 选择 3 条端到端演练：DNU 下滑、首日 ARPU 下滑、Campaign 观察名单。
2. 每条都固定输出：问题识别、口径参数、freshness、使用资产、SQL、主要事实、风险、待确认项。
3. 把演练结果补进 `da_assets/decision_cases/`，即使暂时没有动作，也要记录“为什么不能下动作结论”。

### P1：把人类经验结构化

1. 找 DA 补 SQL、成熟窗口、baseline/anomaly 选择、素材和点位 join 口径。
2. 找 UA 补冷启动、小样本、放量、降预算、停投、继续观察的判断边界。
3. 把确认后的规则迁入 `knowledge/`、`semantic_model/` 或 `da_assets/`，不要长期留在 TODO。

### P2：接入外部只读操作记录

1. 先做 Google Ads / Meta change log 的只读工具。
2. 只记录脱敏摘要：什么对象、什么时间、什么字段发生变化。
3. 不做自动预算调整、自动暂停、自动出价修改。

### P3：形成闭环 Agent

1. 建立标准链路：`question -> SQL -> result -> conclusion -> human_decision -> action -> aftereffect`。
2. 每个动作后补 D+1/D+3/D+7 后验。
3. 让策略从“经验描述”升级为“可审计、可回放、可迭代”的策略记忆。

## 推荐的目标蓝图

```mermaid
flowchart LR
  Q["业务问题"] --> R["只读分析"]
  R --> E["证据链报告"]
  E --> C{"是否需要人类拍板？"}
  C -->|"否"| K["沉淀为 verified 知识"]
  C -->|"是"| H["人类决策"]
  H --> A["人工执行动作"]
  A --> P["后验评估"]
  P --> M["策略记忆"]
  M --> R
  K --> R
```

## 当前最重要的判断

这个基座现在最大的价值不是“自动替人做投放动作”，而是把 Agent 从临场猜测拉回到一条可控链路：

```text
先识别问题
再召回可信资产
再检查数据是否成熟
再用 verified SQL / semantic model 生成事实
最后输出拆解、风险和待确认项
```

下一阶段的核心，不是继续堆更多文档，而是补 **人类决策 + 操作记录 + 后验评估**。只有这个闭环建立后，Data Agent 才能从“分析助手”升级为“投放治理系统的认知层”。
