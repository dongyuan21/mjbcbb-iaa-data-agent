# da_assets — DA 报告与 SQL 沉淀区

> 目标：把 DA 的钉钉 docs、HTML、SQL、分析结论转成 agent 可复用的 verified SQL、分析 SOP 和决策 case。
>
> **与 `knowledge/` 的边界**：`da_assets/` 是"蒸馏管线+过程产物"，`knowledge/` 是"已确认事实基座"。
> - 规则逻辑、数值数据的唯一权威写入点在 `knowledge/`（policies/、report_knowledge/）。
> - 可复跑 SQL、分析流程、事件快照、原始材料的唯一权威写入点在 `da_assets/`。
> - 每个事实的各切面权威写入点见 `knowledge/agent_knowledge/authority_map.yaml`。
> - `decision_cases/` 中闭环且被确认为长期事实的结论应晋升到 `knowledge/`，本目录只保留过程记录。
> - `verified_sql/` 不向 `knowledge/` 晋升，可信度由 SQL 晋升门禁保证。

## 目录

```text
da_assets/
  raw/                 # 原始材料：钉钉导出、HTML、截图说明、原 SQL；见 raw/README.md
  candidate_sql/       # 已写出但未完成 verified 门禁的待晋升 SQL
  verified_sql/        # 经校验可复用 SQL；见 verified_sql/README.md
  analysis_sop/        # 从报告抽出的分析流程；见 analysis_sop/README.md
  decision_cases/      # 结论、动作、后验结果；见 decision_cases/README.md
  index.yaml           # 资产索引
  SQL晋升治理.md # 稳定 SQL 晋升状态机、门禁和指标
  （报告产物见 eval/sql_promotion/SQL晋升指标报告.md） # 自动生成的晋升指标和候选清单
  报告投喂规范.md # 周报 / DA 报告 / 截图附件投喂规范
  报告图片处理策略.md # 图片分级、OCR 边界和不可解析图处理规则
  报告证据结构.md   # 报告证据、置信度和引用结构
```

## 使用流程

0. 如果来源是 docx 周报 / DA 报告，先执行 `../skills/docx报告入库技能/SKILL.md`。
1. 原始文件放入 `raw/`，文件名建议：`YYYY-MM-DD_主题_来源.ext`。
2. 按 `报告投喂规范.md` 记录来源、周期、MCP 读取状态和图片依赖。
3. 按 `报告图片处理策略.md` 判断图片是可 OCR 表格、只读趋势图，还是只归档热力图。
4. 从报告中抽取问题、结论、指标、维度、图表逻辑，写入 `analysis_sop/`。
5. 从 DA SQL 中抽取可复用查询；未验证时先写入 `candidate_sql/`，通过 `SQL晋升治理.md` 门禁后再晋升到 `verified_sql/`。
6. 如果报告产生了投放动作，把动作和后验结果写入 `decision_cases/`。
7. 每新增一份资产，更新 `index.yaml`。

## 钉钉 MCP 读取边界

- 钉钉在线文档 `adoc` 可通过 MCP 读取 Markdown 正文和表格。
- 文档中的图片通常会以 Markdown 图片链接或 `unknown` kcolb 出现；这只能证明“这里有图”，不能证明图中数值已经被读取。
- 不要把带 `Signature`、`OSSAccessKeyId`、`Expires` 的图片链接落入长期知识库。需要使用图片内容时，先单独下载图片并人工/视觉复核，再把复核结果写成结构化文字。
- `raw/` 中必须标注 `mcp_read_status` 和 `image_status`，避免 agent 把未 OCR 的图片内容当成已验证事实。
- 高密度热力图、多指标统计图默认不 OCR；需要原始矩阵或图表数据时，标 `charts_need_source_data` 或 `dense_images_archive_only`。

## SQL 使用状态

SQL 晋升状态机、门禁和评估指标见 `SQL晋升治理.md`。目录名不能替代状态；只有 `promotion_status`、`status` 和 `sql_status` 均达到 verified 级别的 SQL，才能被 Agent 默认召回。

`verified_sql/` 只放可复用 SQL。报告中只有方法论、没有 SQL 时，不要补造 SQL，先在 `index.yaml` 标记：

| status | 含义 |
|---|---|
| `missing_source_sql` | 来源报告没有直接可复用 SQL。 |
| `draft_sql_needed` | 需要按 SOP 另写 SQL，尚未验证。 |
| `copied_unverified` | 已从来源复制 SQL，但未执行验证。 |
| `copied_partial_validated` | 已做轻量聚合或结构验证，但未达到稳定复用标准。 |
| `verified` | SQL 已带日期/分区过滤执行，输出经过 review。 |

只有 `promotion_status: verified_sql` / `semantic_promoted` 且 `sql_status: verified` 的 SQL 才能作为 Agent 默认 reference SQL。

## 目录状态边界

| 目录 | 默认可信度 | 使用方式 |
|---|---|---|
| `verified_sql/` | 高 | 仅放 verified 级 SQL；可默认引用，但要检查日期和过滤条件 |
| `candidate_sql/` | 低到中 | 待验证 SQL；只作候选，不默认召回 |
| `analysis_sop/` | 中 | 用于分析流程；若缺 SQL 要标 `draft_sql_needed` |
| `decision_cases/` | 视状态而定 | 只有闭环 case 才能作为历史证据 |
| `raw/` | 低 | 只作来源材料，不直接当结论 |

## 安全规则

- 不保存 AK/SK、MI token、SSO ticket、数据库密码。
- SQL 结果如果包含用户级明细或 PII，不落盘；只记录聚合结果摘要。
- 原始 docs/html 如果含敏感人名或业务策略，可先脱敏后再进入 agent 上下文。

## Agent 使用规则

Agent 回答投放复盘问题时优先召回：

1. `报告投喂规范.md`、`报告图片处理策略.md`、`报告证据结构.md` 中的报告读取边界。
2. `SQL晋升治理.md` 中的 SQL 晋升门禁和默认召回规则。
3. `verified_sql/` 中同类问题的已验证 SQL。
4. `analysis_sop/` 中同类复盘流程。
5. `decision_cases/` 中历史动作与后验。
6. 最后才临时生成新 SQL；生成后先进入 `candidate_sql/`，不能直接当 verified SQL。
