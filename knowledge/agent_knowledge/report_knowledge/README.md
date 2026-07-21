# report_knowledge — 带时间属性的历史报告知识

本目录放从公司周报、DA 报告、双周会等材料中抽取的历史知识。它回答“某个周期当时怎么判断”，默认不回答“今天是否仍然适用”。

## 必填元数据

每份历史知识文档或结构化表应尽量记录：

| 字段 | 含义 |
|---|---|
| `source_date` | 报告所属月份 / 周期，如 `2026-04` |
| `period_start` / `period_end` | 报告覆盖的业务日期范围 |
| `ingested_at` | 入库日期 |
| `knowledge_status` | 通常为 `historical_report_knowledge` |
| `applies_to_period` | 是否可用于解释来源周期 |
| `applies_to_current` | 是否可直接用于当前判断，默认 `false` |
| `needs_current_confirmation` | 当前复用前是否需要业务确认，默认 `true` |
| `source_type` | weekly_report / da_report / biweekly_meeting 等 |
| `confidence` | raw / reviewed / verified 等 |

## 使用规则

- 回答“4 月当时为什么这样判断”时，可以引用本目录，并标注周期。
- 回答“现在要不要停投/放量/调预算”时，不能直接套历史阈值。
- 如果历史知识被确认仍适用，应迁入或同步到 `../policies/`，并保留来源回链。
