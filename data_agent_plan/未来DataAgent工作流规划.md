# 未来 DataAgent 工作流规划

> 状态：future_architecture
> 更新时间：2026-06-18
> 范围：自然语言问题进入自研开源 DataAgent runtime 后的任务路线、门禁、执行和回写机制。
> 边界：本文件描述未来 Agent 工作方式，不定义新业务口径，不替 DA / UA / owner 拍板；路线不再评估外部代码型 Agent 作为承载框架。

## 核心判断

未来 DataAgent 不应该是“自然语言 -> 全仓 RAG -> 直接回答”，也不应该把 Text2SQL 放在最顶层。

更稳的形态是一个带门禁的工作流：

```text
用户问题
  -> 任务识别
  -> 参数补全
  -> 检索路由
  -> 语义定锚
  -> 资产选择
  -> freshness / PII / 权限 / owner gate
  -> SQL 复用或生成
  -> 执行与校验
  -> 结论生成
  -> 资产回写
```

这不是单向“从上往下读文件”，而是按任务类型动态走一条可解释路线。

## 0. runtime 方向

未来承载形态统一收敛为自研开源 DataAgent runtime。外部代码型 Agent 只能作为人工开发或调试时的外壳，不再作为产品路线、POC 路线或默认交付形态。

自研 runtime 的职责是：

- 把 `AGENT_RETRIEVAL_MAP.yaml` 编译成任务路由和 first-read 计划。
- 把 `knowledge/agent_knowledge/semantic_contract/model.json`、表卡、verified SQL 和 SOP 作为受控资产加载。
- 在执行前强制跑 freshness / PII / source / owner / raw-draft gate。
- 优先复用 verified SQL；证据不足时只生成 candidate SQL 和验证计划。
- 把 SQL 执行、sanity check、结论、风险和回写记录结构化保存。

它暂不负责：

- 自动停投、放量、降预算或修改广告平台状态。
- 让自然语言绕过表卡、语义层、verified SQL 和门禁直接生成 SQL。
- 把 raw、draft、TODO、旧 snapshot 当当前事实。

## 1. 任务识别

Agent 第一步先判断问题类型，而不是先查表。

| 类型 | 示例 | 主要路线 |
|---|---|---|
| 口径解释 | ROI360 蓝底是什么意思？ | `knowledge/` + `ai_ck/agent_knowledge/metrics/` |
| 查数分析 | BB 美国 DNU 为什么掉？ | `knowledge/agent_knowledge/semantic_contract/` + `verified_sql` + freshness + SQL |
| 诊断归因 | campaign 有消耗无回收为什么？ | SOP + verified SQL + CK / MC 对账 |
| 候选决策 | 哪些 campaign 可以放量？ | ROI 治理 policy + SQL + `needs_decision` |
| 点位 / S2S | 应推实推是否一致？ | `ai_hive/agent_knowledge/口径决策记录.md` + ready / push_log 链路 |
| 素材分析 | 素材冷启动好不好？ | 素材前端 SQL + MI 素材能力探索 |
| 报告入库 | 这份周报沉淀进工程 | docx 入库技能 + `da_assets/` |
| 工程治理 | 文件系统怎么精简？ | retrieval map + manifest + eval gates |

## 2. 参数补全

Agent 把自然语言转成任务对象。

```yaml
task_type: roi_or_campaign_analysis
product: kcolb tsalb
country: US
time_window: current_window
baseline_window: previous_window
metric: dnu
granularity: media_source
decision_intent: diagnosis
freshness_required: true
owner_decision_required: false
```

原则：

- 有 confirmed 默认口径时直接使用默认口径，并在输出里说明。
- 缺关键业务参数时才追问。
- 不把“该用哪个工具”交给用户决定；工具路由是 Agent 自己的职责。

## 3. 检索路由

Agent 先查控制面，而不是全仓全文搜索。

默认入口：

```text
AGENT_RETRIEVAL_MAP.yaml
README.md
knowledge/agent_knowledge/semantic_contract/model.json
da_assets/index.yaml
ai_hive/agent_manifest.yaml
ai_ck/agent_manifest.yaml
knowledge/agent_knowledge/catalog.yaml
knowledge/agent_knowledge/policies/第一层分析Agent协议.md
TODO/README.md
```

检索路由的目标是确定：

- 该查哪类资产。
- 哪些目录不能默认召回。
- 哪个文件是 canonical owner。
- 是否需要 freshness / PII / owner decision gate。

## 4. 语义定锚

在生成 SQL 之前，Agent 必须先确认问题中的业务词。

典型定锚问题：

- DNU、DAU、ROI、LTV、ARPU 分别用哪个指标。
- SDK 回收和 AF 回收的使用边界。
- cost / cost_zhe 的使用边界。
- organic / paid_only 是否都要输出。
- campaign 当前用 `campaign_name` 还是 `campaign_id`。
- MC / CK 是否能跨源 join，不能跨源时如何应用层对齐。

