# UA 决策行为沉淀 Phase0 来源覆盖矩阵（UA-P0-04）

> 状态：`draft_for_review`
>
> 日期：`2026-07-23`
>
> `TASK_ID=UA-P0-04`；`TASK_TYPE=IMPLEMENTATION`；`BASE_COMMIT=fb742a9b`
>
> 合并 P0-01（静态审计）、P0-02（实时探测）、P0-03（MI 接口）三份报告，形成平台 × 接口 × DecisionSubject × 证据等级的唯一来源合同。
>
> **不重新做 live 探测，只合并现有证据。**

## 0. 人话摘要

这个任务把前面三个任务的发现拼成一张大表，回答一个问题：**Google、Meta、AppLovin 三个平台，各自的"谁在什么时候改了什么预算"这个信息，我们能从哪里拿到，可信度有多高？**

简单结论：
- **Google**：有原生操作日志（change event），可信度最高
- **Meta**：已有原生操作日志 `ods_market_facebook_activity_hi`（2026-06-23 起采集，小时级）+ MI 操作日志；宽表 `ods_market_facebook_ads_config_wide_hi` 已拉平操作+配置快照
- **AppLovin**：**MI 里没有操作记录**，只能靠"今天的配置减昨天的配置"来猜，可信度最低

## 1. 证据等级定义

沿用方案第 6.2 节和 P0-04 任务卡的定义：

| 证据等级 | 含义 | 能用于什么 |
|---|---|---|
| `native` | 平台原生 change event / change log | 可信 treatment、行为模仿标签、Uplift |
| `audit` | MI 后端记录的操作日志（有操作人、时间、描述） | 可信 treatment（次于 native）、行为模仿标签 |
| `inferred_only` | 只能靠配置快照差分推断变更 | 只能进入事实时间线或带来源等级的检索；**不能**生成可信 treatment 或行为模仿标签 |
| `unknown` | 来源不完整或无法确认 | 只保留事实与缺口 |

## 2. 平台 × 来源 × 证据等级矩阵

### 2.1 Google

| 来源 | 证据等级 | 字段/能力 | 实时状态 | 依据 |
|---|---|---|---|---|
| `ods_market_google_ads_config_wide_hi`（MC，change event 宽表） | `native` | `change_event_old_resource`/`change_event_new_resource`（受限列，有真实 before/after）；`change_event_change_date_time`（精确到秒）；`change_event_user_email`（PII）；`change_event_resource_change_operation`（CREATE/UPDATE/REMOVE）；`change_event_changed_fields`（FieldMask） | `live_verified`，dt=2026-07-23/hour=09，fresh | P0-01 §5；P0-02 §2 |
| `ods_market_google_campaign_da`（MC，Campaign 配置日快照） | `inferred_only`（快照差分） | `campaign_daily_budget`、`campaign_status` 等；**不是 change log**，只能用相邻日期差分推断变更 | `live_verified`，dt=2026-07-23，fresh | P0-01 §6.1；P0-02 §2 |
| MI `ua-operates`（Google Campaign） | `audit` | 5 字段：date/create_time/description/record_type/user；description 有 `[Google Ads 网页端]` 前缀；支持 campaign_name + 日期范围 + limit/offset 分页 | `live_verified` | P0-03 §2 |
| MI `ua-remarks`（Google Campaign） | `audit`（备注，非操作） | 同上字段；description 有 `【有增量空间】` 等意图前缀 | `live_verified` | P0-03 §3、§7A.3 |

**Google 结论**：有 `native`（change event）+ `audit`（MI 操作日志）双重来源，证据等级最高。`native` 是 before/after 的首选来源；`audit` 补充操作人意图和备注。Google 的 `GO_FACTUAL` 候选状态最强。

### 2.2 Meta

