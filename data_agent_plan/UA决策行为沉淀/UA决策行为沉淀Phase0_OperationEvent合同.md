# UA 决策行为沉淀 Phase0 OperationEvent 合同（UA-P0-06）

> 状态：`frozen_candidate`（AI 自主冻结候选版本，待 P0-12 总验收时人工确认）
>
> 日期：`2026-07-23`
>
> `TASK_ID=UA-P0-06`；`TASK_TYPE=IMPLEMENTATION`；`BASE_COMMIT=77f5a3cc`
>
> 权威方案：第 4.2、8.7—8.10 节
>
> 合并来源：P0-01（静态审计）、P0-03（MI 接口探测）、P0-04（来源覆盖矩阵）、P0-05（DecisionSubject 映射）

## 0. 人话摘要

这个任务冻结"一条操作记录长什么样"的标准格式。三平台的操作记录来源不同（Google 有原生 change event，Meta 有 MI 操作日志，AppLovin 只有快照差分），但它们都要映射成同一个标准格式——CanonicalOperationEvent。

核心规则：
- **只有一个基础变更日志真相源**（18 字段统一合同），CanonicalOperationEvent 是它上面的派生扩展，不是第二个平行表
- **Google 的 before/after 只用 change event 自带的 old/new**，不能用最新配置回填历史
- **Meta/AppLovin 的快照差分固定 `evidence_tier=inferred_only`**，不能进入可信 treatment
- **事件去重**：MI 没有稳定事件 ID，用组合 hash 去重

## 1. Observation → 18 字段统一变更日志映射

### 1.1 三平台 Observation 来源

| 平台 | Observation 来源 | 证据等级 | 原始字段 |
|---|---|---|---|
| Google | `ods_market_google_ads_config_wide_hi`（change event 宽表） | `native` | `change_event_change_date_time`、`change_event_old_resource`、`change_event_new_resource`、`change_event_user_email`、`change_event_resource_change_operation`、`change_event_changed_fields` |
| Meta | MI `ua-operates`（操作日志） | `audit` | `date`、`create_time`、`description`、`record_type`、`user` |
| AppLovin | MC 配置快照差分 | `inferred_only` | `budget`(JSON)、`daily_budget_for_all_countries`、`countries` 的相邻日期差值 |

### 1.2 18 字段映射规则

| # | 统一字段 | Google 来源 | Meta 来源（MI） | AppLovin 来源（快照差分） |
|---|---|---|---|---|
| 1 | `platform` | 常量 `google` | `meta`（从 description 前缀推断：`[XMP-30]` 或 Meta 后台） | `applovin` |
| 2 | `change_at` | `change_event_change_date_time` | `create_time` | 快照 `dt` 的 00:00:00（精度低，标 `snapshot_diff`） |
| 3 | `object_type` | `change_event_change_resource_type` 映射（CAMPAIGN→campaign, AD_GROUP→adset, AD→ad） | 从 `description` 文本推断（含"预算"→campaign, "广告组"→adset） | `campaign`（AppLovin 无 adset） |
| 4 | `object_id` | `campaign_id` / `ad_group_id` / `ad_id`（按 object_type） | MI 不返回 ID，需通过 `campaign_name` → ID 映射（P0-05） | `id`（Campaign ID） |
| 5 | `change_type` | `change_event_changed_fields` 映射（含 budget→budget, status→status, bid→bid） | 从 `description` 推断（含"预算"→budget, "暂停"→status, "出价"→bid） | `budget`（当前只追踪预算变化） |
| 6 | `change_by` | `change_event_user_email`（PII，入仓前脱敏） | `user`（PII，入仓前脱敏） | 不可得（快照差分无操作人） |
| 7 | `before_after_json` | `{before: change_event_old_resource, after: change_event_new_resource}` | 从 `description` 文本提取（正则匹配"从 X 调整为 Y"） | `{before: 旧快照 budget, after: 新快照 budget}` |
| 8 | `request_id` | `customer_id + change_event_change_date_time + event_hash` | 组合 hash: `H(date + create_time + description + user)` | `H(campaign_id + dt_before + dt_after)` |
| 9 | `request_url` | 重建: `customers/{customer_id}/campaigns/{campaign_id}` | N/A | N/A |
| 10 | `commit_hash` | N/A | N/A | N/A |
| 11 | `change_reason` | N/A（Google change event 无原因字段） | 从 `ua-remarks` 关联（同 Campaign + 时间窗口） | N/A |
| 12 | `bundle_id` | `bundle_id`（宽表已有） | 通过 `campaign_name` → ID → `bundle_id` 映射 | `app_id` → `bundle_id` 映射 |
| 13 | `customer_id` | `customer_id` | `account_id` | `account_id` |
| 14 | `campaign_id` | `campaign_id` | MI 不返回，通过 name → ID 映射 | `id` |
| 15 | `adset_id` | `ad_group_id`（platform=google） | `campaign_id`（Meta AdSet ID，当 object_type=adset） | N/A（platform=applovin 恒空） |
| 16 | `ad_id` | `ad_id` | N/A（MI 不返回） | N/A |
| 17 | `creative_id` | N/A（预算变更不涉及） | N/A | N/A |
| 18 | `notes` | 脚本附加 `source=google_change_event` | 脚本附加 `source=mi_ua_operates` | 脚本附加 `source=snapshot_diff` |

