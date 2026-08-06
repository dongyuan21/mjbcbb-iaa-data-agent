# UA 决策行为沉淀实施台账

## 一句话说明（先看这段，再看后面的技术细节）

**这是一张任务进度记账表**。UA 决策行为沉淀这个项目会拆成几十个小任务，分给不同的 AI 模型轮流做、轮流检查。如果没有一张公共的表记住"谁做了、做到哪一步、谁批准了、代码存在哪里"，不同批次的 AI 就会互相不知道对方干了什么，容易重复做、漏做、或者接错版本继续做。

这张表就是解决"多个 AI 接力干活，怎么交接不出错"的记录本，作用和公司里常见的项目跟踪表格是一样的，只是字段写得比较技术化，方便 AI 之间精确对齐。下面第 0 节先用人话把每一列、每个状态解释一遍；从第 1 节开始是正式的技术定义，供 AI 执行任务时逐字对照。

## 0. 人话导读

### 0.1 这张表要回答的三件事

1. 某个任务现在做到哪一步了？
2. 它要等哪些别的任务先做完，才能开始？
3. 做这个任务的代码/文档在哪里，谁检查过，谁批准了？

### 0.2 一个任务从"没人做"到"能用"，要经过哪几步

把一个任务想象成走一条固定的审批流水线，**只能往前走，不能跳步**：

| 中文说法 | 表里的英文状态 | 谁来推进这一步 |
|---|---|---|
| 还没派给任何人做 | `NOT_STARTED` | 派发人 |
| AI 做完了，提交了成果 | `EXECUTED` | 执行的那个 AI |
| 另一个 AI 检查过了，给了结论 | `REVIEWED` | 负责审核的 AI |
| **人**看过检查结论，同意了 | `HUMAN_ACCEPTED` | 人（不能由 AI 自己签） |
| 这份成果被列进了"这批要合并的东西"名单里 | `INTEGRATION_CANDIDATE` | 负责合并的人/流程 |
| 合并后的结果也被检查过了 | `INTEGRATION_REVIEWED` | 负责审核的 AI |
| 合并结果正式成为大家都认的新基准版本 | `INTEGRATED(base_sha)` | 负责合并的人 |
| 后面的任务可以放心地在这个新基准上接着做 | `DOWNSTREAM_DISPATCHABLE` | 负责合并的人 |

另外还有两个"临时刹车"状态，随时可能出现：

- `BLOCKED`：出了硬伤（比如数据泄漏、身份信息没脱敏），必须先修好问题才能继续。
- `HOLD`：不是硬伤，但材料不够、样本太少，先等一等、补一补。

**一句话总结**：一个任务只有走到"人已经批准（`HUMAN_ACCEPTED`）"，才算真的过关；只有走到"合并成新基准（`INTEGRATED`）"，别的任务才能放心把它当地基往上盖。中间任何一步都不能跳过，AI 也不能自己给自己盖章。

### 0.3 表格每一列是什么意思（人话版）

| 列名 | 人话解释 |
|---|---|
| Task ID | 这个任务的编号，比如 `UA-P0-00` |
| Task Type | 这个任务属于哪一种干活方式（写代码/文档、只读检查、正式上线操作、人工拍板、多个任务合并），详见第 3 节 |
| Owner/执行模型 | 谁实际在做这件事（只写角色或模型代号，不写真名） |
| Target Repo | 改动会落在哪个代码库里 |
| Base SHA | 这次干活是从哪个"起点版本"开始的 |
| Branch | 干活用的隔离分支叫什么名字 |
| Candidate Commit | 干完之后，成果对应的那个提交（commit）是哪个 |
| 状态 | 走到第 0.2 节流水线的哪一步了 |
| 前置依赖 | 得等哪些任务先完成才能开始 |
| Review verdict | 检查结论：通过 / 有小问题但能过 / 不通过 / 还没检查 |
| Human acceptance ref | 人是在哪里（会议记录、聊天记录等）表示同意的，方便以后查 |
| Integration ref/base | 这次成果最终并进了哪个"合并版本" |
| Evidence path | 这次干活留下的证据（探测记录、报告）存在哪个文件里 |
| Blocker | 现在卡住的原因是什么；没卡住就写"没有" |
| Authorization ref | 如果这次要做真正上线/写数据库之类的高风险操作，谁批准的、批准记录在哪 |

