# verified_sql — 已验证 SQL

本目录只放已通过门禁的可复用 SQL 资产。这里的 SQL 可以被 Agent 优先引用，但仍需遵守每个文件里的日期、分区和适用范围。

稳定 SQL 的晋升状态机、门禁和评估指标见 `../SQL晋升治理.md`。目录名不能替代状态；文件必须同时满足 `status: verified`、`sql_status: verified`、`promotion_status: verified_sql` 或 `semantic_promoted`，才可以被默认召回。

## 使用规则

1. 优先使用与问题最接近的 verified SQL。
2. 运行前检查 `dt` / `active_date` / `event_name` 等分区或过滤条件。
3. 不把样例日期直接当当前日期。
4. 按 `install_time` / 激活业务日期取 cohort 时，必须让 `dt` 扫描窗口覆盖 `latest_partition` 或至少 T+1，并输出 `dt_scan_window`；详见 `../analysis_sop/20260618_DNU安装时间与分区迟到护栏SOP.md`。
5. 如果需要改维度或扩大窗口，先小窗口验证。
6. SQL 输出含用户级明细时，不落盘，只保留聚合摘要。
7. 发现 draft、candidate 或 partial validated SQL 时，移动到 `../candidate_sql/` 或降级索引，不留在本目录。

## 必备章节

每个可默认召回的 SQL 文件必须包含以下二级标题，便于 Agent 和脚本稳定抽取：

- `## 口径说明`
- `## SQL`
- `## 验证记录`
- `## 风险与陷阱`

## 文件命名

| 命名 | 含义 |
|---|---|
| `vsql_YYYYMMDD_*.md` | 某日沉淀的 verified SQL |
| `*_by_*.md` | 按某维度聚合的可复用 SQL |
| `TEMPLATE.md` | 新 SQL 模板 |

## 与其他目录关系

- 原始来源放 `../raw/`。
- 未完成门禁的 SQL 放 `../candidate_sql/`。
- 分析流程放 `../analysis_sop/`。
- 产生动作和后验的复盘放 `../decision_cases/`。
- 每新增 SQL，需要更新 `../index.yaml`。