### 1.3 `change_by` 脱敏规则

**当前状态（P0-01 确认）**：18 字段政策第 45 行写的是 `operator_<sha256>`（普通 SHA256，无密钥）。

**冻结规则**：
- Phase 0 阶段：保持现有 SHA256 方式不变（不阻断主线，只阻断操作人维度分析）
- 正式入仓前：升级为 HMAC（带 `key_scope/key_version`，密钥由安全 Owner 管理）
- HMAC 升级前：`change_by` 只存 `operator_redacted`，不做个人级行为建模
- PII 字段（`change_event_user_email`、MI `user`）**不进入 Agent 可访问层**

## 2. CanonicalOperationEvent 扩展字段

在 18 字段基础之上，派生 CanonicalOperationEvent 的扩展字段（方案 8.10 节）：

| 扩展字段 | 定义 | Google 值 | Meta 值 | AppLovin 值 |
|---|---|---|---|---|
| `operation_event_id` | 事件唯一 ID | `event_hash`（MD5 of resource_name） | 组合 hash | 组合 hash |
| `decision_subject_id` | 关联 DecisionSubject | P0-05 映射结果 | P0-05 映射结果 | P0-05 映射结果 |
| `budget_resource_key` | 预算资源键 | `H(google, customer_id, budget_id, scope)` | `H(meta, account_id, campaign/adset_id, scope)` | `H(applovin, account_id, campaign_id, global)` |
| `observed_treatment` | 动作分类 | 从 `change_type` + `before_after_json` 派生 | 从 `description` 正则派生 | 从快照差值派生 |
| `budget_before_native` | 变更前预算（原生币种） | 从 `old_resource` 解析 | 从 `description` 正则提取 | 旧快照 `budget` JSON 解析 |
| `budget_after_native` | 变更后预算（原生币种） | 从 `new_resource` 解析 | 从 `description` 正则提取 | 新快照 `budget` JSON 解析 |
| `change_pct` | 变化幅度 | `(after-before)/before` | 同左 | 同左 |
| `operation_origin` | 操作来源 | `change_event_client_type` 映射 | `[Google Ads 网页端]`→`human_ua`, `[XMP-30]`→`human_ua` | `unknown`（快照差分无法判断） |
| `evidence_tier` | 证据等级 | `native` | `audit` | `inferred_only` |
| `association_confidence` | 关联置信度 | `high`（ID 直接关联） | `medium`（通过 name→ID 映射） | `low`（快照差分，时间不精确） |
| `event_time_precision` | 时间精度 | `second`（change_date_time） | `second`（create_time） | `day`（只有 dt） |

## 3. 事件去重规则

### 3.1 Google