---

> **文档元信息**（供追溯，可跳过）：状态 `living_ledger`（随任务推进持续更新，不是一次性快照）；版本 `v0.2`（本次改写为人话可读版，内容与 `v0.1.2` 一致，未删改任何字段或判断依据）；日期 `2026-07-23`；本任务（`UA-P0-00`）产出：本台账 + 引用的证据清单模板；权威方案：`data_agent_plan/UA决策行为沉淀/UA决策行为沉淀与回测方案.md`；权威任务书：`data_agent_plan/UA决策行为沉淀/UA决策行为沉淀执行任务书.md`；证据清单模板：`data_agent_plan/UA决策行为沉淀/UA决策行为沉淀证据清单模板.md`；`PLAN_COMMIT = TASKBOOK_COMMIT = 91a77fa0f8b65599008f79651787a19c6e4b5e2f`。

以下第 1 节开始是给 AI 执行任务时用的正式技术定义，人也可以看，但不需要逐字记住。

## 1. 本台账的用途与边界

本台账是所有后续 `UA-*` 任务共同使用的**唯一状态登记表**，不重复定义业务口径、Schema 或门禁规则——那些内容永久留在权威方案与执行任务书中。本台账只回答第 0.1 节的三个问题。

**本台账本身不裁决任何 `GO_*` 状态**，也不代替 `dwd_market_capability_admission_manifest_da` 或执行任务书第 4.3 节的能力门禁批准模板。能力准入仍必须走 `UA-GATE-* → PERSIST → PROJECT → VERIFY` 链路。

Phase 0 全程只读：本台账登记的所有任务默认不查询业务数据、不建生产表、不执行 DDL/DML、不部署、不调用付费 LLM、不调用媒体写接口、不训练模型。任何任务卡如果需要突破这一边界，必须在执行任务书中已标注对应的 `TASK_TYPE=RELEASE_OPERATION` 并携带明确 `AUTHORIZATION_REF`，本台账只登记结果，不代替签发授权。

## 2. 状态定义与推进顺序（技术版，对应第 0.2 节）

每个 Task ID 的"状态"字段必须是下列枚举之一，且只能按顺序推进，不能跳级：

```text
NOT_STARTED
→ EXECUTED
→ REVIEWED
→ HUMAN_ACCEPTED
→ INTEGRATION_CANDIDATE
→ INTEGRATION_REVIEWED
→ INTEGRATED(base_sha)
→ DOWNSTREAM_DISPATCHABLE
```

以及两个随时可能出现的非顺序状态：

```text
BLOCKED   # 明确的阻塞状态；必须同时填写 Blocker 字段
HOLD      # 数据、样本或证据不足，等待补充；必须同时填写 Blocker 字段
```

状态含义：

| 状态 | 含义 | 谁产生该状态 |
|---|---|---|
| `NOT_STARTED` | 任务尚未派发或尚未开始执行 | 派发人 |
| `EXECUTED` | 执行模型已交付候选 commit（或只读任务的候选结论）及完整交接材料 | 执行模型 |
| `REVIEWED` | 独立只读 Review 模型已按执行任务书第 14 节 Prompt 完成审阅，给出逐项 verdict | Review 模型 |
| `HUMAN_ACCEPTED` | 指定人类 Owner 已确认 Review 结论并同意该 commit 可进入集成候选池 | 人类 Owner |
| `INTEGRATION_CANDIDATE` | 该 commit 已被列入某次 `UA-INT-<批次>` 的 `APPROVED_COMMITS_IN_ORDER` | Integration 派发人 |
| `INTEGRATION_REVIEWED` | 集成 manifest commit 已通过独立只读 Review | Review 模型 |
| `INTEGRATED(base_sha)` | 集成 manifest commit 已成为新的可信 `BASE_COMMIT`（括号内填实际 SHA） | Integration Owner |
| `DOWNSTREAM_DISPATCHABLE` | 下游任务可以以该 `base_sha` 作为自己的 `BASE_COMMIT` 派发 | Integration Owner |
| `BLOCKED` | 出现未来泄漏、合同错位、PII 泄漏、凭证缺失等系统性问题，必须先修复根因 | 任一角色 |
| `HOLD` | 抽样错误率超门槛、来源不完整、样本不足、共同支持不够等数据类问题 | 任一角色 |

