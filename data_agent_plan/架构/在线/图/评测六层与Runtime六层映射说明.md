# 评测 E1–E6 与 Runtime 架构 L1–L6 映射说明

> 命名裁决（2026-08-06）：**架构层用 L1–L6；评测层用 E1–E6**。二者不再共用「L」。
> 配图：[评测六层与Runtime六层映射图.excalidraw](评测六层与Runtime六层映射图.excalidraw)（PNG 由 `tools/scripts/export_online_diagrams.sh` 导出）。

## 先记住一句话

Runtime **架构**六层回答“**系统由谁负责**”；**评测**六层回答“**结果按什么维度判对错**”。

它们有主映射，但不是一一对应。评测层可以同时检查多个 Runtime 层；Runtime 的状态面和证据面则横跨全部层。

## 如何读图

1. 左边自上而下是 Runtime **架构 L1–L6** 的责任边界。
2. 右边自上而下是人工评测 **E1–E6** 的判错维度。
3. 实线箭头表示主要责任映射；虚线表示主要发布关系。
4. 中间两个椭圆不是“第七层”：它们分别是贯穿所有层的运行状态面和证据面。
5. 底部黄色框提示：**评测数字是时点快照**，见 `eval/question_control_e1/` 与本说明 §E1 shadow 快照；本图只表达 E↔L 映射结构。

## Runtime 架构六层：系统由谁负责

| 架构层 | 主要职责 | 不负责什么 |
|---|---|---|
| L1 交互与接入 | Web、API、鉴权、Session、SSE | 判断用户业务意图、授权 SQL |
| L2 用户问题控制 | `QuestionContract`、追问、更正、拆分 | 自行决定数据资产或 SQL 授权 |
| L3 知识控制 | route prior、Registry、检索、资产状态 | route 不能代替执行授权 |
| L4 规划与推理 | `MinimalToolLoop`、工具编排、答案综合候选 | 绕过 L5 自行执行 |
| L5 执行与安全 | binding、SQL guard、PII、预算、只读执行 | 代替 L2 定义用户问题 |
| L6 数据与知识底座 | MC/CK、表卡、语义合同、verified SQL、freshness | 宣布问题已经回答完成 |

## 评测六层 E1–E6：结果按什么判对错

| 评测层 | 主要检查 | Runtime 主映射 |
|---|---|---|
| E1 问题理解 | 必答 claim、时间、追问、更正、拆分 | 架构 L2 |
| E2 路由与授权 | route、资产状态、是否获准读取 | 架构 L3，且受 L5 binding 约束 |
| E3 数据语义与 SQL | 选表、粒度、口径、查询计划 | 架构 L3/L4/L5 |
| E4 证据覆盖 | 每个 required claim 是否有合格证据 | 证据面，涉及架构 L2/L5 |
| E5 终态裁决 | `complete` / `partial` / `failed` 是否正确 | 状态面，涉及架构 L2/L4/L5 |
| E6 回答表达 | 事实、推断、限制说明及可用性 | 架构 L4 finalizer，L1 负责展示 |

## 为什么不是一一对应

举例：评测 **E3**“SQL 粒度是否正确”不是只看一个 Runtime 模块。它需要同时检查：

- 架构 L3 提供的表卡与语义资产；
- 架构 L4 形成的查询计划；
- 架构 L5 是否允许并安全执行。

反过来，Runtime **架构 L5** 也会被多层评测覆盖：E2 看它是否阻止未授权资产，E3 看它是否阻止错误 SQL 语义，E4 看它是否留下合格执行证据，E5 看它的失败是否导致正确终态。

## E1 shadow 快照（时点数据，非架构结论）

> 以下数字来自 2026-08-06 前后本地 shadow，会随新金标与新 run 变化；**勿写入架构图**。

当前已经完成的是：

```text
82 个合成 B1 输入 × 每题 3 次重放
→ 评测 E1：57 题通过，25 题存在差异
→ Runtime 架构 L2：QuestionContract / 澄清 / 更正 / 拆分
```

（另有独立题集 `eval/question_control_e1/` 对架构 L2 / 评测 E1 做模型轨对照；晋级仍以 human 金标为准。）

这说明当前本地 Runtime 的“问题理解输出”与冻结的单人业务 reviewer 基线有 25 个待分析差异。

它**不说明**：

- Web/API、登录或 SSE 有问题；
- 路由、SQL、数据证据、终态或最终表达有问题；
- Test 或 Prod 发生过同样问题；
- 应立即修改 Runtime。

下一步应先把 25 个差异按指标、维度、时间、事件关系和终态分组，确定哪些是架构 L2 QuestionContract 的真实修复项，哪些是历史模型差异或基线仍需细化。

## 相关入口

- [Runtime 架构权威定义](../架构分层与冻结边界.md)
- [评测 E1 技术方案](../../../../eval/question_control_e1/评测E1技术方案、输入输出与优化路径.md)
- [评测 E1 跑法与产物](../../../../eval/question_control_e1/README.md)
- [分层人工评测与质量晋级计划](../../../../eval/layered_human_eval/分层人工评测与质量晋级计划.md)
- [当前 L1 shadow 报告（历史文件名，对应评测 E1）](../../../../eval/question_contract_b1/single_reviewer_shadow_report.json)
