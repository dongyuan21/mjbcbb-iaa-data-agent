# UA 决策行为沉淀 Phase0 静态来源审计（UA-P0-01）

> 状态：`draft_for_review`（本任务为 IMPLEMENTATION candidate，未经独立 Review 与人工验收前不作为最终结论）
>
> 日期：`2026-07-23`
>
> `TASK_ID=UA-P0-01`；`TASK_TYPE=IMPLEMENTATION`；`TARGET_REPO=/Users/lidongyuan/hungrystudio/点位/数仓`；`BASE_COMMIT=80f54c4cbc5545d413710068581205b12118d001`
>
> 只读依赖：`pgp-platform@8c7c5c375f65fc57f4cd05e59ed1078c9e414b09`（读取时的 HEAD，仅用于代码证据引用，未修改该仓库任何文件）
>
> 权威方案：`data_agent_plan/UA决策行为沉淀/UA决策行为沉淀与回测方案.md` 第 6、20 节
>
> 权威任务书：`data_agent_plan/UA决策行为沉淀/UA决策行为沉淀执行任务书.md` `UA-P0-01` 任务卡

## 1. 任务范围与方法

本任务只读核对当前仓库与 PGP 代码中已经存在的 MI、MC、CK、Google/Meta/AppLovin 证据，形成 live probe 前的静态来源注册表。**未调用任何 live 接口或数据库，未修改 PGP 代码，未新增表。**

结论状态标注沿用方案第 6.1 节定义：

| 状态 | 含义 |
|---|---|
| `repo_confirmed` | 已通过读取代码/文档确认，引用具体文件与行号 |
| `live_verification_required` | 静态证据显示存在该能力，但覆盖率、最新性、字段完整度仍需 live probe（对应 `UA-P0-02`/`UA-P0-03`） |
| `design_required` | 当前没有形成可训练、可追溯的标准数据产品，需要新增逻辑表或产品埋点 |

## 2. 核对项 1：PGP `/history` 当前是否只合并 `ua-remarks + ua-operates`

**结论：`repo_confirmed`，是。**

`Controller.History`（`pgp-platform@8c7c5c37:server/internal/http/controllers/campaignoverview/controller.go:805-840`）在拿到 MI token 后调用 `queryMICampaignHistoryCached`（同文件 826 行）。

`queryMICampaignHistoryCached`（`.../cached_queries.go:323-328`）只是缓存包装，直接转调 `queryMICampaignHistory`。

`queryMICampaignHistory`（`.../controller.go:2321-2374`）内部只启动两个并发查询：

```text
2333 行 → ctrl.queryCampaignRemarksByScope(...)   → ua-remarks
2340 行 → ctrl.queryCampaignOperatesByName(...)    → ua-operates
```

`callCount` 最多为 2（2330、2337 行的两个 if 分支），代码里没有第三条 goroutine。

## 3. 核对项 2：changelog client 是否存在、是否进入页面主链

**结论：`repo_confirmed`，client 存在，但确认零调用点，未进入 `/history` 主链或任何其他生产路径。**

- Client 方法存在：`mi.Client.QueryCampaignChangelog`（`pgp-platform@8c7c5c37:server/internal/clients/mi/campaign.go:225-231`），内部调用 `queryCampaignChangelog` 私有方法（233-254 行），请求 `GET /api/boards/roi/campaign-govern/changelog`，失败时回退 `GET /api/boards/roi/campaign/changelog`。
- Controller 侧封装存在：`queryCampaignChangelog`（`.../controller.go:2413-2427`）。
- 但对整个 `pgp-platform` 仓库执行：

  ```bash
  grep -rn 'queryCampaignChangelog\|QueryCampaignChangelog' server/
  ```

  仅命中两处**定义**本身（`mi/campaign.go:225`、`controllers/campaignoverview/controller.go:2413`），**没有任何调用点**——不在 `queryMICampaignHistory`、不在 `prewarm_page_chain.go`、不在任何 HTTP handler 里被引用。
