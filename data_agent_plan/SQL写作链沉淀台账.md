# SQL 写作链沉淀台账

> 状态：distillation_complete  
> 创建日期：2026-06-19  
> 原始输入：`<external_sql_writing_chain_package>/`  
> 原则：逐篇读、逐篇判断归属；最终知识必须沉淀到本项目既有层级，不让 Agent 依赖源包原文。

## 沉淀归属

| 内容类型 | 项目落点 | 默认召回 |
|---|---|---|
| SQL 写作流程、需求规范、场景标准化 | `knowledge/agent_knowledge/policies/` | 是 |
| 产品 / 国家 / 实验 / 小包映射 | `knowledge/agent_knowledge/policies/` 或 `knowledge/agent_knowledge/semantic_contract/` | 经 manifest 决定 |
| 表级字段、分区、query_rules、known_pitfalls | `ai_hive/agent_knowledge/tables/` 或 `ai_ck/agent_knowledge/tables/` | 表卡门禁后是 |
| 可复用 SQL | `da_assets/candidate_sql/` -> `da_assets/verified_sql/` | 仅 verified 后是 |
| 指标、维度、实体、join 契约 | `knowledge/agent_knowledge/semantic_contract/` | 回归通过后是 |
| 过宽原始埋点明细、xlsx、配置脚本 | 不入默认召回；仅作为处理输入 | 否 |

## 当前批次

