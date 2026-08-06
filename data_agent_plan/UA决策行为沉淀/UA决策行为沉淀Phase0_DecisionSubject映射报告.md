# UA 决策行为沉淀 Phase0 DecisionSubject 映射报告（UA-P0-05）

> 状态：`draft_for_review`
>
> 日期：`2026-07-23`
>
> `TASK_ID=UA-P0-05`；`TASK_TYPE=IMPLEMENTATION`；`BASE_COMMIT=fd64cbb7`
>
> 权威方案：`data_agent_plan/UA决策行为沉淀/UA决策行为沉淀与回测方案.md` 第 4.4、5.3、8.3—8.5 节
>
> 权威任务书：`data_agent_plan/UA决策行为沉淀/UA决策行为沉淀执行任务书.md` `UA-P0-05` 任务卡

## 0. 人话摘要

这个任务回答一个问题：**当 UA 改了一个预算的时候，他到底改的是"谁的"预算？** 是某个 Campaign 的？还是几个 Campaign 共享的一个预算池？还是某个广告组的？还是某个国家的？

答案取决于平台和预算类型：

| 平台 | 预算可以挂在哪 | 当前数据能不能区分 | 结论 |
|---|---|---|---|
| Google | Campaign 或共享预算池 | ✅ 有 `budget_id` + `budget_explicitly_shared` | 可以区分 |
| Meta | Campaign（CBO）或 AdSet（ABO） | ✅ Campaign 和 AdSet 都有预算字段；CK 有 `budget_type` | 可以区分 |
| AppLovin | 全局预算或国家预算 | ✅ `budget` 字段是 JSON，有 `country_code_to_daily_budget` | 结构化字段存在，但当前没有按国家分预算的 Campaign |

## 1. Google DecisionSubject 映射

### 1.1 探测结果

MC `ods_market_google_campaign_da`（dt=2026-07-23）：

| 字段 | 值示例 | 说明 |
|---|---|---|
| `campaign_id` | `20571899452` | Campaign 唯一 ID |
| `customer_id` | `9367922313` | 广告账户 ID |
| `budget_id` | `12962258784` | 预算资源 ID |
| `budget_explicitly_shared` | `null` 或 `true` | 是否为共享预算 |
| `daily_budget` | `6000.0` | 日预算（micros 单位需确认） |

### 1.2 分布

| `budget_explicitly_shared` | Campaign 数 | 含义 |
|---|---|---|
| `null` | 15,523 | 非共享预算，预算挂在单个 Campaign 上 |
| `true` | 102 | 共享预算，一个 `budget_id` 可能被多个 Campaign 引用 |

共享预算案例：`budget_id=15681555559` 被 2 个 Campaign 引用——这是典型的 shared_budget DecisionSubject。

### 1.3 映射结论

| DecisionSubject 类型 | 映射键 | 可行性 |
|---|---|---|
| `campaign_budget` | `customer_id + campaign_id` | ✅ 可唯一标识 |
| `shared_budget` | `customer_id + budget_id`（当 `budget_explicitly_shared=true`） | ✅ 可唯一标识 |

**`budget_resource_key` 构造方式**（方案 8.4 节）：
- `campaign_budget`：`H(google, customer_id, campaign_id, campaign_budget)`
- `shared_budget`：`H(google, customer_id, budget_id, shared_budget)`

**注意**：共享预算的一次修改影响多个 Campaign，`affected_campaign_keys` 需要通过 `budget_id` JOIN 出所有引用该 budget 的 Campaign。102 个 shared budget Campaign 占比很小（0.65%），但必须正确建模，不能复制成多个独立 treatment。

## 2. Meta DecisionSubject 映射

### 2.1 探测结果

MC `ods_market_meta_campaign_da`（dt=2026-07-23）：

| 统计项 | 值 |
|---|---|
| Campaign 总数 | 41,915 |
| Campaign 有 `daily_budget > 0` | 27,712（66%）→ 预算在 Campaign 层（CBO） |
| Campaign 有 `lifetime_budget > 0` | 7 → 总预算模式 |
| Campaign 无预算 | 14,196（34%）→ 预算可能在 AdSet 层（ABO） |

MC `ods_market_api_adset_facebook_da`（dt=2026-07-23）：

| 统计项 | 值 |
|---|---|
| AdSet 总数 | 51,899 |
| AdSet 有 `daily_budget` | 19,915（38%）→ 预算在 AdSet 层（ABO） |
| AdSet 有 `lifetime_budget` | 19,915 → 与 daily 重叠 |

CK `market_api_campaign_info_facebook_dist`（dt=2026-07-23）的 `budget_type` 分布：

| `budget_type` | Campaign 数 | 含义 |
|---|---|---|
| `DAILY` | 27,712 | 日预算（与 MC daily_budget>0 一致） |
| `NONE` | 14,196 | 无 Campaign 层预算（ABO 模式） |
| `LIFETIME` | 7 | 总预算 |

### 2.2 CBO/ABO 区分

**新发现（P0-01 未覆盖）**：Meta MC 表卡没有 CBO/ABO 标志列，但可以通过以下方式区分：

1. **CK `budget_type` 字段**：`DAILY`/`LIFETIME` = 预算在 Campaign 层（CBO）；`NONE` = 预算在 AdSet 层（ABO）
2. **MC 数据推导**：`daily_budget > 0` → CBO；`daily_budget = null/0` 且对应 AdSet 有 `daily_budget` → ABO