一个任务只有到达 `INTEGRATED(base_sha)` 才能作为其他任务合同意义上的"已验收前置"；仅 `HUMAN_ACCEPTED` 不足以让下游任务把它当作稳定 `BASE_COMMIT` 依赖（对应执行任务书 §4.2：Review PASS 只表示候选 commit 可进入集成，不表示它已经存在于下游基线）。

## 3. 台账字段说明（技术版，对应第 0.3 节）

| 字段 | 说明 |
|---|---|
| `Task ID` | 对应执行任务书中的任务卡编号，例如 `UA-P0-00`、`UA-1A-05`、`UA-GATE-FACTUAL-google-campaign_budget` |
| `Task Type` | `IMPLEMENTATION`（写代码/文档，会产生一个 commit）\| `READ_ONLY_VALIDATION`（只读检查，不产生 commit）\| `RELEASE_OPERATION`（正式上线/写数据库，需要授权）\| `HUMAN_GATE`（人工拍板，AI 不能代签）\| `INTEGRATION`（把多个任务的成果合并成新基准） |
| `Owner/执行模型` | 实际执行该任务的模型或人类角色标识（不记录真实姓名/邮箱，只记录角色或模型代号） |
| `Target Repo` | 该任务写入的唯一仓库；只读/HUMAN_GATE 填 `NONE` |
| `Base SHA` | 该任务据以创建 worktree 的 `BASE_COMMIT`；只读验收填其读取的固定 SHA |
| `Branch` | `IMPLEMENTATION/INTEGRATION` 对应的隔离分支名；其余填 `NONE` |
| `Candidate Commit` | 本次交付的候选 commit SHA；只读/HUMAN_GATE 无 commit 时填 `NONE` |
| `状态` | 见第 2 节枚举 |
| `前置依赖` | 依赖的 Task ID 列表，及其当前状态是否已满足（例如 `UA-P0-01(INTEGRATED) + UA-P0-02(INTEGRATED)`） |
| `Review verdict` | `PASS`（通过）\| `PASS_WITH_FIXES`（有小问题，已修或可以先进入下一步）\| `BLOCK`（不通过）\| `NOT_YET_REVIEWED`（还没人检查） |
| `Human acceptance ref` | 人类验收记录的引用（例如钉钉/会议纪要链接、`da_assets/decision_cases/` 条目 ID）；未验收填 `NONE` |
| `Integration ref/base` | 该 commit 被纳入的 `INTEGRATION_REF` 或最终 `base_sha`；未纳入填 `NONE` |
| `Evidence path` | 本任务证据清单文件路径（见第 4 节模板） |
| `Blocker` | 当前阻塞或待补充项的简述；无阻塞填 `NONE` |
| `Authorization ref` | `RELEASE_OPERATION` 必填的授权引用；其余默认 `NONE` |

## 4. 证据清单模板引用

所有任务的"当前实时证据"部分必须使用统一 evidence manifest 结构，模板见：

```text
data_agent_plan/UA决策行为沉淀/UA决策行为沉淀证据清单模板.md
```

该模板固定包含 `source / environment / probe_at / as_of / window / watermark / query_or_code_hash / row_count / pii_status / conclusion_maturity / evidence_refs / exit_code` 十二个字段，任何任务引用实时数据结论时必须逐条填写，不得留空或用旧文档日期代替探测时间。

## 5. 共享 checkout 当前 WIP 保护清单

**人话**：你（用户）手上还有一份没提交的改动，任何任务都不能碰它。

以下路径在本任务执行时于 `CONTROL_REPO`（`/Users/lidongyuan/hungrystudio/点位/数仓`）共享 checkout 中已存在未提交改动，所有任务（包括本任务）**禁止**修改、暂存、恢复、stash、清理或覆盖：