| 源文档 | 处理状态 | 项目产物 | 备注 |
|---|---|---|---|
| `业务需求描述规范.md` | distilled | `knowledge/agent_knowledge/policies/SQL写作业务协议.md` | 只保留需求字段、必填项、输出规范；不保留源文档引用 |
| `SQL助手_能力逻辑说明文档.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/SQL写作业务协议.md` | 已沉淀总体流程、场景分类、验证和晋升边界；指标 SQL 仍待逐条拆分 |
| `SQL助手_思维链设计文档.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/SQL写作业务协议.md` | 已沉淀内部流程不外显、字段证据、SQL 修改流程原则 |
| `reference.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/SQL写作业务协议.md` | 已沉淀字段证据、性能门禁、分区原则；优化日志需继续拆到表卡 / runbook |
| `游戏产品名称.md` | distilled | `knowledge/agent_knowledge/policies/SQL写作业务协议.md` | 产品和端别名已进入项目协议 |
| `实验类型选择引导.md` | distilled | `knowledge/agent_knowledge/policies/SQL写作业务协议.md` | 产品实验 / 商业化实验识别已进入项目协议 |
| `国家等级映射表.md` | distilled | `knowledge/agent_knowledge/policies/国家等级映射.md` | 国家层级已独立为项目知识 |
| `核心指标定义及SQL.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/游戏核心指标口径语义.md`、`knowledge/agent_knowledge/policies/SQL写作业务协议.md` | 指标口径已沉淀；SQL 示例未晋升为 verified，后续按表卡 / schema / 小窗口验证拆分 |
| `数据表索引.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/SQL表路由协议.md`、`TODO/SQL写作链候选表准入积压清单.md` | 选表路由已沉淀；未表卡化的具体表进入 intake backlog |
| `表信息.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/SQL表路由协议.md`、`TODO/SQL写作链候选表准入积压清单.md` | 主题、粒度、表类型已沉淀为路由规则；候选表仍需表卡治理 |
| `商业化实验主题表用法.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/商业化SQL协议.md`、`knowledge/agent_knowledge/policies/白名单事件表查询协议.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀商业化链路、广告单元 join 护栏和实验汇总过滤；SQL 样例未晋升 |
| `白名单主题表使用方法.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/白名单事件表查询协议.md`、`knowledge/agent_knowledge/policies/SQL表路由协议.md` | 已沉淀白名单事件表扫描护栏、事件过滤和人群圈定规则；SQL 样例未晋升 |
| `投放主题表用法.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/投放与ROI预估SQL协议.md`、`knowledge/agent_knowledge/policies/SQL表路由协议.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀 AF 激活、成本、SDK 收入、SKAN、opt_target 和 join 边界；SQL 样例未晋升 |
| `roi预估表使用方法.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/投放与ROI预估SQL协议.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀 ROI 预估日期、周期、join 和真实 / 预估边界；SQL 样例未晋升 |
| `AB3.0实验ID提取规则.md` | distilled | `knowledge/agent_knowledge/policies/AB3实验ID提取规则.md`、`knowledge/agent_knowledge/policies/SQL写作业务协议.md` | 已沉淀 fs / rv / ba 分层提取、旧格式实验和混合实验处理；SQL 执行结果未晋升 |
| `小包unitid_final.md` | distilled | `knowledge/agent_knowledge/policies/小包广告单元映射.md`、`knowledge/agent_knowledge/policies/小包广告单元映射.csv` | 84 行 Clean Unit ID 已结构化为项目映射；保留 Package / app_name / Ad Type / Role / price_type |
| `小包广告单元UnitID与price_type映射表.md` | distilled | `knowledge/agent_knowledge/policies/小包广告单元映射.md`、`knowledge/agent_knowledge/policies/商业化SQL协议.md` | 已沉淀小包使用 Clean Unit ID 映射、禁止用 BB 配置表 price_type 替代的边界 |
| `用户行为主题表使用方法.md` | distilled | `knowledge/agent_knowledge/policies/用户行为留存画像查询规则.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀 user_multi_dim 查询边界、安装信息归一、PII 和 candidate table 边界；样例 SQL 未晋升 |
| `用户留存行为主题表使用方法.md` | distilled | `knowledge/agent_knowledge/policies/用户行为留存画像查询规则.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀全量快照、hour、业务日期、RR 分母和 SDK banner 字段边界；样例 SQL 未晋升 |
| `用户画像主题表使用方法.md` | distilled | `knowledge/agent_knowledge/policies/用户行为留存画像查询规则.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀画像 / 标签快照、latest dt / hour、app_name / area 过滤和用户明细禁止输出 |
| `block blast局粒度主题表用法.md` | distilled | `knowledge/agent_knowledge/policies/局轮出块粒度查询规则.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀局表优先、game_type、复活 / 通关 / 盘面权重字段边界；样例 SQL 未晋升 |
| `轮维度主题表用法.md` | distilled | `knowledge/agent_knowledge/policies/局轮出块粒度查询规则.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀轮表抽样、策略字段、累计字段禁止二次累加和 LAG / 差分规则 |
| `出块维度主题表用法.md` | distilled | `knowledge/agent_knowledge/policies/局轮出块粒度查询规则.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀块级下钻边界、块位 / 顺序字段和高扫描风险 |
| `BB-GP商业化埋点查询文档.md` | distilled | `knowledge/agent_knowledge/policies/BB商业化埋点查询规则.md`、`knowledge/agent_knowledge/policies/商业化SQL协议.md` | 已沉淀 GP 旧 `s_*`、新 `ad_*`、ADX / MAX 收入、banner 和竞价信息边界；参数字典未搬运为默认事实 |
| `BB-IOS商业化埋点查询文档.md` | distilled | `knowledge/agent_knowledge/policies/BB商业化埋点查询规则.md`、`knowledge/agent_knowledge/policies/商业化SQL协议.md` | 已沉淀 iOS 端字段必传性、大小写差异、load / ready / show / revenue 链路边界 |
| `实验配置主题表用法.md` | distilled | `knowledge/agent_knowledge/policies/实验配置与方案查询规则.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀配置表补元信息、分区 / app_name / Unix 时间戳、商业化 pici 前缀匹配和配置 / 效果分工 |
| `实验方案主题表用法.md` | distilled | `knowledge/agent_knowledge/policies/实验配置与方案查询规则.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀 BB / DT 实验效果表优先级、全量快照、下线实验分区、RR 与人均留存差异；SQL 样例未晋升 |
| `模型特征工程主题表使用方法.md` | distilled | `knowledge/agent_knowledge/policies/特征工程与埋点元数据查询规则.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀模型特征表用途、模型输出 / label 边界、窗口字段和 PII 风险；表卡仍需 schema probe |
| `埋点元数据表用法.md` | distilled | `knowledge/agent_knowledge/policies/特征工程与埋点元数据查询规则.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀 CS 埋点元数据表族、game_id 映射、事件 / 参数 / Hudi 字段关系；事实表 SQL 仍需验证 |
| `皇室麻将SQL代码注意事项和举例.md` | distilled | `knowledge/agent_knowledge/policies/皇室麻将BI看板查询规则.md`、`knowledge/agent_knowledge/policies/游戏核心指标口径语义.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀 MB 默认产品过滤、解析表 / 事件表 / 用户表优先级、版本和 hour 护栏；示例 SQL 未晋升 |
| `皇室麻将bi看板指标口径总说明.md` | distilled | `knowledge/agent_knowledge/policies/皇室麻将BI看板查询规则.md`、`knowledge/agent_knowledge/policies/游戏核心指标口径语义.md` | 已沉淀 MB BI 01 / 02 / 03 层关系、start_uv / install_game_join_uv、局数、收入、banner 和异常处理口径 |
| `bi看板底表01.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/皇室麻将BI看板查询规则.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀 01 层多维明细来源、白名单事件和基础指标字段；完整生产 SQL 未入 verified |
| `bi看板底表02.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/皇室麻将BI看板查询规则.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀 02 层实验配置、用户维度、国家 / 媒体 / 留存拼接边界；完整生产 SQL 未入 verified |
| `bi看板底表03.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/皇室麻将BI看板查询规则.md`、`TODO/SQL写作链候选表准入积压清单.md` | 已沉淀 03 层看板聚合维度、底板 / Bayes 指标和聚合口径；完整生产 SQL 未入 verified |
| `block gp 埋点明细.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/BB大埋点字典使用规则.md`、`knowledge/agent_knowledge/policies/BB商业化埋点查询规则.md` | 已沉淀 GP 大字典事件族、广告 / 玩法 / APM / push / 支付 / web 字段边界和 PII 风险；完整参数字典不入默认召回 |
| `block ios 埋点明细.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/BB大埋点字典使用规则.md`、`knowledge/agent_knowledge/policies/BB商业化埋点查询规则.md` | 已沉淀 iOS 大字典端差异、预置属性、IDFA / postback / request id 风险和字段验证规则；完整参数字典不入默认召回 |
| `README.md` | distilled | `knowledge/agent_knowledge/policies/SQL写作业务协议.md` | 已沉淀能力范围、需求模板、配置安全边界和维护归属；安装 Cursor Skill 的说明不进入项目运行路径 |
| `README_使用说明.md` | distilled | `knowledge/agent_knowledge/policies/SQL写作业务协议.md` | 已沉淀固定执行逻辑、字段校验、轻量 SQL 和提需求模板；同步到 Cursor 的说明不进入项目运行路径 |
| `SKILL.md` | distilled_with_boundary | `knowledge/agent_knowledge/policies/SQL写作业务协议.md`、各专项 policy | 已抽出主动指标推荐、SQL 交付节奏、MaxCompute 语法 / 性能硬门控、字段验证和 dry-run 边界；telemetry、重复规则、安装说明和内部思维链不进入默认召回 |
| `skill_meta.json` | metadata_excluded | 无 | 仅为 skill 包元数据 / system prompt 包装，内容与已沉淀规则重复；不作为项目知识来源 |
| `query_table_info.py` | runtime_excluded | `knowledge/agent_knowledge/policies/SQL写作业务协议.md` | 仅抽出 schema 查询和 EXPLAIN / LIMIT 1 dry-run 思路；本项目真实验证统一走 `maxcompute-dataworks` helper，不迁移源脚本 |
| `maxcompute_config_manager.py` | runtime_excluded | `knowledge/agent_knowledge/policies/SQL写作业务协议.md` | 仅保留“个人配置优先、本地密钥不入 git”的安全边界；不迁移配置加载代码 |
| `init_maxcompute_config.py` | runtime_excluded | 无 | 交互式个人配置初始化脚本，不进入项目知识或运行依赖 |
| `maxcompute_config.env` | template_excluded | 无 | 已确认是占位符模板；真实 AK/SK 不允许写入模板或仓库 |
| `requirements.txt` | runtime_excluded | 无 | 源包依赖清单，不进入项目依赖；本项目使用现有运行环境和 helper |
| `表信息.xlsx` | empty_excluded | 无 | 0 字节空文件；同名 md 已沉淀 |
| `数据表索引.xlsx` | empty_excluded | 无 | 0 字节空文件；同名 md 已沉淀 |
| `游戏产品名称.xlsx` | empty_excluded | 无 | 0 字节空文件；同名 md 已沉淀 |
| `国家等级映射表.xlsx` | empty_excluded | 无 | 0 字节空文件；同名 md 已沉淀 |
| `BB-GP商业化埋点查询文档.xlsx` | empty_excluded | 无 | 0 字节空文件；同名 md 已沉淀 |
| `BB-IOS商业化埋点查询文档.xlsx` | empty_excluded | 无 | 0 字节空文件；同名 md 已沉淀 |

