# UA 决策行为沉淀证据清单模板

> 状态：`reusable_template`
>
> 版本：`v0.1`
>
> 日期：`2026-07-22`
>
> 用途：所有 `UA-*` 任务在引用任何实时或历史数据结论时，必须使用本模板逐条填写证据；不得用旧文档日期、旧 freshness snapshot 或任务成功描述代替本次探测证据。
>
> 使用者：`UA-P0-01` 至 `UA-P6-05` 全部实现、只读验收、发布和人工 Gate 任务；本文件由 `UA-P0-00` 建立，后续任务只引用、不重复定义字段语义。

## 1. 适用范围与不适用范围

适用：

- 对 MI、MC、CK、平台配置的任何只读探测结论；
- 对表卡、SQL、代码中静态证据的引用（`repo_confirmed` 类结论也要填 `probe_at` 为代码阅读时间，`watermark` 填代码所在 commit SHA）；
- 对模型训练、回测、Level 0—5 报告中任何一条量化指标的来源标注；
- HUMAN_GATE、RELEASE_OPERATION 任务交付材料中的运行证据。

不适用：

- 纯规则/方案设计讨论（无需探测证据，但需注明该内容尚为 `design_required`）；
- 已经通过本模板登记过、且未发生新探测的重复引用（此时直接引用已登记的 `evidence_refs`，不必重复填表）。

## 2. 字段定义

| 字段 | 类型/取值 | 定义 | 禁止行为 |
|---|---|---|---|
| `source` | 字符串 | 数据或代码来源的唯一标识，例如 `MC:hungry_studio.ads_market_tj_ad_spend_active_v2`、`CK:shucang_market.xxx`、`MI:GET /api/boards/reports/campaign-govern/ua-operates`、`REPO:ai_hive/agent_knowledge/tables/xxx.yaml@<commit_sha>` | 不得只写“数据库”或“接口”等模糊描述 |
| `environment` | 字符串 | 探测所用环境标识，例如 `maxcompute-dataworks(prod-readonly)`、`clickhouse-shucang(shucang_market)`、`mi-curl(local-token, scope=readonly)` | 不得省略环境，避免把测试环境结论当生产事实 |
| `probe_at` | ISO8601 时间戳（本地时区标注） | 实际执行探测/阅读代码的时间 | 不得用文档撰写日期或方案日期替代 |
| `as_of` | ISO8601 时间戳或业务日期 | 被探测数据本身所代表的业务时点（例如某张表的业务日期、某次 API 返回覆盖的最新日期） | 不得与 `probe_at` 混用；两者语义不同 |
| `window` | 字符串，例如 `2026-07-15~2026-07-21` 或 `limit=50, offset=0` | 本次探测覆盖的时间窗口或分页范围，必须是有界查询 | 不得用全表扫描或无界查询；不得省略窗口边界 |
| `watermark` | 字符串 | 数据源自身声明或可推断的水位（分区、`max(dt)`、`max(active_date)`、MI 返回的最新 `event_at`、代码所在 commit SHA 等） | 不得用探测时间代替真实数据水位 |
| `query_or_code_hash` | 字符串 | 实际执行的 SQL/API 请求/脚本的确定性 hash 或版本引用（例如 SQL 文本 SHA256 前 12 位、脚本文件 + commit SHA） | 不得只写“执行了查询”而不给可复算引用 |
| `row_count` | 整数或范围 | 本次探测返回的行数/记录数/文件数 | 空结果必须显式写 `0`，不得留空后被误读为“未执行” |
| `pii_status` | `no_pii \| redacted \| contains_pii_not_persisted \| unknown` | 本次证据中是否包含 PII，以及处理方式 | 不得默认填 `no_pii`；含操作人姓名/邮箱/原始 payload 时必须标 `contains_pii_not_persisted` 并说明未落盘方式 |
| `conclusion_maturity` | `repo_confirmed \| live_verified \| design_required \| blocked \| snapshot_only \| connectivity_unverified` | 沿用方案第 6.1 节状态定义，标注本条证据的成熟度 | 不得把 `snapshot_only` 或 `design_required` 结论包装成 `live_verified` |
| `evidence_refs` | 列表 | 本条证据可回溯的文件路径、commit SHA、脱敏输出文件、日志路径等 | 不得只写“见上文”，必须给出可定位引用 |
| `exit_code` | 整数或 `N/A` | 实际执行命令/脚本/查询的退出码；未运行命令时填 `N/A` 并说明原因 | 不得省略；命令失败必须原样保留非零退出码，不得改写为成功 |

## 3. 空表模板（Markdown 表格，供复制填写）

```markdown
| 字段 | 值 |
|---|---|
| source | |
| environment | |
| probe_at | |
| as_of | |
| window | |
| watermark | |
| query_or_code_hash | |
| row_count | |
| pii_status | |
| conclusion_maturity | |
| evidence_refs | |
| exit_code | |
```

## 4. 空表模板（YAML，供脚本化产出证据时使用）

```yaml
evidence:
  source: ""
  environment: ""
  probe_at: ""
  as_of: ""
  window: ""
  watermark: ""
  query_or_code_hash: ""
  row_count: null
  pii_status: ""
  conclusion_maturity: ""
  evidence_refs: []
  exit_code: null
```

## 5. 示例填写（说明性示例，非真实探测结果）

以下示例仅用于演示字段填写方式，**不是**本次 `UA-P0-00` 产生的真实数据结论；`UA-P0-00` 本身未查询任何业务数据。

```markdown
| 字段 | 值 |
|---|---|
| source | REPO:data_agent_plan/UA决策行为沉淀/UA决策行为沉淀与回测方案.md@91a77fa0f8b65599008f79651787a19c6e4b5e2f |
| environment | 本地文件阅读（无数据库/接口调用） |
| probe_at | 2026-07-22T20:00:00+08:00 |
| as_of | 2026-07-22（方案文档标注日期） |
| window | 全文档（第 1—21 节） |
| watermark | commit=91a77fa0f8b65599008f79651787a19c6e4b5e2f |
| query_or_code_hash | N/A（非查询，直接阅读文本） |
| row_count | N/A |
| pii_status | no_pii |
| conclusion_maturity | repo_confirmed |
| evidence_refs | ["data_agent_plan/UA决策行为沉淀/UA决策行为沉淀与回测方案.md"] |
| exit_code | N/A |
```

## 6. 与其他文档的关系

- 本模板只定义字段语义和填写规则，不产生任何具体数据结论；具体结论由各任务在自己的产物文档中引用本模板填写。
- 本模板与 `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀实施台账.md` 中的 `Evidence path` 字段配合使用：台账登记“证据在哪个文件”，本模板规定“该文件里的证据应该长什么样”。
- 本模板不替代 `ai_hive/`、`ai_ck/` 表卡中的 freshness、SLA 或 PII 字段合同；表卡仍以 `skills/table-intake/SKILL.md` 和现有表卡 Schema 为准，本模板用于任务级、一次性的探测证据登记。
- 若某条证据的 `conclusion_maturity` 为 `blocked` 或 `connectivity_unverified`，对应任务的最终交接结论必须同步标 `BLOCKED/HOLD`，不得在交接报告正文写 `PASS`。
