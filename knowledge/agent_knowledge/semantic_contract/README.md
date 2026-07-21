# semantic_contract — knowledge 内的统一机器可读语义契约

> 定位：夹在 **物理表 / 表卡** 和 **自然语言问题** 之间的翻译契约。
> 把"业务概念怎么跨表拼"固化成结构化、可组合、机器能直接消费的定义，供自研开源 DataAgent runtime 消费。

本目录是 `knowledge/agent_knowledge/` 下的**跨表机器契约子层**，不再作为与 `knowledge/` 同级的独立目录。它不替代表卡，也不替代 `knowledge/agent_knowledge/policies/` 中的业务政策；它把已确认规则和表卡证据编译成 Agent 可消费的结构化合同。

## 用途分层规范

`semantic_contract` 跟随 `knowledge/` 的三层物理存放。新增或迁移文件时，先判断它是 Agent 可消费的语义契约、工程构建产物，还是审计归档材料。

| 层级 | 用途 | 可以回答问题吗 | 默认召回 |
|---|---|---:|---:|
| Agent 用的知识层 | 实体、维度、指标、join、治理和诊断契约 | 可以 | 是，但优先读 `model.json` |
| 工程建设沉淀层 | 编译脚本、composer 回归、覆盖基线 | 不能直接当业务结论 | 否 |
| 审计 / 归档层 | 未晋升提案、原始候选、历史探索 | 不能直接当当前事实 | 否 |

### Agent 用的知识层

| 位置 | 内容 |
|---|---|
| `model.json` | 编译产物，agent / 框架的唯一对外消费入口，勿手改 |
| `entities.yaml` | 业务对象 + 主键 + 别名(NL→实体) |
| `dimensions.yaml` | 可切分 / 过滤维度 + 物理列 + 所属实体 |
| `metrics.yaml` | 指标：公式、分子分母、依赖表、口径变体、汇总规则、状态 |
| `joins.yaml` | 多表拼装契约：join key、方向、MI 兼容性 |
| `governance.yaml` | 投放治理状态机、生命周期阈值、红线/达标线状态和护栏 |
| `diagnostics.yaml` | 异常诊断映射：现象→候选原因→推荐 metric / join / verified SQL |
| `数据地图.md` | 语义层与 `ai_ck`、`ai_hive`、verified SQL 的关系 |

### 工程建设沉淀层

| 位置 | 内容 |
|---|---|
| `knowledge/engineering_artifacts/semantic_contract/build_model.py` | 校验列 / join / 变体 / 诊断引用并编译 `model.json` |
| `knowledge/engineering_artifacts/semantic_contract/eval/` | 回归验证：`regression_cases.yaml` + `compose_sql.py` + 报告 |
| `knowledge/engineering_artifacts/semantic_contract/覆盖缺口基线.md` | 覆盖缺口基线、北极星指标、进度记录和待拍板清单 |

### 审计 / 归档层

| 位置 | 内容 |
|---|---|
| `knowledge/audit_archive/semantic_contract/raw_exports_knowledge_proposals.yaml` | 从原始材料抽出的未晋升语义候选，不参与构建 |
| `knowledge/audit_archive/semantic_contract/来源索引.md` | 归档材料边界说明 |

## 语义层关系

```text
自然语言问题
  ↑  knowledge/agent_knowledge/semantic_contract/ —— 跨表业务概念与机器契约
  ↑  ai_*/agent_knowledge/tables/*.yaml —— 表卡:单表列、单表公式、must_filter、pitfalls(真理源,保留)
  ↑  catalog.yaml / 物理表
```

- 表卡管"列在不在、单表怎么算"。
- 本目录管"业务概念怎么跨表拼"，通过 `source_table` 指向 `ai_ck/agent_knowledge/catalog.yaml` 的 fqn，并用 `base_columns` 引用列，**不复制列定义**。
- `ai_ck/agent_knowledge/metrics/ROI360指标语义.md` 是本目录的证据源/原材料。

## 当前范围

双源建模(`datasource` 路由,跨源禁 SQL join):

