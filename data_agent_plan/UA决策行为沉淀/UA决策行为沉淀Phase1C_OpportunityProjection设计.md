# UA 决策行为沉淀 Phase1C Opportunity Projection 设计（UA-1C-03A）

> 状态：`design_candidate`
>
> 日期：`2026-07-24`
>
> `TASK_ID=UA-1C-03A`；`TASK_TYPE=DESIGN`
>
> `BASE_COMMIT=a1d9c24a`；`WORKTREE=ua-phase1c-2`

## 0. 人话摘要

advisor 前端和反馈链路需要一个"当前机会状态"的只读视图。本任务设计一个 ClickHouse 上的 minimal projection：每个 opportunity 一行，只暴露决策反馈链路必需的最小字段（opportunity_id + decision_subject_id + as_of_ts + freshness + source_unavailable 标记）。**不在线拼 MI 大表**——所有 MI 原始宽表 join 在离线 ETL 完成，在线只读 projection。

## 1. 为什么需要 projection

- advisor 渲染证据包时需要快速查"这条机会是否还存在/是否已被复盘过"
- 反馈链路写 feedback 时需要校验 opportunity_id 合法性
- 案例检索（Phase2）需要按 as_of_ts / platform / 数据成熟度过滤

这些读路径不能直连 MC（延迟高、成本高），需要一个 CK 只读投影。

## 2. CK minimal projection schema

逻辑表 `ck_ua_opportunity_projection`：

| 列 | 类型 | 说明 |
|---|---|---|
| `opportunity_id` | String PK | 确定性 hash |
| `decision_subject_id` | String | 关联 DecisionSubject |
| `platform` | LowCardinality(String) | google / meta / applovin |
| `as_of_ts` | DateTime | 机会判定时间 |
| `trigger_type` | LowCardinality(String) | scheduled_review / anomaly_triggered |
| `data_maturity` | LowCardinality(String) | low / medium / high |
| `freshness_ts` | DateTime | 投影数据新鲜度（来源 ETL 完成时间） |
| `source_unavailable` | Bool | 来源是否不可用（fail closed 标记） |
| `has_feedback` | Bool | 是否已有 PGP feedback（由 outbox 消费回填） |
| `current_feedback_decision` | LowCardinality(String) \| Null | 当前有效 feedback 的 human_decision |
| `projection_version` | String | 投影脚本版本 |
| `projected_at` | DateTime | 投影写入时间 |

约束：
- 只读表，advisor / 反馈链路只 SELECT，不写
- `source_unavailable=true` 时 `has_feedback` 可为 false（来源不可用的机会仍允许复盘，但标记）
- 不投影 PII（decision_subject_id 是 hash，不含原始 ID）

## 3. typed read API 合同

提供给 advisor / 反馈链路的只读查询接口（封装为函数，非 HTTP）：

### 3.1 get_opportunity(opportunity_id) -> dict | None

返回单条 projection 行。不存在返回 None。

### 3.2 list_opportunities(filters) -> list

支持的 filter：
- `decision_subject_id`
- `platform`
- `as_of_ts` 范围（from / to）
- `source_unavailable` (bool)
- `has_feedback` (bool)
- `data_maturity` (集合)

返回匹配的 projection 行列表，按 as_of_ts 升序。

### 3.3 get_current_feedback_decision(opportunity_id) -> str | None

便捷方法：直接返回 `current_feedback_decision`，不存在或无反馈返回 None。

## 4. 不在线拼 MI 大表

明确禁止：
- advisor 渲染时 join `ods_market_google_ads_config_wide_hi`
- 反馈链路查 MI `ua-operates`
- 在线路径调用 MaxCompute

所有 MI 数据消费在离线 ETL（Phase1A Episode builder / feature snapshot）完成，结果落到 MC 物理表后投影到 CK。在线路径只读 CK projection。

理由：
- MI 在线查询延迟 1-10s，不可接受
- 在线拼表会引入 source_unavailable 不可控
- CK projection 可缓存、可重算、可对账

## 5. freshness 与 source_unavailable 语义

- `freshness_ts` = 投影来源 ETL 的完成时间，不是机会本身的时间
- `source_unavailable=true` 表示该机会的来源数据在 ETL 时不可用（MI 接口失败、MC 表空等），projection 仍写入行但标记不可用
- 消费方看到 `source_unavailable=true` 时应 fail closed，不渲染证据包，但仍允许人工 organic 反馈

## 6. has_feedback / current_feedback_decision 回填

- 这两个字段由 outbox 消费任务（UA-1C-05A 导出后）回填
- outbox 消费不是实时的，projection 上的 feedback 状态有延迟（分钟级）
- 反馈链路写 feedback 时不能依赖 projection 的 has_feedback 做强一致校验，必须直查 PGP feedback store

## 7. 当前阶段实现

- 无物理 CK 表，typed read API 用 mock fixture 实现
- projection 数据由 `ua_build_opportunity.py` 输出的 JSONL 喂入
- 后续物理表落地后，函数实现切为 ClickHouse 查询，接口不变

## 8. 后续依赖

- 物理 CK 表建表（待 MaxCompute CreateTable 权限 + CK DDL 授权）
- outbox 消费 ETL（UA-1C-05A 导出 → 回填 has_feedback）
- advisor 渲染服务接入 typed read API