- 主键：`event_hash`（MD5 of `change_event.resource_name`）
- 同一 `dt/hour` 分区内 `event_hash` 唯一（P0-01 验证：466 行 = 466 distinct event_hash）
- 跨分区去重：同一 `event_hash` 可能出现在多个 `dt/hour`（延迟重试），取最早出现的时间

### 3.2 Meta（MI）

- **无稳定事件 ID**（P0-03 确认）
- 组合去重键：`H(campaign_name + date + create_time + description + user)`
- 风险：同一秒同一人同一描述的两条操作会被误判为重复——实际概率极低，可接受
- `ua-operates` 和 `ua-remarks` 的 `record_type` 不同（`operation` vs `remark`），不会跨接口误去重

### 3.3 AppLovin（快照差分）

- 去重键：`H(campaign_id + dt_before + dt_after + budget_before + budget_after)`
- 同一 Campaign 在相邻两天的快照差值只生成一条事件
- 如果连续多天都有变化，每天生成一条独立事件

## 4. 连续调整与 compound action

| 场景 | 规则 | 适用平台 |
|---|---|---|
| 24 小时内同一对象多次预算调整 | 标 `compound_action=true`，首期 Uplift 排除 | 全部 |
| 同一对象同一天既有预算变化又有状态变化 | 生成两条独立事件（`change_type` 不同），关联到同一 `decision_subject_id` | Google/Meta |
| AppLovin 快照差分检测到变化但无法确定时间 | `event_time_precision=day`，标 `inferred_only`，不进入 Uplift | AppLovin |

## 5. evidence_tier 准入规则

| `evidence_tier` | 可进入 FACTUAL | 可进入 RETRIEVAL | 可进入 IMITATION | 可进入 UPLIFT |
|---|---|---|---|---|
| `native` | ✅ | ✅ | ✅ | ✅ |
| `audit` | ✅ | ✅ | ✅（需显式标签） | ✅（需共同支持） |
| `inferred_only` | ✅（事实时间线） | ✅（标来源等级） | ❌ | ❌ |
| `unknown` | ❌（只保留缺口） | ❌ | ❌ | ❌ |

## 6. 正例/负例/边界样本

| 样本类型 | 描述 | 预期行为 |
|---|---|---|
| 正例：Google 预算调整 | change_event 有 `CAMPAIGN_BUDGET` + old/new | 生成 `native` 事件，`change_type=budget`，有 before/after |
| 正例：Meta XMP 操作 | `ua-operates` 返回 `[XMP-30] 将预算从 5000 调整为 6000` | 生成 `audit` 事件，`operation_origin=human_ua`，before/after 从文本提取 |
| 正例：AppLovin 快照差分 | dt=07-22 budget=1000, dt=07-23 budget=1500 | 生成 `inferred_only` 事件，`change_pct=+50%`，`event_time_precision=day` |
| 负例：MI 空结果 | `ua-operates` 返回 0 行 | **不生成任何事件**；空结果 ≠ 无操作 |
| 负例：MI 接口失败 | HTTP 5xx 或 `status.code != 0` | **不生成事件**，标 `source_unavailable` |
| 边界：连续调整 | 同一对象 24h 内 3 次预算变化 | 生成 3 条事件 + `compound_action=true` |
| 边界：自动操作 | Google `change_event_client_type` 不是网页端 | `operation_origin=platform_automation`，分层单独报告 |
| 边界：未知来源 | MI `description` 无前缀 | `operation_origin=unknown`，`uplift_eligible=false` |

## 7. 修正 P0-01

P0-01 §7 说"change_by 脱敏仍用普通 SHA256，未升级为 HMAC"——**此判断准确，维持不变**。本合同第 1.3 节冻结了脱敏升级路径：Phase 0 保持 SHA256，正式入仓前升级 HMAC，升级前只存 `operator_redacted`。

## 8. 非目标声明

本任务未创建物理表；未执行 DDL/DML；未部署；未签发 `GO_*`。所有映射规则均为候选版本，待 P0-12 总验收时人工确认。
