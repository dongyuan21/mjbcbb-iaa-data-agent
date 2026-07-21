# policies — 当前业务规则与分析协议

本目录放当前可引用的治理政策、分析协议和问题分类。只有文档内标记为 `confirmed`、`active` 或明确由用户/业务 owner 确认的内容，才能作为当前默认规则。

历史周报中的阈值、目标线、动作经验不要直接写入本目录；必须先进入 `../report_knowledge/` 或 `TODO/`，经确认后再 promote。

## 按业务领域导航

### 投放与 ROI

| 文件 | 一句话 | 状态 |
|---|---|---|
| `投放ROI治理政策.md` | 红线 / 黄线治理规则、预警输出规范、Agent 行为边界 | active |
| `投放与ROI预估SQL协议.md` | UA 投放、AF 激活、成本、SDK 收入、ROAS / ROI 预估 SQL 口径 | active |
| `Campaign全览分析协议.md` | Campaign 健康度 / 异动拆解分析顺序、UA 操作历史关联 | active |
| `Campaign管理与操作协议.md` | Campaign 管理、操作记录查询、UA 操作影响边界 | active |
| `花费同步与对账规则.md` | 花费同步链路、对账逻辑和差异处理 | active |

### 投放数据新鲜度 SLA

| 文件 | 一句话 | 状态 |
|---|---|---|
| `ROI360_AF回收表新鲜度SLA.md` | `tj_ad_revenue_v2` AF 回收表 T-2 freshness SLA | active |
| `ROI360_SDK回收表新鲜度SLA.md` | SDK 回收表 T-2 freshness SLA | active |
| `ROI预测准确性表新鲜度SLA.md` | `ads_market_roi_pred_accuracy_da` T-2 freshness SLA | active |

### SQL 写作与表路由

| 文件 | 一句话 | 状态 |
|---|---|---|
| `SQL写作业务协议.md` | SQL 写作链中的业务认知、需求标准化、SQL 输出和验证规范 | active |
| `SQL表路由协议.md` | SQL 选表路由、产品端过滤、主题表粒度和候选表 intake 边界 | active |
| `国家等级映射.md` | T1 / T2 / T3 国家等级映射，用于 SQL 中展开 country 过滤和分组 | active |

### 游戏产品指标与玩法

| 文件 | 一句话 | 状态 |
|---|---|---|
| `游戏核心指标口径语义.md` | 留存、时长、局数、广告变现等游戏核心指标口径语义 | active |
| `局轮出块粒度查询规则.md` | Block Blast 局 / 轮 / 出块粒度玩法分析的选表、字段和扫描护栏 | active |
| `皇室麻将BI看板查询规则.md` | Mahjong Blast 解析表、AB 看板 01/02/03 层、活跃 / 收入 / 局数口径 | active |

### 商业化与埋点

| 文件 | 一句话 | 状态 |
|---|---|---|
| `商业化SQL协议.md` | 商业化链路、商业化实验、广告单元和广告收入 SQL 口径 | active |
| `BB商业化埋点查询规则.md` | BB GP / iOS 商业化埋点事件族、端差异、字段标准化和收入 / eCPM 边界 | active |
| `BB大埋点字典使用规则.md` | BB GP / iOS 大埋点字典事件族、端差异、字段验证和 PII / token 风险 | active |
| `白名单事件表查询协议.md` | 白名单事件表查询、事件过滤、JSON 字段和扫描风险护栏 | active |
| `小包广告单元映射.md` | 小包 Clean Unit ID 与兜底 / 中价 / 高价档位映射（配套 `小包广告单元映射.csv`） | active |

### 实验与特征工程

| 文件 | 一句话 | 状态 |
|---|---|---|
| `AB3实验ID提取规则.md` | AB3.0 `fs` / `rv` / `ba` 实验 ID 从分层表提取的规则 | active |
| `实验配置与方案查询规则.md` | 实验配置、方案效果、BB / DT 实验表优先级、日期快照和组别边界 | active |
| `特征工程与埋点元数据查询规则.md` | 模型特征、模型输出标签、事件定义、参数定义和 Hudi 字段映射 | active |

### 用户行为与画像

| 文件 | 一句话 | 状态 |
|---|---|---|
| `用户行为留存画像查询规则.md` | 用户行为、留存、画像 / 标签快照 SQL 的选表、分区、粒度和 PII 边界 | active |

### 点位与 S2S

| 文件 | 一句话 | 状态 |
|---|---|---|
| `点位Campaign映射查询规则.md` | 点位 `s2s_event` 与 Campaign / AdSet 的 CK 映射、join 口径、两跳分析 | active |

### MI 平台

| 文件 | 一句话 | 状态 |
|---|---|---|
| `MI平台架构参考.md` | MI 平台架构认知（P3 - 仅作参考，不作为当前规则） | active |
| `MI平台其他模块协议.md` | MI 平台投放内容池、Google 实验、GP Store、KOL、预测服务五模块协议 | active |

### 分析协议与问题分类

| 文件 | 一句话 | 状态 |
|---|---|---|
| `第一层分析Agent协议.md` | 第一层分析 Agent 固定执行规程 | active |
| `第一层分析Agent问题目录.md` | 问题池、任务分类、参数草案和资产入口 | active_backlog |

### 治理与工具

| 文件 | 一句话 | 状态 |
|---|---|---|
| `默认召回边界与晋升规则.md` | Agent 默认召回、证据分层、知识晋升边界 | active |
| `工具调用审计输出模板.md` | 工具调用审计字段、失败记录和人工决策输出模板 | active |
| `DA问题已处理结论_20260628.md` | DA 问题已处理结论归档（2026-06-28） | review_log |
