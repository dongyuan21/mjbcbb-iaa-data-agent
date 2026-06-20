# 数仓 Agent 知识库

> 面向 Data Agent / Cursor Agent 的投放、点位、MI ROI360、MaxCompute、ClickHouse 知识工作区。
> 本目录沉淀的是 **agent 可用的语义、表卡、SQL、SOP、case、工具能力和路线图**，不是业务原始系统本身。

<!-- 自动快照：开始 -->

> 自动快照：2026-06-18；生成脚本：`python3 tools/scripts/refresh_data_agent_snapshots.py`；来源：`eval/agent_regression/Agent回归报告.md`、`semantic_model/model.json`、`da_assets/index.yaml`。

| 项 | 当前值 |
|---|---|
| 问答回归 | 通过 — 8/8 cases passed, 0 freshness-blocked, knowledge 6/6 routes 4/4 (门槛 7 pass_or_blocked) |
| 数据新鲜度门禁 | 正常 |
| 语义模型 | 11 个实体、38 个维度、50 个指标、3 条关联规则；16/16 个语义用例通过 |
| 表卡覆盖 | ai_hive 104 张表；ai_ck 20 张表；CK 精选表画像 49 份 |
| DA 资产 | 已验证 SQL 22 条；候选 SQL 1 条；决策记录 4 个；已闭环 1 个 |
| 北极星覆盖 | 约 16/35 个高频场景，概念覆盖率约 46% |

- 数据新鲜度门禁：正常

维护提示：状态数字不要手改；跑本脚本刷新。

<!-- 自动快照：结束 -->

## 建设路线

本工程当前采用自底向上的建设路线：先把数据资产、语义契约、verified SQL、SOP、freshness 和回归门禁做硬，再接上层 planner、Text2SQL、工具调用和 agent loop。

上层 Agent 不缺想象力，缺的是别让它乱想的轨道和刹车。先把地基做硬，后面接 planner、Text2SQL、工具调用会自然很多；这也是为什么本工程没有从一开始研究 agent loop 编程。

未来 DataAgent 的完整工作流见 `data_agent_plan/未来DataAgent工作流规划.md`；当前文件系统路由与默认召回边界见 `AGENT_RETRIEVAL_MAP.yaml`。

## 先读什么

