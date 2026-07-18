# knowledge — 已审核业务知识与分析规则

本目录放可复用的业务规则、分析协议、问题分类、报告分析提示、对账证据、带时间属性的历史报告知识，以及跨表机器语义契约。它不放原始材料、不放表卡、不放 verified SQL、不放近期 TODO。

机器召回入口是 `agent_knowledge/catalog.yaml`。Agent 需要先看 manifest 的 `status`、`default_recall`、`applies_to_current` 和 `confidence`，再决定是否引用具体文档。

## 用途分层规范

三层模型(`agent_knowledge` / `engineering_artifacts` / `audit_archive`)、manifest 约定和跨库归属规则的 canonical 定义见 [`../data_agent_plan/知识库三层结构规范.md`](../data_agent_plan/知识库三层结构规范.md)；本节只列 knowledge 库各层的具体文件。

### Agent 用的知识层

| 位置 | 用途 | 默认事实级别 |
|---|---|---|
| `agent_knowledge/catalog.yaml` | 机器可读召回注册表 | 判断是否可默认召回的真理源 |
| `agent_knowledge/数据地图.md` | knowledge 三层与状态边界导航 | 入口说明，不替代 manifest |
| `agent_knowledge/policies/` | 当前可引用的业务规则、治理政策、分析协议、问题分类 | 仅 `confirmed` / `active` 可作为当前规则 |
| `agent_knowledge/semantic_contract/` | 跨表实体、维度、指标、join、治理状态和诊断的机器契约 | `model.json` 是运行时入口；源 YAML 只在维护时读取 |
| `agent_knowledge/report_knowledge/` | 从周报、DA 报告抽取的历史知识，必须带报告周期和适用边界 | 默认只对来源周期成立；显式 `trial_active` 且 `applies_to_current=true` 的表除外 |
| `agent_knowledge/prompts/` | 报告分析、结构化抽取等提示词 | 操作规范，不是业务事实 |
| `agent_knowledge/reconciliations/` | 小窗口对账、口径校准、日期差异验证证据 | 按文档状态使用 |

### 工程建设沉淀层

| 位置 | 用途 |
|---|---|
| `engineering_artifacts/知识一致性门禁.md` | `check_knowledge_consistency.py` 的维护说明 |
| `engineering_artifacts/semantic_contract/` | 语义契约编译、composer 回归和覆盖缺口基线 |

### 审计 / 归档层

| 位置 | 用途 | 默认事实级别 |
|---|---|---|
| `audit_archive/mi_analysis/` | MI ROI360 一次性分析输出和 JSON 快照 | snapshot，不代表最新口径 |
| `audit_archive/draft_knowledge/` | Obsidian 候选草稿 | draft_only，不进入默认事实召回 |
| `audit_archive/semantic_contract/` | 未晋升语义候选和来源索引 | source_manifest，不参与构建 |
| `audit_archive/来源索引.md` | 归档材料说明 | 追溯入口，不作为业务事实 |

## 时间规则

历史报告知识必须回答两个问题：

1. 这条知识描述的是哪个业务周期？
2. 它是否仍能用于当前决策？

`agent_knowledge/report_knowledge/` 中的文档和结构化表应尽量包含：

```yaml
source_date: 2026-04
period_start: 2026-04-01
period_end: 2026-04-30
ingested_at: 2026-06-14
knowledge_status: historical_report_knowledge
validity:
  applies_to_period: true
  applies_to_current: false
  needs_current_confirmation: true
source_type: weekly_report
confidence: reviewed
```

## Agent 使用规则

1. 先读 `agent_knowledge/catalog.yaml` 判断是否允许默认召回；`default_recall=false` 的文件只能作为线索、快照或待审核材料。
2. `agent_knowledge/policies/` 中 confirmed/current 规则优先于历史报告知识。
3. `agent_knowledge/report_knowledge/` 可以回答“当时怎么判断”，不能直接回答“现在应该怎么动作”；但显式 `trial_active` 且 `applies_to_current=true` 的阈值表可作为试运行当前候选判断依据。
4. 当前治理判断需要阈值但只有历史报告知识时，输出 `needs_current_threshold` 或 `needs_current_confirmation`。
5. `audit_archive/draft_knowledge/` 只能作为线索，不能直接回答为最终结论。
6. 规则如果产生 SQL、SOP 或 case，分别沉淀到 `da_assets/verified_sql/`、`da_assets/analysis_sop/`、`da_assets/decision_cases/`。
7. 跨表指标、join、治理状态和诊断规则进入 `agent_knowledge/semantic_contract/`；业务政策仍留在 `agent_knowledge/policies/`，由语义契约引用，不复制政策正文。

## 维护门禁

修改本目录任意文件后必须运行：

```bash
python3 tools/scripts/check_knowledge_consistency.py
```

硬错误和 warning 都应清零；报告写入 `eval/知识一致性报告.md`。

修改 `agent_knowledge/semantic_contract/metrics.yaml` 或 `ai_ck/agent_knowledge/metrics/` 后，另需运行：

```bash
python3 tools/scripts/check_metric_layer_boundary.py
```

该门禁校验跨表机器指标只归 `semantic_contract/metrics.yaml`、CK / MI 页面指标解释只归 `ai_ck/agent_knowledge/metrics/`，二者不得复制同一公式或 join 定义。

## 与 da_assets 的边界

本目录放业务规则、分析协议、跨表语义契约和带时间属性的报告知识，**不放 verified SQL 正文**。规则产出的可复用已验证 SQL 沉淀到 `da_assets/verified_sql/`；候选 / 未验证 SQL 放 `da_assets/candidate_sql/`。本目录的 policies 可以引用 `da_assets/` 下的 SQL 路径和口径结论，但不复制 SQL 正文。