- 前端侧交叉确认：`frontend/src/views/pgp/campaign-overview/components/CampaignDataOverview.vue` 只消费后端已聚合的 `historyEvents` prop（288、387 行等），没有出现 `changelog` 字样，说明前端也不存在绕过后端直接拉 changelog 的路径。

**结论意义**：方案第 6.2 节"当前 PGP `/history` 主链只合并 `ua-remarks + ua-operates`，没有调用 changelog"的判断准确；且changelog 路径是完全未被生产流量覆盖的死代码，其字段完整度、分页、去重、覆盖率**没有任何生产运行时证据**，比方案原文措辞更保守——不能假设它"至少被调用过、只是覆盖不明"，应视为**从未被验证执行过**。

## 4. 核对项 3：`ua-operates` 当前过滤维度

**结论：`repo_confirmed`。**

- Client 方法 `QueryCampaignOperates`（`mi/campaign.go:259-283`）的参数结构体 `QueryCampaignUARowParams`（60-67 行）包含 `CampaignID`、`CampaignName`、`StartDate`、`EndDate`、`Limit`、`Offset` 六个字段。
- 但方法体内（264-280 行）**只读取并设置了** `CampaignName`（264-266 行）、`Limit`/`Offset`（267-273 行）、`StartDate`/`EndDate`（275-279 行）；**`p.CampaignID` 从未被读取或设置到请求 query string**。即：结构体声明支持按 `campaign_id` 过滤，但 `ua-operates` 端点的实际调用代码完全没有使用这个字段。
- 在 `/history` 主链的实际调用处（`queryCampaignOperatesByName`，`controller.go:2446-2462`），进一步确认调用方传入的 `mi.QueryCampaignUARowParams{CampaignName: campaignName, StartDate: startDate, EndDate: endDate, Limit: limit}` 里根本没有填 `CampaignID` 字段；而 `queryMICampaignHistory`（2340 行）调用时又把 `startDate`、`endDate` 都传成空字符串 `""`。

**合成结论**：`ua-operates` 端点当前的实际过滤维度是**只有 `campaign_name`**（`campaign_id`、日期范围在主链路径上均未生效）；`limit`/`offset` 分页参数存在，但主链固定用 `historyQueryLimit=200`（`controller.go:34`）单页拉取，没有多页游标循环逻辑。

对比 `ua-remarks`（`QueryCampaignUARemarks`，`mi/campaign.go:287-314`）：该方法**同时**设置了 `campaign_name`（292-294 行）**和** `campaign_id`（295-297 行），双维度过滤能力优于 `ua-operates`。

## 5. 核对项 4：Google change-event 宽表的 old/new 与 `MAX_PT` 最新配置边界

**结论：`repo_confirmed`。**

表卡 `ai_hive/agent_knowledge/tables/ods_market_google_ads_config_wide_hi.yaml`：

- 该表 `grain`（28 行）明确为"change_event 行 × dt × hour；用 change_event 行补最新 campaign/ad_group/ad 配置快照"。
- 真正的历史 before/after 只存在于两个受限列：`change_event_old_resource`（323-325 行）、`change_event_new_resource`（326-328 行），且这两列在 `query_rules.restricted_raw_columns_do_not_select`（89-91 行）中被标记为不可直接 `SELECT`。
- 生产 lineage 明确写出（`known_pitfalls` id `latest-dimension-not-asof`，405-408 行）："生产 SQL 对 campaign/ad_group/ad/criterion 使用 `MAX_PT` 最新分区补维；这是本表已确认口径……"——也就是说 `campaign_name`、`campaign_daily_budget` 等维度列**不是**该行 change_event 发生时刻的历史值，而是查询时刻的当前最新配置，只能作为"当前参考配置"，不能当作历史 `PreActionSnapshot`。
- 另有 `known_pitfalls` id `change-event-not-config-snapshot`（400-404 行）强调本表"只覆盖发生变更的对象"，不能用 `COUNT(*)` 代表当前全量配置。

此结论与方案第 6.2、8.9、8.12 节的边界描述完全一致，且本次审计补上了精确的字段级证据（列名 + 行号 + `known_pitfalls` id）。

