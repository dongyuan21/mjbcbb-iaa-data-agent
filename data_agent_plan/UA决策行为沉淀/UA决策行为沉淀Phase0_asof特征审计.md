# UA 决策行为沉淀 Phase0 as-of 特征审计（UA-P0-08）

> 状态：`frozen_candidate`
>
> 日期：`2026-07-23`
>
> `TASK_ID=UA-P0-08`；`TASK_TYPE=IMPLEMENTATION`；`BASE_COMMIT=c7b94aa2`
>
> 权威方案：第 7.3、8.12 节

## 0. 人话摘要

这个任务回答一个问题：**UA 在做决策的时候，他看到的数据是什么样的？** 我们能不能在事后还原"当时 UA 眼里看到的数字"？

核心结论：
- **消耗、收入、留存等事实表**：按 `active_date` 分区，每天一个版本，**没有回填**——可以安全地做 point-in-time 重建
- **预测表（ROI prediction）**：**有版本化**——同一个日期的预测会随时间更新（每天约 20:30 写入新版本），必须选决策时点当时可见的版本，不能拿最新版本回填
- **Google change-event 宽表的配置列**：用 `MAX_PT` 最新配置补维（P0-01 已确认），**不是历史值**，不能当操作前快照

## 1. 特征分类与时间可见性

### 1.1 消耗/规模趋势特征

| 特征 | 来源表 | 分区字段 | 回填风险 | point-in-time 可重建 |
|---|---|---|---|---|
| 1/3/7/14 天 cost | `tj_ad_spend_active_v2`（CK） | `active_date` | 无（每天一行，不覆盖） | ✅ `available_at = active_date + T+2 延迟` |
| shows / clicks / registers | 同上 | 同上 | 无 | ✅ |
| media_installs | 同上 | 同上 | 无 | ✅ |

**关键规则**：`available_at = active_date + 实际延迟`。P0-02 探测确认 spend 表最新分区 `active_date=2026-07-22`（探测时 07-23），延迟约 1 天。决策时点 `as_of_ts` 能看到的最新 `active_date` = `as_of_ts - 1`（保守取值）。

### 1.2 效率趋势特征

| 特征 | 来源表 | 分区字段 | 回填风险 | point-in-time 可重建 |
|---|---|---|---|---|
| CPI / CTR / CVR | 从 `tj_ad_spend_active_v2` 派生 | `active_date` | 无 | ✅ |
| 实际 ROI（roi_0~roi_359） | `tj_ad_revenue_v2`（CK） | `active_date` | **有回填风险**——收入会随 `date_diff` 增长持续更新 | ⚠️ 必须按 `date_diff` 冻结版本 |
| 留存（retention_1~29） | `af_cohort_user_acquisition_v2`（CK） | `dt` | **有回填风险**——留存随时间成熟 | ⚠️ 必须按 `dt` 冻结版本 |

**收入/留存的回填处理**：同一 `active_date` 的收入会随 `date_diff` 增长持续回填（D0 只有 day-0 收入，D7 才有 7 天累计收入）。point-in-time 重建时必须用决策时点当时已可见的 `date_diff` 版本，不能拿最新回填值。

**规则**：`available_at = active_date + max(date_diff) + SLA延迟`。决策时点 `as_of_ts` 能看到的最大 `date_diff` = `as_of_ts - active_date - 1`（保守）。

### 1.3 预测状态特征

| 特征 | 来源表 | 分区字段 | 回填风险 | point-in-time 可重建 |
|---|---|---|---|---|
| forecast ROI | `market_roi_prediction_360_v6_da`（CK） | `dt`（脚本运行日期）+ `active_date` | **有版本化**——同一 `active_date` 有多个 `dt` 版本 | ⚠️ 必须选 `dt <= as_of_ts` 的最新版本 |
| forecast version | 同上 `created_time` 字段 | — | — | ✅ `created_time` 可作为 `available_at` |

**探测发现**：
- 同一 `active_date` 有 1-5 个 `dt` 版本（越早的 active_date 版本越多）
- `created_time` 每天约 20:30 写入（北京时间）
- 最新版本会覆盖旧版本的预测值

**规则**：`available_at = created_time`。决策时点 `as_of_ts` 能看到的预测版本 = `WHERE created_time <= as_of_ts ORDER BY created_time DESC LIMIT 1`。**不能用最新版本回填历史决策时点的预测值**。

### 1.4 配置特征