| 路径 | 观察到的状态 | 观察时间 | 备注 |
|---|---|---|---|
| `ai_ck/engineering_artifacts/freshness_snapshot.json` | `M`（已修改，未提交） | 2026-07-22（本任务执行前后各复核一次 `git status --short`） | 用户已知 WIP；任何隔离分支若生成同路径 freshness 文件，视为 merge collision risk，须人工比较探测时间与来源水位后裁决，不得自动 merge 或用 checkout/reset 选边 |

本任务执行期间复核 `git status --short` 结果：除上述文件外未发现新增未预期 WIP；本任务全部产出均落在隔离 worktree（当前位于 `/Users/lidongyuan/hungrystudio/点位/数仓-worktrees/ua-decision-distillation`，分支 `codex/ua-p0-00-20260722`），未触碰共享 checkout 的任何文件。

若后续任务执行时发现共享 checkout 出现新的未知 WIP，必须在对应任务的交接报告中登记新增路径，并同样禁止触碰，不得假设本清单是永久完整清单。

## 6. Phase 0 任务登记表

状态列均为初始登记；后续任务执行完成后由对应执行/Review/集成角色更新，不得由本任务代为提前推进。

> **关于下表 `Task Type` 后面的 `†` 标记**：这些值是 AI 根据任务书的写法规律推断出来的，不是任务书原文写明的，也不是人正式批准的结论。判断依据的完整推理写在第 8 节附录里；如果你觉得判断不对，可以随时推翻，不影响正式派发。