## 6. 核对项 5：Meta Ad Set、Meta Campaign、AppLovin Campaign 表卡

**结论：三张表均为 `repo_confirmed`（表卡已存在）+ `live_verification_required`（覆盖率/新鲜度/字段真实取值需 live probe）。**

### 6.1 `ods_market_meta_campaign_da`（Meta Campaign）

- `grain`："account_id × bundle_id × status"（16 行），`dt` 日分区快照（17-20 行），**不是** change log。
- 预算相关列：`daily_budget`、`lifetime_budget`、`budget_remaining`、`spend_cap`（55-62 行，均为 `decimal(18,2)`）。
- **没有**任何列标识"是否 CBO / Advantage Campaign Budget"（无 `budget_optimization`、`is_cbo` 等字段）；`known_pitfalls`（110-114 行）只泛化提示"业务口径仍需结合媒体 API / MI / DA SQL 校准"，未专门覆盖 CBO/ABO 区分问题——这是**新发现的缺口**，方案第 5.3、8.5 节要求的 `budget_scope=campaign/adset`、`allocation_mode` 字段目前在此表**不存在原生列**，需要额外设计或从 API 层新增采集（`design_required`）。

### 6.2 `ods_market_api_adset_facebook_da`（Meta Ad Set）

- `grain`：`account_id × campaign_id × id × bundle_id × status`（18 行），`dt` 日分区（19-22 行），同样是**快照表，不是 change log**。
- 预算相关列：`daily_budget`、`lifetime_budget`、`budget_remaining`、`spend_cap`（67-78 行，均为 `type: string`，**不是** decimal——最小货币单位和数值解析需要额外校准，对应 `known_pitfalls` id `topic-p3-new`，217-218 行）。
- `campaign` 列（181-183 行）是嵌套 JSON 字符串（"campaign 摘要 JSON"），**不是**结构化的 `budget_scope`/`allocation_mode` 字段；`known_pitfalls` id `metadata-not-fact`（219-220 行）只提示这是元数据表不是事实表，未提到 CBO/ABO。
- **结论**：Meta ABO 的实际决策对象（Ad Set 级预算）在字段层面存在（`daily_budget`/`lifetime_budget`），但 CBO 与 ABO 的**区分标志**在当前两张表卡都不存在，需要新增字段或从原始 API payload 里派生（对应方案 8.5 节 `allocation_mode` 字段，当前状态应为 `design_required`，比方案原先笼统写的"待确认"更精确）。

### 6.3 `ods_market_applovin_campaign_da`（AppLovin Campaign）

- `grain`："created_at × updated_at × platform × account_id × app_id × status"（16 行），`dt` 日分区，快照表。
- 预算相关列：`budget`（47-48 行，`type: string`）、`daily_budget_for_all_countries`（49-50 行，`type: string`）；另有 `countries`（63-64 行，`type: string`）。
- **没有**单独的"国家预算"结构化列（例如 `country_budget_json` 或按国家展开的行）；`daily_budget_for_all_countries` 的命名暗示这是"全部国家共用的日预算"，但字段类型为 `string`，具体是否为 JSON、逗号分隔还是单一数值，表卡未说明，`known_pitfalls`（86-90 行）也只泛化提示需要媒体 API 校准。
- **结论**：方案第 5.3、8.3 节要求的"国家和原始安全解析版本"目前在此表**未见结构化实现**，AppLovin 国家预算语义仍是 `design_required` + `live_verification_required`（需要先拿真实取值样本才能判断 `budget`/`daily_budget_for_all_countries`/`countries` 三列的实际关系）。

## 7. 核对项 6：现有 18 字段统一变更日志合同与 Meta/AppLovin TODO

**结论：`repo_confirmed`。**