| 特征 | 来源表 | 回填风险 | point-in-time 可重建 |
|---|---|---|---|
| Campaign 预算/状态 | Google `ods_market_google_campaign_da`（MC，日快照） | 无（日快照） | ✅ `available_at = dt + 延迟` |
| Campaign 预算/状态 | Meta `ods_market_meta_campaign_da`（MC，日快照） | 无 | ✅ |
| Campaign 预算/状态 | AppLovin `ods_market_applovin_campaign_da`（MC，日快照） | 无 | ✅ |
| Google change-event 宽表的配置列 | `ods_market_google_ads_config_wide_hi` | **有**——`MAX_PT` 最新配置回填 | ❌ 不能当历史值（P0-01 已确认） |

### 1.5 经营状态特征

| 特征 | 来源 | point-in-time 可重建 |
|---|---|---|
| threshold_status（红线状态） | 从 spend + revenue + 阈值规则派生 | ✅（如果阈值版本化） |
| 目标 ROI / gap | PGP 配置或 MI 面板 | ⚠️ 需确认是否有历史版本 |
| 预估利润候选 | 从 forecast + spend 派生 | ⚠️ 依赖 forecast 版本冻结 |

## 2. `event_at` / `snapshot_at` / `available_at` / `ingested_at` 定义

| 时间字段 | 定义 | 例子 |
|---|---|---|
| `event_at` | 业务事件发生时间 | 消耗的 `active_date`；操作记录的 `create_time` |
| `snapshot_at` | 状态快照采集时间 | MC 日快照的 `dt`；CK prediction 的 `created_time` |
| `available_at` | 当时可被决策系统读取的时间 | `active_date + T+2`；`created_time` |
| `ingested_at` | 本流水线到仓时间 | ETL 写入时间 |

**硬规则**：`available_at <= opportunity.as_of_ts`。任何 `available_at > as_of_ts` 的特征值进入快照即为未来泄漏。

## 3. 未来泄漏检测规则

| 检测项 | 规则 | 严重度 |
|---|---|---|
| 收入回填泄漏 | 使用了 `date_diff > (as_of_ts - active_date)` 的收入值 | **P0 阻断** |
| 预测版本泄漏 | 使用了 `created_time > as_of_ts` 的预测版本 | **P0 阻断** |
| 配置回填泄漏 | 使用了 Google 宽表的 `MAX_PT` 配置列当历史值 | **P0 阻断** |
| 迟到数据泄漏 | 使用了 `active_date >= as_of_ts` 的 spend 数据 | P1 |
| target encoding 泄漏 | target encoding 使用了测试集数据 | P1 |

**目标**：`future_leakage_count = 0`。

## 4. 候选特征清单

| 特征组 | 具体特征 | 来源 | point-in-time | 状态 |
|---|---|---|---|---|
| 身份与阶段 | platform, bundle, country, lifecycle, active_days | MC 配置表 | ✅ | `go_candidate` |
| 预算配置 | budget, budget_scope, currency, shared/CBO/ABO/country mode | MC 配置表 + P0-05 映射 | ✅ | `go_candidate` |
| 规模趋势 | cost/shows/clicks/registers/media_installs 的 1/3/7/14d 值和变化率 | CK spend 表 | ✅ | `go_candidate` |
| 效率趋势 | CPI, CTR, CVR, 实际 ROI, 留存 | CK spend+revenue+cohort | ⚠️ 需 version freeze | `go_candidate`（需冻结规则） |
| 预测状态 | forecast ROI, forecast version, 预测生成时间, 预测成熟度 | CK prediction 表 | ⚠️ 需版本选择 | `go_candidate`（需冻结规则） |
| 经营状态 | threshold_status, 目标 ROI, gap, 预估利润候选 | 派生 | ⚠️ 需确认版本 | `hold` |
| 结构特征 | 国家集中度, 素材集中度, Top 项变化 | 派生 | ✅ | `hold`（需设计） |
| 历史动作 | 最近动作方向/幅度/距离上次操作时间/近7/14天操作数 | P0-06 OperationEvent | ✅ | `go_candidate` |
| 数据质量 | freshness, maturity, missingness, sample_size, source coverage | 派生 | ✅ | `go_candidate` |

## 5. 非目标声明

本任务未创建物理表；未执行 DDL/DML；未部署；未签发 `GO_*`。特征清单为候选版本，待 P0-12 总验收时人工确认。
