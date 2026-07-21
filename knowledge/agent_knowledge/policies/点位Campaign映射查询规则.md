# 点位 Campaign 映射查询规则

> 状态：active  
> 创建日期：2026-07-02  
> 适用范围：PGP 点位 / S2S 事件与 MI Campaign、AdSet 的映射查询；点位→消耗/回收第一跳；点位覆盖诊断。

## 使用边界

本文定义点位与 Campaign 映射的 CK 表选型、join 口径、查询护栏和常见误区。

可作为当前默认规则使用：

- 回答「点位对应哪个 Campaign」「某 s2s_event 映射到哪些 campaign/adset」。
- 做点位→campaign→ROI360 第一跳：映射表 join 消耗 / 回收事实表。
- 做「有映射无事实」「映射覆盖数」等点位覆盖诊断。

不能直接作为 verified 事实使用：

- 未经过 freshness probe 的当前窗口结论（须标 `freshness_status`）。
- 把映射表当作用户事件触发明细或 AF `event_name` 桥表。
- 把投放优化目标点位与用户高频行为事件混为同一层次做端到端全景（见注意点 §6）。

表卡与 schema 细节以 CK 表卡为准：`ai_ck/agent_knowledge/tables/dim_market_campaign_s2s_event_map_da.yaml`。  
MC 同源表：`ai_hive/agent_knowledge/tables/dim_market_campaign_s2s_event_map_da.yaml`（`hungry_studio.dim_market_campaign_s2s_event_map_da`）。

## 权威表

| 层 | 全名 | 别名 | 角色 |
|---|---|---|---|
| CK（MI ROI360 查询首选） | `shucang_market.dim_market_campaign_s2s_event_map_da` | `ck_point_mapping`、`campaign_s2s_event_map` | PGP 点位投放数据页进入 MI ROI360 的**第一跳** |
| MC（明细溯源 / 训练源） | `hungry_studio.dim_market_campaign_s2s_event_map_da` | — | 与 CK 同源映射；CK 不是 MC 替代真理源，跨源需确认同步延迟 |

本地物理表：`dim_market_campaign_s2s_event_map_da_local`（`ReplicatedReplacingMergeTree`）；查询一律走 Distributed 表 `dim_market_campaign_s2s_event_map_da`。

## 粒度与字段

**粒度**：`media_source × bundle_id × account_id × campaign × adset → s2s_event`

| 字段 | 含义 | 查询注意 |
|---|---|---|
| `s2s_event` | S2S 转化回传事件名 / 点位 | 与 PGP `event_name` **非全局 1:1**，跨系统须按包体/媒体验证 |
| `campaign_name` / `campaign_id` | Campaign | MI filter 主字段为 `campaign_name`；稳定 join 可用 `campaign_id` |
| `adset_name` / `adset_id` | Ad Set | 与 campaign 同级出现在映射行 |
| `bundle_id` | 包体 | PGP 查询会自动限制允许包体；直连 CK 须自行过滤 |
| `media_source` | 媒体渠道 | 与 `bundle_id`、`s2s_event` 组合过滤 |
| `account_id` | 广告账户 | PII，日志中不输出明文 |
| `last_dt` | 映射组合最新出现日期 | **不是分区键**；低频更新维表，不按事实表 SLA 判 stale |

## 标准查询路径

### 1. 按点位查 Campaign

```sql
SELECT
  campaign_name,
  any(campaign_id) AS campaign_id,
  count() AS mapping_rows,
  max(last_dt) AS latest_dt
FROM shucang_market.dim_market_campaign_s2s_event_map_da
WHERE s2s_event = '{s2s_event}'
  AND bundle_id = '{bundle_id}'
  AND media_source = '{media_source}'
GROUP BY campaign_name
ORDER BY campaign_name ASC
LIMIT 50;
```

### 2. 点位→消耗（第一跳 ROI 复盘）

映射表 join 消耗事实，join key 优先 `campaign_name`（保留原始字符串）：

```text
dim_market_campaign_s2s_event_map_da
  → tj_ad_spend_active_v2_view（或 tj_ad_spend_active_v2）
  ON spend.campaign_name = mapping.campaign_name
```

回收侧常见第二跳：`tj_ad_sdk_revenue_view`、`tj_ad_revenue_v2`、`af_cohort_user_acquisition_v2`。  
已验证复盘见：`da_assets/verified_sql/vsql_20260616_point_s2s_roi_review.md`。

### 3. 点位事件渗透 / 价值（需 MC）

映射表**只到 campaign 级**。用户是否触发事件、渗透率、D7 ARPU 等须走 MC AF / 白名单事件表，不能从映射表推导。  
已验证第二跳见：`da_assets/verified_sql/vsql_20260616_point_event_penetration_value.md`。

### 4. 覆盖诊断（有映射无 MI 数据）

症状：映射表有点位，但 MI / CK 事实无消耗或回收。  
推荐 SQL：`ai_ck/engineering_artifacts/queries/verified/point_campaign_coverage.sql`  
常见原因：`campaign_name` 不匹配（含前导空格）、MI 权限、事实表空值、映射陈旧。

## Join 规则摘要

