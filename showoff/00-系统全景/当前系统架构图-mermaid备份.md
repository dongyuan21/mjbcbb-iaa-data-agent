# 当前系统架构图 · mermaid 备份

> 备份自 [`当前系统架构图.md`](当前系统架构图.md)。
> 正文已改用手绘 Excalidraw PNG；本文件仅保留原始 mermaid 源，便于 diff / 文本检索。
> 备份日期：2026-07-31（单一 Python Runtime 主链）。
> 说明：图 1 的四块是展示视图，不是 Runtime 权威架构的 L1–L6；白盒主链见 [`从一个问题看懂Data Agent.md`](从一个问题看懂Data%20Agent.md)。

## 图1 · §1 系统全景（四层栈）

```mermaid
flowchart TB
  User["业务问题<br/>ROI、DNU、素材、点位、Campaign"]

  subgraph EvalView["评测闭环展示视图"]
    Eval["eval/ 回归与评测集<br/>以最新报告为准"]
    Gate["tools/scripts/ 门禁脚本<br/>以当前门禁清单为准"]
  end

  subgraph RuntimeView["运行层展示视图"]
    Runtime["runtime/backend FastAPI<br/>+ MinimalToolLoop<br/>+ runtime/deploy 分析平台 K8s"]
  end

  subgraph ControlView["控制面展示视图"]
    Map["AGENT_RETRIEVAL_MAP.yaml<br/>检索路线图"]
    Routes["task_routes/<br/>一任务一文件"]
  end

  subgraph KnowledgeView["知识基座展示视图"]
    Hive["数据资产目录<br/>MaxCompute 数据资产目录"]
    Ck["数据资产目录<br/>ClickHouse/MI 数据资产目录"]
    Knowledge["knowledge<br/>业务口径合同 + 政策"]
    Assets["da_assets<br/>已验证 SQL、SOP 与 case"]
  end

  MC["MaxCompute / Hive<br/>事实源和明细"]
  CK["ClickHouse / MI<br/>报表层和 OLAP"]
  Report["周报 / DA 报告<br/>沉淀经验和案例"]
  Output["汇报输出<br/>事实、拆解、风险、待确认项"]

  User --> ControlView
  ControlView --> RuntimeView
  RuntimeView --> KnowledgeView
  KnowledgeView --> MC
  KnowledgeView --> CK
  Report --> KnowledgeView
  RuntimeView --> Output
  EvalView -. 门禁/回归 .-> KnowledgeView
  EvalView -. 精度/线上 review .-> RuntimeView
```

## 图2 · §2 知识基座三层模型

```mermaid
flowchart TB
  Agent["agent_knowledge/<br/>Agent 知识层 · 默认召回候选"]
  Eng["engineering_artifacts/<br/>工程沉淀层 · 默认不进召回"]
  Audit["audit_archive/<br/>审计归档层 · 默认不进召回"]

  Agent -. 维护/排障 .-> Eng
  Agent -. 追溯/证据 .-> Audit
```

## 图3 · §3 知识晋升通道

```mermaid
flowchart TB
  Raw["原始材料<br/>报告、截图、临时 SQL、DDL"]
  Review["人工或脚本复核<br/>抽取、标注、脱敏"]
  Candidate["候选资产<br/>候选 SQL / 草稿流程 / L0-L1 数据资产目录"]
  Validate["验证<br/>小窗口跑数、schema probe、对账"]
  Verified["可信资产<br/>已验证 SQL / L2-L3 数据资产目录 / SOP / case"]
  Recall["默认召回候选<br/>仍受 route / 状态 / first_read 约束"]

  Raw --> Review --> Candidate --> Validate --> Verified --> Recall
```

## 图4 · §4 控制面按需加载

```mermaid
flowchart LR
  Q["用户问题"] --> Boot["L0 常驻导航<br/>README + AGENTS + 路由图 + INDEX"]
  Boot --> Index["L1 路由索引<br/>task_routes/INDEX.yaml"]
  Index --> Task["L2 命中任务<br/>单一 task_route"]
  Task --> First["L3 first_read<br/>协议 + 数据资产目录 + SOP + 阈值"]
  First --> Card["L4 命中数据资产目录<br/>不整包加载"]
  Card --> Vsql["L5 verified SQL<br/>按路由、问题形态与资产状态受控命中"]
  Vsql --> Ans["带证据和数据时效的回答"]
```

## 图5 · §5 运行层问答主路径

```mermaid
flowchart TD
  Q["1. 用户问题"] --> Auth["2. 鉴权与请求校验<br/>创建可恢复 Job"]
  Auth --> Queue["3. MySQL 持久化 + Redis 投递"]
  Queue --> Worker["4. runtime_worker 领取 Job<br/>租约与幂等保护"]
  Worker --> Resolve["5. 控制面解析<br/>问题归一化、路由、反问判断"]
  Resolve --> Route["6. KnowledgeRouter<br/>命中 task_route"]
  Route --> Assemble["7. 初始上下文装配<br/>first_read、数据资产目录摘要、verified SQL"]
  Assemble --> Loop["8. MinimalToolLoop<br/>模型可见工具通常 9；特定白名单 route 10"]
  Loop --> Guard["9. 运行时护栏<br/>先读 DataContractView，再做只读、PII、分区、合同 binding"]
  Loop --> Verify["10. 回答校验与持久化<br/>trace、QueryRecord、JobEvent"]
  Verify --> Answer["11. 流式输出答案<br/>事实、证据、限制、风险、needs_decision"]

  Loop --> Need{"需要更多已授权证据？"}
  Need -->|"是：仅受控工具"| Guard
  Need -->|"否"| Verify
```

## 图6 · §5.2 默认 off 主路径

```mermaid
flowchart LR
  Q["问题"] --> R["规则路由"]
  R --> P["命中 route 的 first_read / allowed_assets"]
  P --> C["一次性预编译上下文"]
  C --> A["MinimalToolLoop：仍只能通过受治理工具继续取证"]
```

## 图7 · §6 评测闭环三线评测

```mermaid
flowchart TB
  Asset["资产齐备性回归<br/>run_regression.py"]
  Precision["精度对比回归<br/>run_resolver_precision.py<br/>rule/model/hybrid 三模式"]
  Live["线上 review<br/>review-sampler skill<br/>真实调用 + 人工判 pass/fail"]

  Asset --> Report["Agent回归报告.md"]
  Precision --> PrecReport["resolver_precision_report.md"]
  Live --> ReviewRuns["review_runs/"]
```
