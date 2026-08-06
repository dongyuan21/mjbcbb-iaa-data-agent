# UA 沉淀后续工作清单（供你过目）

> 日期：2026-07-23
>
> 这是 Phase 1A 到 Phase 6 的完整任务清单，按执行顺序排列。你过目后启动目标模式，我按这个清单自驱推进，只在标记"🔔 需要你"的地方停下来问你。

## Phase 1A：Google 预算事实与 Episode（我自驱，不需要你）

| 序号 | 任务 | 做什么（人话） | 需要你？ |
|---|---|---|---|
| 1 | UA-1A-01A | 设计账户、汇率、Campaign 身份、预算资源桥的表结构（只设计不建表） | 否 |
| 2 | UA-1A-01B | 设计操作日志、统一变更日志、CanonicalOperationEvent 的表结构 | 否 |
| 3 | UA-1A-01C | 设计 Opportunity、特征快照、Outcome、Episode、能力清单的表结构 | 否 |
| 4 | UA-1A-02 | 实现 Google 操作日志的采集代码（分页、去重、coverage 审计） | 否 |
| 5 | UA-1A-03 | 实现账户 SCD、Campaign 身份 SCD、共享预算桥 | 否 |
| 6 | UA-1A-04 | 实现 Observation → 统一变更日志 → CanonicalOperationEvent 的 ETL | 否 |
| 7 | UA-1A-05 | 实现每日固定复盘 + 异常触发两类 Opportunity 生成器 | 否 |
| 8 | UA-1A-06 | 实现三类标签（实际动作/人工决定/审核状态）的生成逻辑 | 否 |
| 9 | UA-1A-07 | 实现 point-in-time 特征快照（不含未来信息）+ 泄漏检测 | 否 |
| 10 | UA-1A-08 | 实现 D3/D7/D14 Outcome 回填（收入、消耗、CPI、ROI） | 否 |
| 11 | UA-1A-09 | 把以上所有部分拼成一行一 Episode 的数据集 + 能力清单 | 否 |
| 12 | UA-1A-09P | 实现能力清单从 MC 到 CK 的安全投影 | 否 |
| 13 | UA-1A-09R | 🔔 受控发布到测试环境 + 小窗口真实数据跑通 | **需要你授权发布** |
| 14 | UA-1A-09V | 真实数据对账 + freshness 验收（只读检查） | 否 |
| 15 | UA-1A-10 | Level 0 人工抽样核验 Google Episode 准确性 | 🔔 **需要你看抽样结果** |

## Phase 1B：Meta / AppLovin（AppLovin 暂停）

| 序号 | 任务 | 做什么 | 需要你？ |
|---|---|---|---|
| 16 | UA-1B-M01 | 核验 Meta change log、CBO/ABO | 否 |
| 17 | UA-1B-M02 | Meta 的采集→Episode 全链路（和 Google 同一套合同，换 Meta 数据源） | 否 |
| ~ | UA-1B-A01~A02 | AppLovin 全链路 | ⏸ **暂停**（你已确认） |

## Phase 1C：PGP 三选项反馈（需要改 PGP 代码）

| 序号 | 任务 | 做什么 | 需要你？ |
|---|---|---|---|
| 18 | UA-1C-01 | 定义"继续观察/调整预算/补数据"三个选项的产品和 API 合同 | 否 |
| 19 | UA-1C-02 | 在 PGP DB 实现追加式反馈存储 + outbox | 🔔 **需要 PGP DB 变更授权** |
| 20 | UA-1C-03A | 数仓侧实现 Opportunity 只读 API | 否 |
| 21 | UA-1C-03B | PGP 侧消费数仓 Opportunity | 否 |
| 22 | UA-1C-04 | PGP 前端三选项 UI + BFF | 否 |
| 23 | UA-1C-05A | PGP outbox 安全导出合同 | 否 |
| 24 | UA-1C-04R | 🔔 PGP 统一受控发布到测试环境 | **需要你授权发布** |
| 25 | UA-1C-05B | 数仓侧 MC append-only ingestion | 否 |
| 26 | UA-1C-05R | 🔔 数仓同步发布 + 小窗口对账 | **需要你授权发布** |
| 27 | UA-1C-06 | 显式决定 → 实际操作的关联 | 否 |
| 28 | UA-1C-06R | 🔔 Operation link 受控发布 | **需要你授权发布** |
| 29 | UA-1C-07 | 端到端验收 + 标签积累启动 | 否 |

## Phase 2：案例检索 MVP