| 映射字段 | 可 join 事实表字段 | 说明 |
|---|---|---|
| `campaign_name` | `tj_ad_spend_active_v2.campaign_name`、`tj_ad_sdk_revenue.campaign_name`、`tj_ad_revenue_v2.campaign_name`、`af_cohort_user_acquisition_v2.campaign_name` | 精确匹配时**保留前导空格**，禁止 `trim` |
| `campaign_id` | `tj_ad_spend_active_v2.campaign_id`、`tj_ad_revenue_v2.campaign_id` | 稳定 join 备选；MI `campaign_id` filter 尚需按场景实证 |
| `s2s_event` | PGP `event_name`、MC 同名映射表 | 命名空间部分重叠，按点位/包体/媒体验证 |

## 注意点（强制）

### 1. `campaign_name` 不可 trim

`campaign_name` 可能有前导空格；传给 MI 或做精确 join 时**禁止** `trim()` / `ltrim()`。  
诊断时若怀疑空格问题，用显式长度或 hex 比对，不要静默清洗。

### 2. `s2s_event` ≠ PGP 点位名（非全局字典）

`s2s_event` 与 PGP 点位 `event_name` **不是全局 1:1**。跨系统对照必须带 `bundle_id` + `media_source` 验证，不能假设所有命名空间完全一致。

### 3. CK 无 `s2s_event ↔ AF event_name` 桥表

当前 5 张映射类表只到 **campaign/adset 级**，不提供 S2S 事件与 AF `event_name` 的官方桥表。  
实测 com.block.juggle：约 **76%** 精确同名、去 `_IOS/_NU/编号` 后缀后约 **82%** 覆盖；其余需按场景建桥（精确同名 → 去后缀模糊 → 标注待确认）。  
桥结果样例见 verified SQL 备注，不得把模糊匹配当全局规则。

### 4. `last_dt` 不是分区键

`last_dt` 表示该映射组合**最新出现日期**，不是按日分区的事实字段。维表低频更新，freshness 按 `dimension_snapshot` 处理，不按消耗/回收表 T-1 SLA 判 stale。

### 5. 映射表不含用户行为明细

CK 映射表只能说明「某点位配置到了哪些 campaign/adset」，**不包含**用户是否触发、触发次数、渗透、重叠率或触发用户价值。这些必须走 MC。

### 6. 投放优化目标点位 ≠ 用户高频行为事件

端到端「投放 ROI → 触发渗透 → 价值」须分两层：

- **投放侧**（第一跳）：优化目标类点位（如 `af_purchase`、`Total_Ads_Revenue`）→ 映射表 → 消耗/ROI。
- **用户侧**（第二跳）：行为埋点类事件（如 `s_custom*`、`s_ad_revenue*`）→ MC 事件表 → 渗透/价值。

仅当某点位**既**被当作 campaign 优化目标投放、**又**被用户高频触发时，才可同点位做端到端全景；当前窗口此类点位极少。不得把两层混为一个事实。

### 7. CK / MC 同源但不同角色

| 用途 | 默认源 |
|---|---|
| MI ROI360 日常看数、点位→campaign 第一跳 | CK `shucang_market.dim_market_campaign_s2s_event_map_da` |
| 训练、标签、明细溯源 | MC `hungry_studio.dim_market_campaign_s2s_event_map_da` |

跨源分析须确认同步延迟和字段同构；CK 不是 MC 替代真理源。

### 8. PGP 包体白名单 ≠ Campaign Overview 范围

Campaign Overview 可见 bundle 与 PGP 点位白名单范围**不一定一致**（如 Block Blast 3D、Nut Sort GO 等）。查映射前确认业务上下文用的是哪套白名单。

## 关联资产

| 资产 | 路径 |
|---|---|
| CK 表卡 | `ai_ck/agent_knowledge/tables/dim_market_campaign_s2s_event_map_da.yaml` |
| MC 表卡 | `ai_hive/agent_knowledge/tables/dim_market_campaign_s2s_event_map_da.yaml` |
| 数据地图 | `ai_ck/agent_knowledge/数据地图.md` |
| 点位→ROI 复盘 | `da_assets/verified_sql/vsql_20260616_point_s2s_roi_review.md` |
| 点位事件渗透/价值 | `da_assets/verified_sql/vsql_20260616_point_event_penetration_value.md` |
| 覆盖诊断 SQL | `ai_ck/engineering_artifacts/queries/verified/point_campaign_coverage.sql` |
| 任务路由 | `task_routes/point_s2s_analysis.yaml` |
| 语义 join | `knowledge/agent_knowledge/semantic_contract/joins.yaml` |
| 覆盖诊断 | `knowledge/agent_knowledge/semantic_contract/diagnostics.yaml` |

## 强制禁止

- 不得把映射表当 AF `event_name` 桥表或用户事件明细表。
- 不得对 `campaign_name` 做静默 `trim` 后 join MI 或事实表。
- 不得假设 `s2s_event` 与 PGP 点位名全局 1:1。
- 不得仅凭映射存在就断言 MI 有 ROI 数据；须 join 事实表或跑覆盖诊断。
- 不得把「有映射无事实」直接写成投放异常结论，须列出 `campaign_name` 清洗、权限、freshness 等排查项。