## 源包收口结论

- `.md` 正文已逐篇沉淀到本项目 policy、backlog、映射或专项协议；大 SQL 和字段清单只作为候选线索，不直接晋升 verified。
- `.xlsx` 文件全部为 0 字节空文件，已排除。
- `.py` / `.env` / `requirements.txt` / `skill_meta.json` 只保留可迁移的安全和验证边界，不作为本项目运行依赖。
- 默认召回只使用已进入本项目的 `knowledge/`、`knowledge/agent_knowledge/semantic_contract/`、`ai_hive` / `ai_ck` 表卡和 `da_assets/verified_sql`。

## 后续治理队列（不阻塞本次源包沉淀完成）

| 优先级 | 源文档 | 目标落点 | 处理要点 |
|---|---|---|---|
| P1 | `商业化实验主题表用法.md`、`白名单主题表使用方法.md` 表卡补充 | `ai_hive/agent_knowledge/tables/` | 已完成协议沉淀；后续只补 live schema / 表卡可证实的字段、known_pitfalls 和 example_queries |
| P1 | `数据表索引.md`、`表信息.md` 候选表卡化 | `ai_hive/agent_knowledge/tables/`、`ai_hive/agent_knowledge/catalog.yaml` | 已完成路由沉淀；只对通过 schema probe 的候选表补表卡 |
| P1 | `核心指标定义及SQL.md` SQL 样例后续拆分 | `knowledge/agent_knowledge/semantic_contract/metrics.yaml`、`da_assets/candidate_sql/` | 已完成口径沉淀；只有通过字段证据和小窗口验证的 SQL 才能晋升 |
| P1 | `投放主题表用法.md`、`roi预估表使用方法.md` 表卡 / SQL 后续 | `ai_hive/agent_knowledge/tables/`、`knowledge/agent_knowledge/semantic_contract/metrics.yaml`、`da_assets/candidate_sql/` | 已完成协议沉淀；后续只补 live schema / 表卡可证实的字段和可验证 SQL |
| P1 | AB3.0 与小包广告单元 example query 后续 | `ai_hive/agent_knowledge/tables/`、`da_assets/candidate_sql/` | 规则与映射已进入项目；只有通过 schema / 小窗口验证的 SQL pattern 才能作为表卡样例或 candidate_sql |
| P1 | 用户行为 / 留存 / 画像表卡后续 | `ai_hive/agent_knowledge/tables/`、`knowledge/agent_knowledge/semantic_contract/` | 协议已完成；未进 catalog 的源表继续按 backlog 做 schema probe 和表卡 intake |
| P1 | Block Blast 局 / 轮 / 出块表卡后续 | `ai_hive/agent_knowledge/tables/`、`da_assets/candidate_sql/` | 协议已完成；候选表字段仍需 schema probe、PII、freshness、example query 和小窗口验证 |
| P1 | BB 商业化埋点字段级表卡后续 | `ai_hive/agent_knowledge/tables/`、`da_assets/candidate_sql/` | 协议已完成；字段是否列展开、JSON path、端差异和可复用 SQL 仍需小窗口验证 |
| P1 | 实验配置 / 方案表卡后续 | `ai_hive/agent_knowledge/tables/`、`da_assets/candidate_sql/` | 协议已完成；候选配置表、实验汇总表、留存表仍需 schema probe、freshness、收入单位和 example query |
| P1 | 模型特征 / 埋点元数据表卡后续 | `ai_hive/agent_knowledge/tables/`、`da_assets/candidate_sql/` | 协议已完成；特征表和 CS 元数据表仍需 schema、分区、PII、join key、Hudi 映射和 example query 验证 |
| P1 | MB 解析表 / BI 看板表卡后续 | `ai_hive/agent_knowledge/tables/`、`knowledge/agent_knowledge/semantic_contract/` | MB 协议已完成；解析表、01 / 02 / 03 层仍需 schema、分区、hour、PII、freshness、收入单位和 example query 验证 |
| P2 | MB BI 底表 SQL 拆分后续 | `da_assets/candidate_sql/`、`knowledge/agent_knowledge/semantic_contract/` | 只抽可复用小段并小窗口验证；完整生产 SQL 不直接进入 verified |
| P2 | BB 大埋点高频事件表卡 / SQL 后续 | `ai_hive/agent_knowledge/tables/`、`da_assets/candidate_sql/` | 大字典协议已完成；只对高频事件族补 event metadata、Hudi 展开列、JSON path、小窗口样本和 PII 边界 |

## 状态口径

- `distilled`：源文档已审阅，稳定业务认知已沉淀到项目内资产。
- `distilled_with_boundary`：源文档已审阅；其中未验证 SQL、过宽字段清单或需要 live schema 的内容没有直接晋升，已保留为候选边界或后续治理项。
- `empty_excluded` / `runtime_excluded` / `template_excluded` / `metadata_excluded`：源文件已审阅，但不应进入默认召回或运行依赖。

## 工作规则

- 每处理一篇源文档，都更新本台账的处理状态。
- 默认召回产物不得出现“去源包读某文件”的运行依赖。
- 涉及 `knowledge/` 变更必须同步 `knowledge/agent_knowledge/catalog.yaml` 并运行 `check_knowledge_consistency.py`。
- 涉及路由变更必须运行 `check_agent_retrieval_map.py` 和 agent regression。
