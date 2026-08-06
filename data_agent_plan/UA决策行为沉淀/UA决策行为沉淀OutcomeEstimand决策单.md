# UA 决策行为沉淀 OutcomeEstimand 决策单（UA-P0-10）

> 状态：`draft_from_knowledge_base`（答案来自数仓知识库验证，待业务 Owner 最终签认）
>
> 日期：`2026-07-23`
>
> `TASK_ID=UA-P0-10`；`TASK_TYPE=HUMAN_GATE`（AI 只整理候选，正式签认来自业务/数据 Owner）
>
> `BASE_COMMIT=afcbd77f`
>
> 权威方案：第 4.6、14.5、18.2 节

## 0. 人话摘要

这个任务定义"怎么算利润"——UA 改了预算之后，到底赚了还是亏了，用哪个数字衡量。

5 个关键问题全部从数仓知识库里找到了答案，不需要额外拍脑袋：

| 问题 | 答案 | 来源 |
|---|---|---|
| 收入用哪个？ | SDK 收入（AF 做对照） | `metrics.yaml:162-175` + 全部 verified SQL |
| 成本用哪个？ | cost_zhe ÷ currency（折后消耗美元） | `metrics.yaml:26-32` + 全部 verified SQL |
| D7/D14 怎么算？ | D7 = date_diff≤6，D14 = date_diff≤13 | `metrics.yaml:188-189` + verified SQL |
| 同一天又改预算又改出价？ | 首期排除 compound action | 方案 `:262,1148` |
| 随机实验按什么粒度？ | 随机簇 × 预注册分析周期 | 方案 `:227,1855` |

**状态**：`estimand_status=unconfirmed`——答案来自知识库，但正式 `GO_OUTCOME` 仍需业务 Owner 签认。

## 1. 收入源

### 1.1 决策

默认收入源 = **SDK 收入**（`tj_ad_sdk_revenue` 表）。AF 收入（`tj_ad_revenue_v2` 表）作为对照口径，两者不可混用。

### 1.2 证据

| 证据 | 文件:行号 |
|---|---|
| 语义合同 `revenue_source.default = sdk` | `knowledge/agent_knowledge/semantic_contract/metrics.yaml:162-175` |
| `roi_n` 同样 `revenue_source.default = sdk` | `metrics.yaml:193-210` |
| verified SQL 全部用 SDK 表 | `da_assets/verified_sql/vsql_20260720_roi360_campaign_cost_roi29_retention6.md:36,95` |
| SDK vs AF 对照 SQL | `da_assets/verified_sql/vsql_20260720_roi360_bundle_media_sdk_vs_af_revenue.md:52,62` |

### 1.3 待确认

方案 `:2084` 标注"是否需要双口径敏感性分析"——建议 Phase 1A 时跑一次 SDK vs AF 对照，确认差异是否显著。

## 2. 成本口径

### 2.1 决策

成本 = **折后消耗** = `SUM(cost_zhe / NULLIF(currency, 0))`。

- `cost_zhe` = 消耗 × 返点比例（已打折）
- 除以 `currency` 得到美元值
- 与方案候选利润公式的 `discounted_spend_usd(enrollment_window)` 语义一致

### 2.2 证据

| 证据 | 文件:行号 |
|---|---|
| `total_cost_zhe` 定义 | `metrics.yaml:26-32` |
| `roi_n` 分母 = `total_cost_zhe` | `metrics.yaml:199-209` |
| verified SQL 一致用 `cost_zhe/currency` | `vsql_20260616_point_s2s_roi_review.md:24,40` |
| 方案候选利润公式 | `UA决策行为沉淀与回测方案.md:2071-2077` |

### 2.3 注意

素材表的 `cost_zhe_usd` 已是折后美元（不再除 currency），与 CK spend 表的 `cost_zhe` 不同——跨表 JOIN 时必须确认口径一致。

## 3. D7/D14 成熟窗口

### 3.1 决策

- **D7**：`date_diff <= 6`（即第 0 天到第 6 天，共 7 天累计）
- **D14**：`date_diff <= 13`（即第 0 天到第 13 天，共 14 天累计）
- 通用规则：**DN = `date_diff <= N-1`**

### 3.2 证据

| 证据 | 文件:行号 |
|---|---|
| 语义合同 `取 date_diff<=N-1` | `metrics.yaml:188-189` |
| verified SQL `sumIf(revenue, date_diff<=6) AS rev6` | `vsql_20260616:25,48-49` |
| 方案 `date_diff <= N-1` | `UA方案:1670,2072,2076` |

### 3.3 留存区别