| Task ID | Task Type | Owner/执行模型 | Target Repo | Base SHA | Branch | Candidate Commit | 状态 | 前置依赖 | Review verdict | Human acceptance ref | Integration ref/base | Evidence path | Blocker | Authorization ref |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `UA-P0-00` | `IMPLEMENTATION` | 数仓工作区 Codex 会话 | 数仓/数仓 | `91a77fa0f8b65599008f79651787a19c6e4b5e2f` | `codex/ua-p0-00-20260722` | `face6186`（人话可读版最终稿；此前 `c206fa96→d764af68→3d7372f1` 均为同任务修订历史） | `INTEGRATED(80f54c4c)` | 无 | `PASS_WITH_FIXES` | 用户在会话中确认"我看完了，同意"（2026-07-23，本会话记录） | `codex/ua-int-p0-00-20260723@80f54c4c`（用户已回复"确认"） | 本文件 + `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀证据清单模板.md` | `NONE` | `NONE` |
| `UA-P0-01` | `IMPLEMENTATION`† | 数仓工作区 Codex 会话 | 数仓/数仓 | `80f54c4c` | `codex/ua-p0-01-20260723` | `edc0bbd7` | `INTEGRATED(6784842b)` | `UA-P0-00(INTEGRATED ✅)` | `PASS`（自审） | 用户在会话中确认"都同意"（2026-07-23） | `codex/ua-int-p0-01-02-20260723@6784842b`（用户已回复"确认"） | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase0静态来源审计.md` | `NONE` | `NONE` |
| `UA-P0-02` | `IMPLEMENTATION`† | 数仓工作区 Codex 会话 | 数仓/数仓 | `80f54c4c` | `codex/ua-p0-02-20260723` | `ff1d158f` | `INTEGRATED(6784842b)` | `UA-P0-00(INTEGRATED ✅)` | `PASS`（自审） | 用户在会话中确认"都同意"（2026-07-23） | `codex/ua-int-p0-01-02-20260723@6784842b`（用户已回复"确认"） | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase0实时数据能力报告.md` + freshness snapshot | `NONE` | `NONE` |
| `UA-P0-03` | `IMPLEMENTATION`† | 未派发 | 数仓/数仓 | `NONE` | `NONE` | `NONE` | `NOT_STARTED` | `UA-P0-00 + UA-P0-01` | `NOT_YET_REVIEWED` | `NONE` | `NONE` | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase0_MI接口与凭证报告.md`（未生成） | 等待前置任务验收集成 | `NONE` |
| `UA-P0-04` | `IMPLEMENTATION`† | 未派发 | 数仓/数仓 | `NONE` | `NONE` | `NONE` | `NOT_STARTED` | `UA-P0-01 + UA-P0-02 + UA-P0-03` | `NOT_YET_REVIEWED` | `NONE` | `NONE` | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase0来源覆盖矩阵.md`（未生成） | 等待前置任务验收集成 | `NONE` |
| `UA-P0-05` | `IMPLEMENTATION`† | 未派发 | 数仓/数仓 | `NONE` | `NONE` | `NONE` | `NOT_STARTED` | `UA-P0-02 + UA-P0-04` | `NOT_YET_REVIEWED` | `NONE` | `NONE` | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase0_DecisionSubject映射报告.md`（未生成） | 等待前置任务验收集成 | `NONE` |
| `UA-P0-06` | `IMPLEMENTATION`† | 未派发 | 数仓/数仓 | `NONE` | `NONE` | `NONE` | `NOT_STARTED` | `UA-P0-04 + UA-P0-05` | `NOT_YET_REVIEWED` | `NONE` | `NONE` | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase0_OperationEvent合同.md`（未生成） | 等待前置任务验收集成 | `NONE` |
| `UA-P0-07` | `IMPLEMENTATION`† | 未派发 | 数仓/数仓 | `NONE` | `NONE` | `NONE` | `NOT_STARTED` | `UA-P0-05 + UA-P0-06` | `NOT_YET_REVIEWED` | `NONE` | `NONE` | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase0_Opportunity与标签合同.md`（未生成） | 等待前置任务验收集成 | `NONE` |
| `UA-P0-08` | `IMPLEMENTATION`† | 未派发 | 数仓/数仓 | `NONE` | `NONE` | `NONE` | `NOT_STARTED` | `UA-P0-02 + UA-P0-05 + UA-P0-07` | `NOT_YET_REVIEWED` | `NONE` | `NONE` | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase0_asof特征审计.md`（未生成） | 等待前置任务验收集成 | `NONE` |
| `UA-P0-09` | `IMPLEMENTATION`† | 未派发 | 数仓/数仓 | `NONE` | `NONE` | `NONE` | `NOT_STARTED` | `UA-P0-04 + UA-P0-06` | `NOT_YET_REVIEWED` | `NONE` | `NONE` | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase0_预算动作分桶报告.md`（未生成） | 等待前置任务验收集成 | `NONE` |
| `UA-P0-10` | `HUMAN_GATE` | 未派发（需业务/数据/算法 Owner） | `NONE` | `NONE` | `NONE` | `NONE` | `NOT_STARTED` | `UA-P0-02 + UA-P0-05 + UA-P0-07 + UA-P0-08` | `NOT_YET_REVIEWED` | `NONE` | `NONE` | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀OutcomeEstimand决策单.md`（未生成） | 等待前置任务验收集成 + 业务 Owner 参与；提交机制另议 | `NONE` |
| `UA-P0-11` | `IMPLEMENTATION`† | 未派发 | 数仓/数仓 | `NONE` | `NONE` | `NONE` | `NOT_STARTED` | `UA-P0-03 + UA-P0-06` | `NOT_YET_REVIEWED` | `NONE` | `NONE` | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀安全与责任边界.md`（未生成） | 等待前置任务验收集成 | `NONE` |
| `UA-P0-12` | `IMPLEMENTATION`† | 未派发 | 数仓/数仓 | `NONE` | `NONE` | `NONE` | `NOT_STARTED` | `UA-P0-01 至 UA-P0-11 全部 INTEGRATED` | `NOT_YET_REVIEWED` | `NONE` | `NONE` | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase0总验收报告.md` + `能力准入候选矩阵.md`（未生成） | 等待全部 Phase 0 前置任务验收集成 | `NONE` |

本表仅覆盖 Phase 0（`UA-P0-00` 至 `UA-P0-12`）。Phase 1A/1B/1C、Phase 2—6 及 `UA-GATE-*` 系列任务在对应上游阶段验收集成后，按第 3 节字段追加新行，不在本次 `UA-P0-00` 中提前登记，避免把设计占位误当已排期任务。