| 任务 | 先读 |
|---|---|
| 判断自然语言问题该查哪些层、哪些目录不能默认召回 | `AGENT_RETRIEVAL_MAP.yaml`、`eval/Agent检索路线图报告.md` |
| 查 MaxCompute / ODPS 表、写达成率 SQL | `knowledge/policies/SQL写作业务协议.md`、`knowledge/policies/SQL表路由协议.md`、`ai_hive/README.md`、`ai_hive/口径决策记录.md` |
| 写游戏核心指标、留存、时长、局数、广告变现 SQL | `knowledge/policies/SQL写作业务协议.md`、`knowledge/policies/游戏核心指标口径语义.md`、`semantic_model/model.json` |
| 查皇室麻将 / MB 解析表、AB 看板或看板指标口径 | `knowledge/policies/皇室麻将BI看板查询规则.md`、`knowledge/policies/游戏核心指标口径语义.md`、`TODO/SQL写作链候选表准入积压清单.md` |
| 查用户行为、留存、画像 / 标签快照 | `knowledge/policies/用户行为留存画像查询规则.md`、`knowledge/policies/SQL表路由协议.md`、`ai_hive/catalog.yaml` |
| 查 Block Blast 局 / 轮 / 出块玩法细节 | `knowledge/policies/局轮出块粒度查询规则.md`、`knowledge/policies/SQL表路由协议.md`、`TODO/SQL写作链候选表准入积压清单.md` |
| 查产品实验配置、实验方案效果或组别 | `knowledge/policies/实验配置与方案查询规则.md`、`knowledge/policies/SQL写作业务协议.md`、`TODO/SQL写作链候选表准入积压清单.md` |
| 查白名单事件、商业化链路、广告单元或商业化实验 | `knowledge/policies/白名单事件表查询协议.md`、`knowledge/policies/商业化SQL协议.md`、`ai_hive/catalog.yaml` |
| 查 BB GP / iOS 商业化埋点链路 | `knowledge/policies/BB商业化埋点查询规则.md`、`knowledge/policies/白名单事件表查询协议.md`、`knowledge/policies/商业化SQL协议.md` |
| 查 BB GP / iOS 大埋点事件、参数、端差异或 PII 风险 | `knowledge/policies/BB大埋点字典使用规则.md`、`knowledge/policies/BB商业化埋点查询规则.md`、`knowledge/policies/特征工程与埋点元数据查询规则.md` |
| 查模型特征、模型输出标签、事件定义、参数定义或 Hudi 字段映射 | `knowledge/policies/特征工程与埋点元数据查询规则.md`、`knowledge/policies/白名单事件表查询协议.md`、`TODO/SQL写作链候选表准入积压清单.md` |
| 查 AB3.0 实验 ID 或小包广告单元档位 | `knowledge/policies/AB3实验ID提取规则.md`、`knowledge/policies/小包广告单元映射.md`、`knowledge/policies/小包广告单元映射.csv` |
| 查投放、AF 激活、成本、SDK 收入、ROAS / ROI 或 ROI 预估 | `knowledge/policies/投放与ROI预估SQL协议.md`、`knowledge/policies/投放ROI治理政策.md`、`ai_hive/catalog.yaml` |
| 理解当前 Text2SQL 能力和检索链路 | `data_agent_plan/Text2SQL当前能力说明.md`、`data_agent_plan/Text2SQL保守建设计划.md` |
| 写新的 Text2SQL candidate SQL | `data_agent_plan/Text2SQL保守建设计划.md`、`da_assets/Text2SQL字段证据模板.md`、`da_assets/SQL晋升治理.md` |
| 查 MI / ROI360 / ClickHouse 口径 | `ai_ck/README.md`、`ai_ck/metrics/ROI360指标语义.md` |
| 回答跨表指标、让 agent 拼 SQL | `semantic_model/model.json`、`semantic_model/README.md` |
| 做投放、ROI、DNU、素材、点位、campaign 第一层分析 | `knowledge/policies/第一层分析Agent协议.md` |
| 判断红线、黄线、冷启动、爬坡 | `knowledge/policies/投放ROI治理政策.md`、`knowledge/report_knowledge/包体ROI目标阈值.md` |
| 投喂 docx 周报 / DA 报告 / 截图附件 | `skills/docx报告入库技能/SKILL.md`、`da_assets/报告投喂规范.md`、`da_assets/报告图片处理策略.md` |
| 找可复用 SQL / SOP / 历史 case | `da_assets/README.md`、`da_assets/SQL晋升治理.md`、`da_assets/index.yaml`、`da_assets/报告证据结构.md` |
| 看近期要补、要问、要拍板的事项 | `TODO/README.md` |
| 跑回归、刷新 freshness、维护知识库 | `tools/README.md`、`eval/README.md` |

## 顶层目录

| 目录 | 定位 | Agent 默认召回 | 说明 |
|---|---|---:|---|
| `ai_hive/` | MaxCompute / Hive 表知识库 | 是 | 一表一卡、口径决策、catalog、RAG bundle |
| `ai_ck/` | ClickHouse / MI ROI360 知识库 | 是 | CK 表、MI 页面能力、ROI360 指标语义 |
| `semantic_model/` | 跨表语义模型 | 是 | 机器可读契约；`model.json` 为产物勿手改 |
| `da_assets/` | DA 报告沉淀资产 | 是，优先 verified | `raw`、`verified_sql`、`analysis_sop`、`decision_cases`、`index.yaml` |
| `knowledge/` | 已审核业务知识和分析规则 | 是 | policy、protocol、问题分类、报告分析提示、历史阈值说明 |
| `TODO/` | 近期闭环事项 | 按需 | DA/UA 问题、语义层待补、工具建设、周报问题池、远期 TODO |
| `关键问题记录/` | 工程级关键问题→整改→验证记录 | 按需 | 命名 `YYYYMMDD<主题>.md`；区别于 TODO 待办与 decision_cases 投放复盘 |
| `skills/` | 仓库本地 agent skill | 按需 | docx 报告入库、MI ROI360 分析等可执行技能说明；SQL 写作规范已沉淀到 `knowledge/policies/` |
| `tools/` | 维护脚本与运行手册 | 否/按需 | `tools/scripts` 放脚本，`tools/runbooks` 放可复跑命令说明 |
| `eval/` | 跨资产回归 | 否/按需 | Agent R 系列回归；语义模型专属回归仍在 `semantic_model/eval` |
| `data_agent_plan/` | 长远规划与阶段快照 | 否/按需 | roadmap、POC readiness、handoff、专题 gap 快照 |
| `examples/` | 未验证样例 | 否 | 可参考但不能直接当正式口径；验证后晋升到 `da_assets/verified_sql` |
| `case_studies/` | 历史专项治理案例 | 按需 | 如 `wide_hi` 血缘、审计、验证材料 |
| `raw_exports/` | 原始输入 inbox（仅本地，不纳入 git） | 否 | 公司周报、DA 报告、导出 CSV/txt、待入库材料；不直接当事实 |