- 18 字段合同见 `ai_ck/agent_knowledge/policies/平台操作记录统一变更日志字段规范.md`：字段清单（14-33 行）、级联约束（35-45 行）、三平台覆盖矩阵（47-70 行）与方案第 4.2 节描述的字段集合一致。
- **新发现的治理缺口**：该规范第 45 行 `change_by` 脱敏方式写明"email/user_id 替换为 `operator_<sha256>`"——**这正是方案第 4.2 节明确指出的风险**："不得用普通 SHA256 处理邮箱、工号、低熵文本或原始 payload"。当前生效的政策文档本身仍在用普通 SHA256，尚未按方案要求切换为带 `key_scope/key_version` 的 HMAC 或不可逆 token。这是一个需要单独走治理变更的**已确认阻塞项**，不是方案的假设性风险。
- Meta/AppLovin change log 阻塞状态：`TODO/平台操作记录与素材能力待办.md` 第 73-76 行明确写"Meta / AppLovin change log 表名与采集频率未确认"，"生产 SQL 不能全量跑通"；第 50 行 P1 待办状态为 `blocked（待表名/采集频率确认）`。这与方案第 6.3 节"当前仓库证据只确认 Google 有原生 change-event 示例"的判断完全一致，且 TODO 文件给出的阻塞原因更具体（表名、采集频率两项具体缺口）。

## 8. 结论汇总表

| 核对项 | 状态 | 关键证据（文件:行号） |
|---|---|---|
| `/history` 只合并 ua-remarks+ua-operates | `repo_confirmed` | `pgp-platform:server/internal/http/controllers/campaignoverview/controller.go:805-840,2321-2374` |
| changelog client 存在但零调用 | `repo_confirmed` | `pgp-platform:server/internal/clients/mi/campaign.go:225-231`；`pgp-platform:.../controller.go:2413-2427`（0 调用点） |
| `ua-operates` 只按 `campaign_name` 过滤，主链不传日期范围 | `repo_confirmed` | `pgp-platform:server/internal/clients/mi/campaign.go:259-283`；`pgp-platform:.../controller.go:2340,2446-2462` |
| Google change-event old/new 与 `MAX_PT` 最新配置边界 | `repo_confirmed` | `ai_hive/agent_knowledge/tables/ods_market_google_ads_config_wide_hi.yaml:323-328,400-408` |
| Meta Campaign CBO/ABO 标志缺失 | `repo_confirmed`（缺口本身）+ `design_required`（补齐方式） | `ai_hive/agent_knowledge/tables/ods_market_meta_campaign_da.yaml:55-62,110-114` |
| Meta Ad Set 预算字段存在但类型为 string、无 CBO/ABO 标志 | `repo_confirmed` + `design_required` | `ai_hive/agent_knowledge/tables/ods_market_api_adset_facebook_da.yaml:67-78,181-183` |
| AppLovin 国家预算无结构化列 | `repo_confirmed` + `design_required` + `live_verification_required` | `ai_hive/agent_knowledge/tables/ods_market_applovin_campaign_da.yaml:47-64` |
| 18 字段合同存在，`change_by` 脱敏仍用普通 SHA256（治理阻塞） | `repo_confirmed`（阻塞已确认，非假设） | `ai_ck/agent_knowledge/policies/平台操作记录统一变更日志字段规范.md:45` |
| Meta/AppLovin change log 表未齐套 | `repo_confirmed` | `TODO/平台操作记录与素材能力待办.md:73-76` |

## 9. 本任务未覆盖、留给 `UA-P0-02`/`UA-P0-03` 的项

- 以上所有 `live_verification_required` 结论都需要通过 MC/CK 实际连通性探测和 MI 接口探测确认覆盖率、行数、最新分区——本任务未做任何数据库或接口调用，严格遵守 `UA-P0-01` 非目标"不调用 live 数据"。
- `ua-operates`/`ua-remarks` 的真实分页上限、最早可用日期、账户/媒体维度覆盖仍需 `UA-P0-03`（MI history 与 collector credential gate）验证。

## 10. 非目标声明

本任务未调用 MI、MC、CK 的任何 live 接口；未修改 PGP 代码；未新增或修改任何 MC/CK 表；未执行 DDL/DML；未部署；未查询业务数据；未保存操作人姓名、邮箱或原始敏感 JSON（本报告中出现的字段名均为 schema 元数据，不含真实取值）。