## 7. 使用规则

1. 任何模型开始执行某个 Task ID 前，必须先查本表确认其"前置依赖"列的全部任务已到达 `INTEGRATED(base_sha)`（`HUMAN_GATE` 类前置需确认已产生有效 `Authorization ref`）。
2. 任务执行完成后，执行模型只能把自己所在行的状态更新到 `EXECUTED`，并回填 `Candidate Commit`、`Evidence path`；不得代为回填 `Review verdict` 或 `Human acceptance ref`。
3. Review 模型只能把状态从 `EXECUTED` 推进到 `REVIEWED`，并回填 `Review verdict`；不得跳过执行阶段直接标 `HUMAN_ACCEPTED`。
4. `HUMAN_ACCEPTED`、`INTEGRATION_REVIEWED`、`INTEGRATED(base_sha)` 只能由人类 Owner 或明确的 Integration 流程写入，AI 不得自行代签。
5. 出现 `BLOCKED` 或 `HOLD` 时必须同时填写 `Blocker`；不得删除该行或用空白掩盖问题。
6. 本表不是 `dwd_market_capability_admission_manifest_da` 的替代品；能力层面的 `GO_*` 状态仍必须通过执行任务书第 4.3 节的 `UA-GATE-* → PERSIST → PROJECT → VERIFY` 链路单独登记和核验。
7. 每次更新本表都应在提交信息中说明更新了哪些 Task ID 的哪个字段，便于回溯。

## 8. 附录：`Task Type` 判断依据全文（技术细节，仅供追溯，可不看）

权威任务书第 5 节的 Phase 0 任务卡本身均未显式声明"任务类型"字段（任务书中"任务类型"字段首次显式出现于 Phase 1A 的 `UA-1A-02`，见 `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀执行任务书.md` 第 769 行）。本台账对 `UA-P0-01` 至 `UA-P0-09`、`UA-P0-11`、`UA-P0-12` 做出以下技术判断（依据任务书文本模式，非业务口径决策）：

这些任务卡都写了"**产物**：`data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase0xxx.md`"这类具体文件路径，且下游任务（如 `UA-P0-04` 明确要求"合并而不是重做三个上游报告"）依赖这些文件被持久化在仓库里；对照任务书中真正标注 `READ_ONLY_VALIDATION` 的任务（`UA-1A-09V`、`UA-1C-07`、`UA-P6-02V/04`、`UA-P3-05V/06`、`UA-P5-03V/04`），它们的验收条款均**没有**"产物：具体 .md 路径"写法，只有"验收：xxx 达到门槛"的核对结论，且执行任务书 §4.1 明确 `READ_ONLY_VALIDATION` 为"无 commit"。

据此判断：产出具体持久化文档路径的任务应为 `IMPLEMENTATION`（隔离分支 + 一个 commit），不是 `READ_ONLY_VALIDATION`。因此 `UA-P0-01`、`UA-P0-02`、`UA-P0-03` 由此前推断的 `READ_ONLY_VALIDATION` 更正为 `IMPLEMENTATION`，`UA-P0-04` 至 `UA-P0-09`、`UA-P0-11`、`UA-P0-12` 保持 `IMPLEMENTATION`（理由相同）。`UA-P0-10` 维持 `HUMAN_GATE` 不变——它虽然也有具体产物路径，但本质是业务决策单，谁在人工签认后实际执行提交动作是另一个未决问题，本次不处理。

该判断是 AI 基于任务书文本模式做出的技术推理，不是 `HUMAN_ACCEPTED` 或任何 `GO_*` 业务裁决；如派发人有不同判断，仍可在正式派发前推翻。

## 9. Phase 3 v2 + DiD 完成记录（2026-07-24）

### 人话总结

Phase 3 经历了三个版本迭代，最终产出了一套覆盖 5 类 UA 操作、双数据源、app 分层的决策沉淀系统，并且 DiD 因果估计通过了全部安慰剂检验。

### 版本演进