| 序号 | 任务 | 做什么 | 需要你？ |
|---|---|---|---|
| 30 | UA-P2-01 | 从成熟 Episode 生成候选案例集 | 否 |
| 31 | UA-P2-02 | 实现结构化过滤 + 数值相似度检索 | 否 |
| 32 | UA-P2-03 | 🔔 时间旅行回测 + **双人盲审** | **需要 UA/业务人工标注** |
| 33 | UA-P2-04 | 案例检索接入 Agent 只读输出 | 否 |

## Phase 3：行为模仿训练与 Shadow

| 序号 | 任务 | 做什么 | 需要你？ |
|---|---|---|---|
| 34 | UA-P3-01 | 验收是否有足够显式标签训练行为模型 | 否 |
| 35 | UA-P3-02 | 冻结基线（始终继续观察、历史多数类、规则、上一次延续） | 否 |
| 36 | UA-P3-03 | 训练行为分类模型（LightGBM/XGBoost，不是大模型） | 否 |
| 37 | UA-P3-04 | Forward/cold-start 回测 | 否 |
| 38 | UA-P3-05 | 离线 serving 安全验收 | 否 |
| 39 | UA-P3-05R | 🔔 行为模型受控发布 | **需要你授权发布** |
| 40 | UA-P3-06 | 在线静默 Shadow（只生成不展示） | 否 |

## Phase 4：Uplift 可行性

| 序号 | 任务 | 做什么 | 需要你？ |
|---|---|---|---|
| 41 | UA-P4-01 | 共同支持与干扰盘点 | 否 |
| 42 | UA-P4-02 | target-trial emulation 预注册 | 否 |
| 43 | UA-P4-03 | 匹配/AIPW/因果森林候选 | 否 |
| 44 | UA-P4-04 | 🔔 独立因果审阅 | **需要算法 Owner 审阅** |

## Phase 5：Advisor Shadow

| 序号 | 任务 | 做什么 | 需要你？ |
|---|---|---|---|
| 45 | UA-P5-01 | 组合事实+案例+风险+缺数据的 EvidenceBundle | 否 |
| 46 | UA-P5-02 | 离线评分 + CK projection + 只读 API | 否 |
| 47 | UA-P5-03 | Advisor pre-shadow 安全验收 | 否 |
| 48 | UA-P5-03R | 🔔 Advisor Shadow 受控发布 | **需要你授权发布** |
| 49 | UA-P5-04 | Prospective Shadow（只生成不展示） | 否 |
| 50 | UA-P5-05 | 🔔 安全/事实/abstain 盲审 | **需要人工盲审** |

## Phase 6：随机展示实验

| 序号 | 任务 | 做什么 | 需要你？ |
|---|---|---|---|
| 51 | UA-P6-01 | 🔔 实验预注册（随机簇、MDE、Guardrails、停止规则） | **需要业务+数据+算法共同参与** |
| 52 | UA-P6-01A | PGP 实验 assignment 埋点实现 | 否 |
| 53 | UA-P6-01B | 数仓 assignment/opportunity/outcome bridge | 否 |
| 54 | UA-P6-01AR | 🔔 PGP 实验 instrumentation 受控发布 | **需要你授权发布** |
| 55 | UA-P6-01BR | 🔔 数仓实验 bridge 受控发布 | **需要你授权发布** |
| 56 | UA-P6-02 | assignment/exposure/view dry-run | 否 |
| 57 | UA-P6-02AR | 🔔 PGP 真实试点版本受控发布 | **需要你授权发布** |
| 58 | UA-P6-02BR | 🔔 数仓真实试点 bridge 受控发布 | **需要你授权发布** |
| 59 | UA-P6-02V | 真实试点双边就绪验收 | 否 |
| 60 | UA-P6-03 | 🔔 小范围随机展示实验启动 | **需要单独人类授权 + 安全停止 Owner 在线** |
| 61 | UA-P6-04 | 等待成熟 + assignment-based ITT 分析 | 否 |
| 62 | UA-P6-05 | 🔔 人工 GO/HOLD/STOP 裁决 | **需要业务/数据/安全/算法 Owner 裁决** |

## 总结：需要你的地方只有这几类

1. **授权发布**（标 🔔 的 RELEASE_OPERATION 任务）：每次要把代码/数据发布到测试或生产环境时，需要你说一声"可以发"
2. **人工标注/盲审**：Phase 2 的案例盲审、Phase 5 的安全盲审——需要人看样本
3. **实验预注册和启动**（Phase 6）：需要业务+数据+算法共同参与
4. **PGP DB 变更**：Phase 1C 改 PGP 数据库时需要授权

**除了这些，全部我自己来。**

你过完这个清单后，回我"启动目标模式"，我就从 Phase 1A 第一个任务开始自驱推进。