| 来源 | 证据等级 | 字段/能力 | 实时状态 | 依据 |
|---|---|---|---|---|
| MI `ua-operates`（Meta Campaign） | `audit` | 同 Google 的 5 字段；description 有 `[XMP-30]` 前缀（XMP 工具操作）或 Meta 后台操作前缀；**都是 `human_ua`** | `live_verified` | P0-03 §7A.2 |
| MI `ua-remarks`（Meta Campaign） | `audit`（备注） | 同上 | `live_verified` | P0-03 §3 |
| `ods_market_meta_campaign_da`（MC，Campaign 配置日快照） | `inferred_only`（快照差分） | `daily_budget`/`lifetime_budget`（decimal）；**无 CBO/ABO 标志列** | `live_verified`，dt=2026-07-23 | P0-01 §6.1；P0-02 §2 |
| `ods_market_api_adset_facebook_da`（MC，AdSet 配置日快照） | `inferred_only`（快照差分） | `daily_budget`/`lifetime_budget`（string，最小货币单位）；**无 CBO/ABO 标志列** | `live_verified`，dt=2026-07-23 | P0-01 §6.2；P0-02 §2 |
| `market_api_campaign_info_facebook_dist`（CK，Campaign 投影） | `inferred_only`（快照差分） | 有 `budget_type`（DAILY/LIFETIME/NONE）字段——**可以区分 CBO/ABO** | `live_verified`，dt=2026-07-23，42K 行 | P0-02 §3 |
| `market_api_adset_info_facebook_dist`（CK，AdSet 投影） | `inferred_only`（快照差分） | 有 `budget_type` 字段 | `live_verified`，dt=2026-07-23，52K 行 | P0-02 §3 |
| `ods_market_facebook_activity_hi`（MC，小时级操作记录） | `native` | Meta Ads API activities，包含 event_type/object_type/extra_data；object_type 使用历史命名（CAMPAIGN_GROUP=Campaign, CAMPAIGN=AdSet, ADGROUP=Ad） | `live_verified`，dt 范围 2026-06-23 ~ 2026-07-29 | 2026-07-29 表卡准入 |
| `ods_market_facebook_ads_config_wide_hi`（MC，小时级宽表） | `native`（派生） | activity × Campaign/AdSet/Ad/Creative 快照拉宽；预算已 ÷100 | `live_verified`，dt 范围 2026-06-23 ~ 2026-07-19（宽表产出落后于驱动表） | 2026-07-29 表卡准入 |

**Meta 结论（2026-07-29 更新）**：已有 `native` 操作日志（`ods_market_facebook_activity_hi`，2026-06-23 起采集）+ `audit`（MI 操作日志）。宽表 `ods_market_facebook_ads_config_wide_hi` 已将操作记录与 Campaign/AdSet/Ad/Creative 快照拉平。CBO/ABO 区分在 MC 表卡里缺失，但 CK 投影表有 `budget_type` 字段可以补充。Meta 的数据覆盖已接近 Google，但历史窗口更短（Meta API activities 仅保留约 7 天，MC 采集始于 2026-06-23）。

### 2.3 AppLovin

| 来源 | 证据等级 | 字段/能力 | 实时状态 | 依据 |
|---|---|---|---|---|
| MI `ua-operates`（AppLovin Campaign） | **`unknown`（无数据）** | 2 个 AppLovin Campaign 探测均返回 0 条 | `live_verified`（接口连通但无数据） | P0-03 §7A.2 |
| MI `ua-remarks`（AppLovin Campaign） | `audit`（备注） | 有备注记录 | `live_verified` | P0-03 §3 |
| `ods_market_applovin_campaign_da`（MC，Campaign 配置日快照） | `inferred_only`（快照差分） | `budget`/`daily_budget_for_all_countries`（string）；**无结构化国家预算列** | `live_verified`，dt=2026-07-23 | P0-01 §6.3；P0-02 §2 |
| `market_api_campaigns_v2`（CK，Campaign 投影） | `inferred_only`（快照差分） | 有 `updated_at` 字段 | `live_verified`，dt=2026-07-23，104K 行 | P0-02 §3 |
| AppLovin 原生 change log | **不存在** | — | — | P0-01 §7 |
| AppLovin 操作采集 | **TODO** | 用户确认 AppLovin 操作是手动下载的，MI 里没有记录 | — | P0-03 用户确认 |

