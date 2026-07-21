# Campaign 管理与操作协议

> 来源：`nexus/backend/boards/internal/service/report/handler/roi/campaign/`
> 蒸馏日期：2026-06-20

本协议覆盖 MI Campaign 面板的业务规则和查询护栏。指标公式和字段映射见 `ai_ck/agent_knowledge/metrics/Campaign面板指标语义.md`。

## 适用场景

- Campaign 粒度投放分析（消耗、ROI、留存下钻到具体 campaign）
- Campaign 状态管理（开关、预算）
- 投放人员归属和权限
- Campaign 新增 vs 存量分析

## 核心规则

### 1. Campaign 面板与 ROI360 UA 面板的差异

| 维度 | ROI360 UA | Campaign |
|---|---|---|
| 粒度 | `active_date × bundle_id`（可下钻 media/country/campaign） | `campaign_name` 为必选维度 |
| 操作能力 | 只读 | 可开关 Campaign、修改预算 |
| 消耗状态筛选 | 无 | `camp_run` / `camp_close` |
| 时间范围筛选 | 无 | `all` / `new`（仅看新增） |
| 多人操作 | 无 | 检测 campaign 是否多人操作 |
| 描述/变更日志 | 无 | 支持查看和编辑 |
| Marketing API | 无 | 实时获取/修改 AppLovin/FB/TikTok campaign 状态 |

### 2. 消耗状态判断

**投放中**（`camp_run`）：截止日期当天 `SUM(cost_zhe) > 0`

**关闭**（`camp_close`）：截止日期当天 `SUM(cost_zhe) = 0`

注意：这里的"关闭"是数据层判断（当天无消耗），不等于媒体侧的 campaign status。一个 campaign 可能媒体侧状态是 LIVE 但当天没有消耗。

### 3. Campaign 首次消耗日期

表 `shucang_market.campaign_min_cost` 预存每个 `(bundle_id, media_source, campaign_name)` 的首次 `active_date`。

"仅看新增" = 首次消耗日期落在当前筛选的日期区间内。

### 4. Campaign 状态优先级

```text
Marketing API 实时状态（timestamp 更新时） > CK campaign 管理表快照 > 消耗状态推断
```

### 5. Campaign 名称匹配

- Campaign 面板的主 join key 是 `campaign_name`（字符串精确匹配）
- spend/revenue/retention/camp_info/changelog 均通过 `campaign_name` 关联
- `campaign_name` 不做 trim 后传给 MI（保留原始字符串）
- 查询 spend 表时用 `argMax(bundle_id, active_date)` 取该 campaign 的最新包体和媒体归属

### 6. 投放人员权限

Campaign 面板有数据范围权限控制：
- 按 `bundle_id` 关联用户的包体 ownership
- 按 ownership 中的 `Usernames` 筛选 `user` 字段
- 若用户无特定权限配置，回退到 `GetUAUser` 全量人员列表

### 7. 媒体平台筛选

Campaign 面板的媒体筛选仅返回"信息流"分组，不含全部媒体。

## 查询护栏

1. Campaign 面板查询必须包含 `bundle_id` 和日期范围
2. 消耗状态子查询限制 `active_date = endDate` 且 `campaign_name <> ''`
3. `QueryBundleMediaByNames` 仅查近 180 天数据，避免全表扫描
4. 左右表（spend/revenue）通过 `CampaignID` 做中间过滤对齐
5. 默认左表=spend 保证消耗行不丢失；仅当排序字段为收入时交换

## 操作边界

- **Agent 不执行** Campaign 开关或预算修改操作
- Agent 可以查询和分析 Campaign 状态、消耗、ROI
- 放量/停投/观察的阈值判断需业务 owner 拍板
- Agent 只能推荐候选策略，不能自动执行投放动作