留存（retention）用精确等于：`retention_6 = sumIf(unique_users, date_diff = 6)`（不是 `<=6`）。收入累计用 `<=`，留存单日用 `=`，两者不可混用。

## 4. Compound Action 处理

### 4.1 决策

- **首期 Uplift 默认排除 compound action**（24h 内多次预算调整，或同一天既改预算又改出价/状态/素材）
- **不简单删失**：后续预算调整由表现驱动，简单删失会造成信息性删失
- 替代方案：限定"单次孤立动作 + washout"支持人群，或用 IPCW / 动态 treatment 方法
- 共享预算/竞价外溢无法归属单对象时：改做簇级 Outcome 或标 `effect_not_estimable`

### 4.2 证据

| 证据 | 文件:行号 |
|---|---|
| compound_action 是质量标记不是可学习动作 | `UA方案:262` |
| 首期 Uplift 默认排除 | `UA方案:1148` |
| 不简单删失，需 washout 或 IPCW | `UA方案:919` |
| 首期只聚焦预算动作 | `UA方案:66` |

## 5. 随机实验单位

### 5.1 决策

- **确认性统计单位**：随机簇 × 预注册分析周期
- **随机簇构建**：按共享预算（shared budget）、账户 ownership、UA 管理关系构建连通分量（ownership connected component），互不重叠的连通分量随机分组
- **不能**机械采用 `UA × account`
- 随机的是"是否展示 Agent 证据与意见"，不是强制 UA 执行动作
- 分析采用 assignment-based ITT

### 5.2 证据

| 证据 | 文件:行号 |
|---|---|
| 确认性统计单位 = 随机簇 × 预注册分析周期 | `UA方案:227,1653` |
| 按 shared budget / ownership / UA 管理关系构建连通分量 | `UA方案:1855` |
| 不能机械用 UA × account | `UA方案:1855` |
| 随机的是"是否展示 Agent 证据" | `UA方案:1841` |
| assignment-based ITT | `UA方案:1853` |

### 5.3 主指标层级

| 层级 | 指标 | 用法 |
|---|---|---|
| 最终确认性主指标 | D14 随机簇 × 预注册分析周期的实际利润 | 确认性业务结果 |
| 早期效果指标 | 同一统计单位的 D7 实际利润 | 更快发现方向和安全问题 |
| 效率 Guardrail | D7/D14 实际 ROI | 防止利润改善由回收恶化换来 |
| 获客 Guardrail | CPI | 防止获客成本显著抬高 |
| 规模 Guardrail | 实际消耗、预算利用率 | 防止被动大幅缩量 |

## 6. 候选利润公式

```
actual_profit_D7
= SUM(actual_revenue(
    acquisition_cohort in enrollment_window,
    date_diff <= 6
  ))
- SUM(discounted_spend_usd(enrollment_window))

actual_profit_D14
= SUM(actual_revenue(
    acquisition_cohort in enrollment_window,
    date_diff <= 13
  ))
- SUM(discounted_spend_usd(enrollment_window))
```

其中：
- `actual_revenue` = SDK 累计收入（`tj_ad_sdk_revenue`，`revenue_source=sdk`）
- `discounted_spend_usd` = `SUM(cost_zhe / NULLIF(currency, 0))`
- `enrollment_window` = 获客 cohort 的时间窗口，由 treatment 生效和 washout 合同定义
- 收入和成本必须对应**同一个** enrollment window 的新增获客 cohort

## 7. 仍待确认项

| # | 待确认 | 谁确认 | 阻断什么 |
|---|---|---|---|
| 1 | SDK vs AF 是否需要双口径敏感性分析 | 业务 Owner | 不阻断 Phase 0/1A，Phase 6 前确认 |
| 2 | 折后消耗的返点比例版本和汇率版本 | 数据/财务 Owner | 正式 `GO_OUTCOME` 前 |
| 3 | partial-day 处理（动作当天的部分天数据） | 业务+数据 Owner | Phase 1A 前确认 |
| 4 | 后续操作的 washout/IPCW 具体参数 | 算法 Owner | Phase 4（Uplift）前 |
| 5 | 预注册分析周期的具体长度 | 业务+数据 Owner | Phase 6 前确认 |
| 6 | MDE、样本量、非劣界值、多重检验校正 | 业务+数据+算法 | Phase 6 前冻结 |

**状态**：`estimand_status=unconfirmed`。在上述 1-6 项确认前，`actual_profit_candidate` 只用于口径核验，不得作为模型标签或 `GO_OUTCOME` Gate。

## 8. 非目标声明

本任务 AI 只整理候选和证据引用；正式签认来自业务/数据/算法 Owner。未执行 DDL/DML；未部署；未签发 `GO_OUTCOME`。