两种方式交叉验证一致：27,712 Campaign 有 Campaign 层预算（CBO），14,196 没有（ABO）。

### 2.3 映射结论

| DecisionSubject 类型 | 映射键 | 可行性 |
|---|---|---|
| `campaign_budget`（CBO） | `account_id + campaign_id`（当 `budget_type != NONE`） | ✅ 可唯一标识 |
| `adset_budget`（ABO） | `account_id + campaign_id + adset_id`（当 Campaign `budget_type = NONE` 且 AdSet 有预算） | ✅ 可唯一标识 |

**`budget_scope` 字段**：`campaign`（CBO）或 `adset`（ABO），由 `budget_type` 决定。
**`allocation_mode` 字段**：CBO 时为 `advantage_campaign_budget` 或 `manual`（需进一步确认 `smart_promotion_type` 字段是否对应 Advantage CBO）。

## 3. AppLovin DecisionSubject 映射

### 3.1 探测结果

MC `ods_market_applovin_campaign_da`（dt=2026-07-23）：

| 字段 | 值示例 | 说明 |
|---|---|---|
| `id` | `2298226` | Campaign ID |
| `account_id` | `944004934` | 账户 ID |
| `budget` | `{"daily_budget_for_all_countries": "1000", "country_code_to_daily_budget": {}}` | **JSON 字符串**，含全局预算和国家预算 |
| `daily_budget_for_all_countries` | `1000` | 全局日预算（与 JSON 内字段一致） |
| `countries` | `["US"]` 或 `["TT","UG",...]` | 国家列表 |

### 3.2 关键发现

**P0-01 报告说"AppLovin 无结构化国家预算列"是错误的**——`budget` 字段实际上是 JSON 字符串，里面有 `country_code_to_daily_budget` 子字段。只是当前探测的所有 Campaign 这个字段都是空 `{}`，说明目前没有 Campaign 按国家分预算。

`budget` JSON 结构：

```json
{
  "daily_budget_for_all_countries": "1000",
  "country_code_to_daily_budget": {}
}
```

### 3.3 映射结论

| DecisionSubject 类型 | 映射键 | 可行性 |
|---|---|---|
| `campaign_budget`（全局预算） | `account_id + campaign_id`（当 `country_code_to_daily_budget` 为空） | ✅ 可唯一标识 |
| `country_budget`（国家预算） | `account_id + campaign_id + country`（当 `country_code_to_daily_budget` 非空） | ✅ 结构化字段存在，但当前无实际数据 |

**`budget_scope` 字段**：`global`（`country_code_to_daily_budget` 为空）或 `country`（非空）。
**安全解析**：`budget` 字段是 JSON 字符串，需要版本化解析器；解析失败时标 `parse_failed`，不能静默丢弃。

## 4. 跨平台身份映射

### 4.1 MI Campaign Name → MC/CK Campaign ID

MI `ua-operates` 只支持 `campaign_name` 过滤，不支持 `campaign_id`。需要建立 name → ID 的映射：

| 平台 | ID 来源 | 映射可行性 |
|---|---|---|
| Google | MC `ods_market_google_campaign_da.campaign_id` | ✅ 名称在 MC 表里有对应 ID |
| Meta | MC `ods_market_meta_campaign_da.id` | ✅ |
| AppLovin | MC `ods_market_applovin_campaign_da.id` | ✅ |

**风险**：Campaign 改名后 MI 操作记录里的旧名称可能与 MC 当前快照不匹配——需要用历史快照做带时间有效期的映射（方案 8.3 节 `dim_market_campaign_identity_scd`）。

### 4.2 改名/复制/删除

当前探测未覆盖改名场景。需要后续在 P0-06（OperationEvent 合同）中用更大样本验证名称匹配命中率。P0-04 矩阵已标记此项为 `hold`。

## 5. 候选 DecisionSubject 准入状态

| 平台 | DecisionSubject | 身份可唯一标识 | 预算层级可区分 | 候选状态 |
|---|---|---|---|---|
| Google | `campaign_budget` | ✅ | ✅（非 shared） | `go_candidate` |
| Google | `shared_budget` | ✅ | ✅（`budget_explicitly_shared`） | `go_candidate` |
| Meta | `campaign_budget`（CBO） | ✅ | ✅（`budget_type`） | `go_candidate` |
| Meta | `adset_budget`（ABO） | ✅ | ✅（AdSet 有预算） | `go_candidate` |
| AppLovin | `campaign_budget`（全局） | ✅ | ✅（JSON 解析） | `go_candidate` |
| AppLovin | `country_budget` | ✅（结构存在） | ✅（`country_code_to_daily_budget`） | `hold`（当前无实际数据） |

## 6. P0-01 修正

P0-01 报告第 6.3 节说"AppLovin 无结构化国家预算列"——**此处修正**：`budget` 字段是 JSON 字符串，包含 `country_code_to_daily_budget` 子字段，结构化国家预算字段存在，只是当前无 Campaign 使用按国家分预算。

## 7. 非目标声明

本任务未创建生产 SCD 表；未签发 `GO_FACTUAL`；未执行 DDL/DML；未部署；未查询 PII；未保存操作人信息。所有探测均为有界只读查询（LIMIT 5 或聚合统计）。
