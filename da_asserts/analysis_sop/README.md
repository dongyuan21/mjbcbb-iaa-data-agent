# analysis_sop — 分析流程

本目录沉淀从 DA 报告、周报、复盘中抽取出来的分析 SOP。

## 状态边界

- SOP 说明“怎么分析”，不一定说明“最终结论是什么”。
- `draft` SOP 只能作为分析候选流程。
- 只有同时有 verified SQL / 复盘 case 支撑时，才可作为强引用。

## Agent 使用规则

1. 先读 SOP 判断分析维度、公式拆解、输出结构。
2. 再去 `../verified_sql/` 找对应 SQL。
3. 如果缺 SQL，输出 `draft_sql_needed`，不要临时编造已验证 SQL。
4. 如果 SOP 与 `ai_hive/`、`ai_ck/` 已确认口径冲突，以已确认口径为准。

## 模板

新 SOP 使用 `TEMPLATE.md`，至少写清：

- 适用场景。
- 输入指标 / 维度。
- 推荐 SQL 或缺失 SQL 状态。
- 输出结构。
- 风险和误用。