- CK `shucang_market`:P0 五张表(spend / sdk_revenue / af_revenue / cohort / mapping)。
- CK `ad_revenue`:广告变现 / LTV 两张表(bs_ad_revenue_v2_di / tj_ad_revenue_ltv_list_utc)。
- MaxCompute `hungry_studio`:预测精度表 `ads_market_roi_pred_accuracy_da`、素材前端表 `ads_market_material_metric_di`。
- 11 实体 / 38 维度 / 50 指标 / 3 join + governance + diagnostics;源覆盖 CK(shucang_market + ad_revenue) + MaxCompute(预测/素材前端/大盘 dau)。
- 回归 16/16:R5/R6/R7 + 素材前端(SC6) + CK 维度/比率(SC7) + ad_revenue LTV(SC8) + 治理状态机(SC9) + 异常诊断(SC10) + 素材级 ROI(SC11) + 大盘 DAU/DNU(SC12) + needs_decision 护栏(SC13) + 首日 ARPU(SC14) + 大盘 ARPDAU/eCPM(SC15) + organic_dnu 拆解(SC16);指标按 `knowledge/engineering_artifacts/semantic_contract/覆盖缺口基线.md` 高频问题优先级扩展,不追求 ROI360 148 全列。
- `needs_decision` 类型/状态的 metric(如 organic_dnu_broad)由 composer 返回 unsupported,不生成 SQL,不替业务拍板。

## 多源与跨源护栏

- 每张表/指标带 `datasource`(`clickhouse` / `maxcompute`)，agent 据此路由到 CK helper 或 MaxCompute skill。
- `engineering_artifacts/build_model.py` 强制:join 左右表必须**同源**，跨源 join 直接报错(CK 与 MC 不能直接 SQL join)。
- 预测偏差(MC)与消耗/回收/留存(CK)分别查询，在应用层对齐，不在 SQL 层 join。

## 口径默认（对齐根 README 高置信口径）

| 口径 | 默认 | 变体 |
|---|---|---|
| 成本 | `total_cost_zhe`(折后) | `total_cost`(折前) |
| 回收源 | `sdk` | `af`(对照) |
| CPI/LTV 分母 | `total_registers`(AF install) | `total_media_installs` |
| organic | 固定输出 `all` 与 `paid_only` 两版 | — |
| campaign join | `campaign_name`(MI 兼容,保留原始字符串) | `campaign_id`(稳定备选) |
| ROI 段 | 真实段；蓝底为预估，不可当真实回收 | — |

## 状态机（复用根 README 约定）

`confirmed` 可作口径结论；`needs_decision` 需业务拍板，agent 不替决；`draft` 仅候选。

## Agent 使用规则

1. 回答跨表指标问题(ROI/LTV/留存)前，先读 `knowledge/agent_knowledge/semantic_contract/model.json` 取 metric 定义与所需 join，不要靠读散文推导 SQL。
2. metric 带 `variants` 时，按默认口径出主版，并按治理要求补对照版(如 organic 两版)。
3. metric/口径标 `needs_decision` 时，输出待决，不写死阈值或默认。
4. 生成 SQL 必须带 `metric.requires_join` 指定的 join 与各表 `must_filter`。
5. 做投放治理/异常诊断时，先读 `knowledge/agent_knowledge/semantic_contract/model.json` 的 `governance`(状态机字段 + 生命周期阈值)与 `diagnostics`(现象→原因→推荐 SQL)；红线/达标线数值标 `needs_decision`，不自行拍板。

## 验收（第 1 点"完成"的判定）

- a. [达成] entities/metrics/dimensions/joins 覆盖 P0 五表 20 指标，结构合法。
- b. [达成] `python3 knowledge/engineering_artifacts/semantic_contract/build_model.py` 校验通过并产出 `knowledge/agent_knowledge/semantic_contract/model.json`。
- c. [达成] `python3 knowledge/engineering_artifacts/semantic_contract/eval/compose_sql.py` 仅凭 model.json 拼出 SQL,16/16 用例通过(SC1→R7 放量候选、SC2→R5 SDK/AF 两版、SC3 留存、SC4→R6 预测偏差跨源拼装、SC5 越界 unsupported、SC6 素材前端 MaxCompute 单表、SC7 CK 维度层级+比率、SC8 ad_revenue 库 LTV 宽表、SC9 治理状态机消费、SC10 异常诊断现象→推荐、SC11→SC16 扩展素材级 ROI、大盘、ARPU、ARPDAU/eCPM 和 organic_dnu 拆解)。

复跑验证：

```bash
python3 knowledge/engineering_artifacts/semantic_contract/build_model.py
python3 knowledge/engineering_artifacts/semantic_contract/eval/compose_sql.py
```

报告写入 `knowledge/engineering_artifacts/semantic_contract/eval/回归验证报告.md`。

## 维护

改 P0 表卡列名/口径后，重跑 `python3 knowledge/engineering_artifacts/semantic_contract/build_model.py`，确认零校验错误再提交。