主要读取：

```text
knowledge/agent_knowledge/semantic_contract/
knowledge/agent_knowledge/policies/
ai_hive/
ai_ck/
```

## 5. 资产选择

SQL 选择优先级：

```text
verified SQL
  > SOP-guided SQL
  > semantic_contract 约束下的 Text2SQL
  > 表卡兜底 SQL
```

也就是说，Text2SQL 不是第一反应。已有 verified SQL 时，优先复用和参数化。

主要读取：

```text
da_assets/index.yaml
da_assets/verified_sql/
da_assets/analysis_sop/
da_assets/decision_cases/
```

## 6. 门禁

执行前必须过门禁。

| Gate | 作用 | 阻断行为 |
|---|---|---|
| freshness gate | 判断当前窗口能不能答 | delayed / stale 时阻断当前结论 |
| PII gate | 防止输出用户级明细和敏感字段 | 禁止 SELECT / 打印 forbidden 字段 |
| source gate | 判断走 MC、CK、MI 还是 verified SQL | 禁止无依据跨源 join |
| owner gate | 判断是否涉及停投、放量、预算等动作 | 输出 `needs_decision`，不替人决定 |
| snapshot gate | 判断材料是否为旧快照 | 标注 snapshot，不当当前事实 |
| raw/draft gate | 判断是否来自 raw / draft / TODO | 只能当线索，不当 verified 事实 |

## 7. 执行与校验

SQL 执行后，Agent 不能只贴结果，需要做基本 sanity check：

- 分区是否命中预期窗口。
- 行数是否异常为 0 或爆炸。
- 关键维度是否大量为空。
- 指标方向是否和 reference SQL / SOP 口径一致。
- 结果是否只是候选，不是业务动作。

输出必须包含：

```text
结论
证据
SQL / 资产引用
freshness 状态
数据源
置信度
风险
needs_decision
下一步
```

## 8. 资产回写

有复用价值的分析要回写资产库。

| 产物 | 回写位置 |
|---|---|
| 小窗口跑通但未稳定 | `da_assets/candidate_sql/` |
| 稳定可复用 SQL | `da_assets/verified_sql/` |
| 可复用分析流程 | `da_assets/analysis_sop/` |
| 带人类动作和后验 | `da_assets/decision_cases/` |
| 新口径 / 新规则 | `knowledge/` 或 `knowledge/agent_knowledge/semantic_contract/` |
| 新表或字段理解 | `ai_hive/` 或 `ai_ck/` |
| 待问人 / 待拍板 | `TODO/` |

回写后必须更新对应 index / manifest，并跑相关门禁。

## 当前建设路线：自底向上是正确的

当前工程走自底向上路线没有问题，而且是更稳的路线。

原因：

1. DataAgent 的上层智能依赖底层资产质量；表卡、PII、freshness、verified SQL 不稳，上层 planner 会很容易“聪明地犯错”。
2. 当前主要 blocker 不是缺外部 Agent 框架，而是 freshness、verified 覆盖、业务阈值拍板、操作日志和闭环 case。
3. 自底向上能先形成可验证地基：表卡质量、SQL 晋升、knowledge consistency、retrieval map、R1-R8 回归。
4. 等地基稳定后，自研开源 DataAgent runtime 才有清楚的输入输出契约。

推荐节奏：

```text
阶段 1：数据资产和语义底座
  ai_hive / ai_ck / semantic_contract / knowledge / verified SQL

阶段 2：检索路由和门禁
  AGENT_RETRIEVAL_MAP / manifest / index / freshness / regression

阶段 3：只读 DataAgent POC
  自研 runtime 最小闭环：任务识别 / verified SQL 复用 / Text2SQL 兜底 / 结果解释

阶段 4：闭环经验沉淀
  decision_cases / human decision / action / aftereffect / reusable rule

阶段 5：外部操作日志接入
  Google Ads / Meta change log，只读归因，不自动执行动作

阶段 6：开源发布形态
  CLI / 服务化 API / 插件式工具适配 / 本地只读部署包 / 回归门禁
```

## 不建议现在做的事

- 不把所有材料放进一个无差别 RAG 池。
- 不把 Text2SQL 作为顶层入口。
- 不把路线重新拆成外部 Agent 适配矩阵。
- 不在 freshness 阻断时硬答当前窗口问题。
- 不让 Agent 自动停投、放量、降预算。
- 不把 raw、draft、TODO、旧 snapshot 当当前事实。
- 不为了视觉清爽而大搬家。

## 验收线

未来 DataAgent 能进入只读 POC 的最低线：

- `AGENT_RETRIEVAL_MAP.yaml` 通过门禁。
- `semantic_contract` 回归通过。
- SQL 晋升门禁通过。
- 表卡质量硬错误清零。
- knowledge consistency 通过。
- R1-R8 回归至少 pass_or_blocked 达标。
- freshness blocker 被明确区分为数据新鲜度问题，而不是 Agent 路由问题。