**AppLovin 结论**：**最弱的平台**。MI 里没有 AppLovin 操作记录（`ua-operates` 返回 0 条），没有原生 change log，只有配置快照差分（`inferred_only`）和 MI 备注（`audit` 但不含操作）。AppLovin 的预算操作事实只能靠快照差分推断，**不能生成可信 treatment 或行为模仿标签**。AppLovin 操作采集方案标记为 TODO。

### 2.4 通用来源（跨平台）

| 来源 | 证据等级 | 说明 | 依据 |
|---|---|---|---|
| `ua-operates` 分页 | `live_verified` | limit/offset 游标分页，has_more + next_offset；空结果与错误可区分 | P0-03 §2.3、§5 |
| `ua-operates` 日期过滤 | `live_verified` | start_date/end_date 生效（PGP 主链不传是代码 bug，不是接口不支持） | P0-03 §2.4 |
| `ua-operates` campaign_id 过滤 | `not_supported` | 接口不读取 campaign_id 参数 | P0-03 §2.5 |
| `ua-operates` media_source 过滤 | `not_supported` | 接口不暴露此参数 | P0-03 §2.5 |
| 稳定事件 ID | `not_found` | 无唯一事件 ID，去重需组合 hash | P0-03 §9 |
| `changelog` operations 字段 | `not_populated` | 4 个 Campaign 均为空，可能从未被填充 | P0-03 §7A.4 |
| collector 凭证 | `RESOLVED` | MI JWT 不过期，用户确认个人 token 可用 | P0-03 §6.3、§7A.5 |

## 3. 候选能力准入状态（不签发正式 GO）

按"平台 × DecisionSubject × 能力"给出候选状态，**不签发正式 `GO_*`**：

| 平台 | DecisionSubject | FACTUAL | OUTCOME | RETRIEVAL | IMITATION | UPLIFT |
|---|---|---|---|---|---|---|
| Google | campaign_budget | `go_candidate` | `go_candidate`（待 estimand） | `go_candidate` | `hold`（待显式标签） | `hold`（待共同支持盘点） |
| Google | shared_budget | `hold`（待身份映射） | `hold` | `hold` | `hold` | `hold` |
| Meta | campaign_budget（CBO） | `go_candidate` | `go_candidate`（待 estimand） | `go_candidate` | `hold` | `hold` |
| Meta | adset_budget（ABO） | `go_candidate` | `go_candidate`（待 estimand） | `go_candidate` | `hold` | `hold` |
| AppLovin | campaign_budget | `hold`（只有 inferred_only） | `go_candidate`（待 estimand） | `hold` | `blocked`（无可信 treatment） | `blocked` |
| AppLovin | country_budget | `blocked`（无结构化列） | `hold` | `blocked` | `blocked` | `blocked` |

**说明**：
- `go_candidate` = 证据足够形成候选，但正式 `GO_*` 须由 `UA-GATE` 人工批准
- `hold` = 有已知缺口，需后续任务补齐
- `blocked` = 当前来源不足以支撑该能力

## 4. 新发现的缺口（需后续任务处理）

| # | 缺口 | 影响 | 建议处理任务 |
|---|---|---|---|
| 1 | Meta MC 表卡无 CBO/ABO 标志列，但 CK 投影有 `budget_type` | DecisionSubject 映射需要 CK 补充 | P0-05 |
| 2 | AppLovin 无操作记录，手动下载 | 预算操作事实只能 inferred_only | TODO（AppLovin 操作采集方案） |
| 3 | AppLovin 无结构化国家预算列 | country_budget DecisionSubject 无法定义 | P0-05 + TODO |
| 4 | MI 操作日志无稳定事件 ID | 去重需组合 hash（date+create_time+description+user） | P0-06（OperationEvent 合同） |
| 5 | `change_by` 脱敏仍用普通 SHA256 | 操作人维度分析不可用 | 治理变更（不阻断主线） |
| 6 | 7 张 MC 表卡缺 `freshness:` 段 | 自动探测覆盖不全 | 表准入流程（不阻断） |

## 5. 非目标声明

本任务未做新的 live 探测（只合并 P0-01/02/03 证据）；未修改 PGP 代码；未新增表；未执行 DDL/DML；未部署；未签发任何正式 `GO_*`。