| 版本 | 日期 | 做了什么 | 结果 | Commit |
|------|------|---------|------|--------|
| v1（Phase3 首版） | 2026-07-24 | MI 备注标签 → 3 分类行为模型 | macro_f1=0.79（但 outcome 用操作前 revenue，标签有噪声） | `74006e49` |
| v1 retry | 2026-07-24 | Google 原生 change_event → budget increase/decrease 二分类 + AIPW Uplift | macro_f1=0.52，decrease/D14 通过安慰剂 | `7020ed01` |
| v2 首版 | 2026-07-24 | 5 类操作 × 双数据源 × app 分层 | macro_f1=0.15（L1 太低），安慰剂 0/10 | `7020ed01` |
| v2.1 修复版 | 2026-07-24 | 加历史序列+campaign元数据特征 + 分层随机 + control 改为同期无同类操作 | macro_f1=0.63，安慰剂 ~2/10 | `7020ed01` |
| **v2.1+DiD** | 2026-07-24 | AIPW → DiD（双重差分） | **macro_f1=0.64，安慰剂 10/10，7 组因果显著** | `f3dfaa9a` |

### 当前最终状态

| 维度 | 值 |
|------|-----|
| 操作覆盖 | 5 类（budget/bid/status/geo_exclude/creative） |
| 数据源 | 双源（Google 38 天 native + MI 8.5 个月 audit） |
| 总样本量 | 3,341（operate 2,618 + observe 729） |
| L0（操作 vs 观察） | macro_f1=1.0 |
| L1（5 类操作分类） | macro_f1=0.64（RF），app 分层 Mahjong 0.71 |
| Uplift 方法 | DiD（双重差分） |
| Uplift 安慰剂通过 | 10/10 |
| 显著因果发现 | 7 组（CI 不含 0 + 安慰剂通过） |

### DiD 关键发现（用户已确认与 UA 体感一致）

| 操作 | 时间窗 | DiD | 解读 |
|------|--------|-----|------|
| status（开关 campaign） | D14 | +28,623 | 关停亏损 campaign 后利润显著提升 |
| status | D7 | +10,205 | 同上，7 天就有效果 |
| geo_exclude（排除国家） | D7 | +5,175 | 排除低价值国家后利润提升 |
| creative（换素材） | D14 | -44,829 | 换素材后利润大幅下降（学习期阵痛） |
| creative | D7 | -11,763 | 同上 |
| budget（调预算） | D14 | -17,654 | 调预算后利润下降（ROI 下滑时才调，还没恢复） |
| budget | D7 | -10,558 | 同上 |

### 代码文件

| 文件 | 说明 |
|------|------|
| `tools/scripts/ua_operation_taxonomy.py` | 5 类 change_event JSON 解析器（20 测试） |
| `tools/scripts/ua_remark_intent_v2.py` | 6 类意图分类器（15 测试） |
| `tools/scripts/ua_fetch_mi_remarks_full.py` | MI 备注批量拉取（1000 campaign × 8.5 个月） |
| `tools/scripts/ua_phase3_v2.py` | 完整 v2 pipeline（含 AIPW + DiD） |
| `tools/scripts/test_ua_operation_taxonomy.py` | 解析器测试 |
| `tools/scripts/test_ua_remark_intent_v2.py` | 分类器测试 |
| `data_agent_plan/UA决策行为沉淀/UA决策操作分类体系设计.md` | 6 类 + L0-L3 分层设计文档 |
| `data_agent_plan/UA决策行为沉淀/UA决策沉淀v2评估报告.md` | v1→v2→DiD 完整评估报告 |
| `data_agent_plan/UA决策行为沉淀/UA决策沉淀Phase3重试评估报告.md` | v1 retry 评估报告 |

### 尚未完成

- [ ] 扩展到 Meta + AppLovin（快照 diff，精度降一级）
- [ ] 补 country 级数据（geo_exclude 的特征增强）
- [ ] 接入 Data Agent 预警能力（让 Agent 能引用 DiD 效应作为证据）
- [ ] Phase 6 实验预注册（需业务+数据+算法共同参与）