> **`raw_exports/` 与 `da_assets/raw/` 仅本地归档**：已在 `.gitignore` 中排除、不纳入 git。文档、表卡、SOP、`index.yaml` 中指向这两个目录的路径均为**本地来源标注**（git 协作者需在本地查阅或重新获取），不是仓库内可达文件。

## 知识状态约定

| 状态 | 含义 | Agent 行为 |
|---|---|---|
| `verified` | 已跑通或人工核验 | 可作为默认引用 |
| `confirmed` | 业务或代码实现已确认 | 可作为口径结论 |
| `draft` | 草稿 / 初步整理 | 只能标注为候选，不当事实 |
| `candidate_sql` | SQL 已写出但未完成 verified 门禁 | 不默认召回，需先验证 |
| `validated_sql` | SQL 小窗口跑通但未成为稳定口径 | 可临时参考，不能当默认事实 |
| `semantic_promoted` | 已进入语义层或稳定诊断路径 | 可用于默认 SQL 生成路径 |
| `raw` | 原始材料 | 只能作为来源证据，需要再抽取 |
| `needs_decision` | 需要业务拍板 | 明确输出待决，不替用户决定 |
| `algorithm_pending` | 算法/模型规则待定 | 不写死阈值或动作 |

## 当前高置信口径

- MI ROI 真实段默认使用 `cost_zhe` / 折后消耗。
- MI 默认回收源跟页面默认 `revenue_source=sdk`，`af` 回收作为对照保留。
- MI 默认 CPI / LTV 分母是 `total_registers`，即 AF install / AF 侧激活。
- organic 固定输出 `all` 与 `paid_only` 两版。
- ROI360 蓝底是预估值，非蓝底才是已返回真实值。
- campaign 级 MI ROI360 当前使用 `campaign_name`，不是 `campaign_id`。
- 投放治理文档当前用于候选识别、观察名单和上会问题，不自动给最终停投/放量动作。
- 包体 ROI 红线 / 达标线已从 2026-06-16 试运行文档结构化到 `knowledge/report_knowledge/PACKAGE_ROI_TARGET_THRESHOLDS.csv`；当前为 `trial_active`，按月 review，不作为永久 confirmed 阈值。

## 不要做什么

- 不把 `raw_exports/`、`da_assets/raw/`、`knowledge/draft_knowledge/` 里的内容直接当正式事实。
- 不把蓝底 ROI360 当真实回收。
- 不从热力图、复杂多指标图截图中反推精确数值。
- 不在阈值未结构化或未确认前输出“必须停投/必须放量”。
- 不保存或输出 AK/SK、MI token、SSO ticket、数据库密码、用户级明细。
- 不用 wide 表作 安装/激活用户数分母；安装/激活用户数分母见 `ai_hive/口径决策记录.md`。

## 维护方式

| 材料 | 放到哪里 |
|---|---|
| Agent 检索路线、canonical owner、默认召回边界 | `AGENT_RETRIEVAL_MAP.yaml` |
| 新表 schema / 表口径 | `ai_hive/tables/` 或 `ai_ck/tables/` |
| MI / ROI 指标语义 | `ai_ck/metrics/` |
| 跨表实体、指标、维度、join 契约 | `semantic_model/` |
| 已审核业务规则 / 分析规程 | `knowledge/` |
| 近期待办 / 待问 DA/UA / 待拍板 | `TODO/` |
| 待晋升 SQL | `da_assets/candidate_sql/` |
| 可复用 SQL | `da_assets/verified_sql/` |
| 分析流程 | `da_assets/analysis_sop/` |
| 复盘 case | `da_assets/decision_cases/` |
| 原始公司周报、DA 报告、导出件 | `raw_exports/`，入库后归档到 `da_assets/raw/` |
| 仓库本地 agent skill | `skills/` |
| 维护脚本 / 运行手册 | `tools/scripts/`、`tools/runbooks/` |
| 非正式样例 SQL | `examples/` |
| 历史专项审计 | `case_studies/` |
| 长远路线图 / POC / handoff | `data_agent_plan/` |
