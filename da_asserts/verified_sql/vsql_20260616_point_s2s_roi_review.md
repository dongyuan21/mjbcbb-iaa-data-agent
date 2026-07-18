# Verified SQL: 点位 S2S → campaign → ROI360 复盘

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260616_point_s2s_roi_review` |
| 状态 | verified |
| 来源 | `../../ai_ck/agent_knowledge/tables/dim_market_campaign_s2s_event_map_da.yaml` + `../../ai_ck/agent_knowledge/metrics/ROI360指标语义.md` |
| 适用场景 | 点位(s2s_event/转化优化目标)投放效率复盘：按点位看消耗、注册、CPI、ROI1/ROI7，判断点位选择/优化目标治理 |
| 最后验证 | 2026-06-16 |

## 原始问题

> PGP 点位页能从 s2s_event 找到 campaign，但"某个点位(优化目标)带来的投放消耗与 ROI 如何"在 CK 内一直没有打通的 verified SQL。

## 口径说明

| 类型 | 内容 |
|---|---|
| 链路 | `dim_market_campaign_s2s_event_map_da`(点位映射) → `tj_ad_spend_active_v2_view`(消耗) + `tj_ad_sdk_revenue_view`(sdk 回收)，按 `campaign_name` join |
| 粒度 | s2s_event(点位) 聚合；窗口内有点位映射且有消耗的 campaign |
| 基数 | 单 bundle 内 campaign→s2s_event 几乎 1:1(com.kcolb.juggle 6379 单点位 / 20 多点位)，按点位聚合不重复计消耗 |
| 折后消耗 | `SUM(cost_zhe/NULLIF(currency,0))` |
| ROI | `roi1 = SUM(rev where date_diff<=0)/SUM(cost_zhe)`；`roi7 = SUM(rev where date_diff<=6)/SUM(cost_zhe)`(实际段) |
| 窗口 | 取 ROI 实际段已成熟窗口(示例 2026-06-07~06-11)；预测段不可纯 SQL 复现 |

## SQL

```sql
WITH
map AS (  -- campaign -> s2s_event (单 bundle 内几乎 1:1, 多点位取 any)
  SELECT campaign_name, any(s2s_event) AS point_event
  FROM shucang_market.dim_market_campaign_s2s_event_map_da
  WHERE bundle_id='com.kcolb.juggle' AND s2s_event != '' AND s2s_event IS NOT NULL
  GROUP BY campaign_name
),
spend AS (
  SELECT campaign_name,
    SUM(cost_zhe/NULLIF(currency,0)) AS cost,
    SUM(registers) AS regs, SUM(shows) AS shows, SUM(clicks) AS clicks
  FROM shucang_market.tj_ad_spend_active_v2_view
  WHERE active_date BETWEEN '2026-06-07' AND '2026-06-11' AND bundle_id='com.kcolb.juggle'
  GROUP BY campaign_name
),
rev AS (
  SELECT campaign_name,
    sumIf(revenue, date_diff<=0) AS rev0,
    sumIf(revenue, date_diff<=6) AS rev6
  FROM shucang_market.tj_ad_sdk_revenue_view
  WHERE active_date BETWEEN '2026-06-07' AND '2026-06-11' AND bundle_id='com.kcolb.juggle'
  GROUP BY campaign_name
)
SELECT m.point_event AS point,
  count(distinct s.campaign_name) AS camps,
  round(SUM(s.cost),2) AS cost_zhe_usd,
  toUInt64(SUM(s.regs)) AS registers,
  round(SUM(s.cost)/NULLIF(SUM(s.regs),0),3) AS af_cpi,
  round(SUM(r.rev0)/NULLIF(SUM(s.cost),0),4) AS roi1,
  round(SUM(r.rev6)/NULLIF(SUM(s.cost),0),4) AS roi7
FROM spend AS s
INNER JOIN map AS m ON s.campaign_name = m.campaign_name
LEFT JOIN rev AS r ON s.campaign_name = r.campaign_name
GROUP BY m.point_event
HAVING cost_zhe_usd > 0
ORDER BY cost_zhe_usd DESC
LIMIT 25;
```

## 预期输出

按点位(s2s_event)输出 campaign 数、折后消耗、注册、CPI、ROI1、ROI7，按消耗排序，用于识别高消耗低回收 / 高 CPI 高价值的优化目标点位。

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-16 | AI | verified | com.kcolb.juggle 06-07~06-11：点位 cost 合计 **756178.20** 与独立总量查询 **756178.2 完全一致**（口径无重复/遗漏）；regs 微差仅因 `HAVING cost>0` 排除零消耗 campaign。8 个有消耗点位，`af_purchase`(375k,ROI7 0.167)、`Total_Ads_Revenue_0013`(292k,ROI7 0.182) 量级最大。 |

## 风险与陷阱

- **多点位 campaign**：单 bundle 内极少(20/6399)，用 `any(s2s_event)` 取一个，消耗误差可忽略；跨 bundle 全量分析须按 bundle 分别跑。
- **s2s_event ≠ PGP 点位名**：命名空间非全局 1:1（见映射表卡 `not-global-point-dictionary`），跨系统对照需验证。
- **`HAVING cost>0`** 只看有投放的点位；零消耗但有自然注册的点位被排除。
- **ROI 实际段**：窗口须取 date_diff 已成熟段；ROI360 等预测段为 MI 应用层预测，本 SQL 不复现。
- **留存维度**可扩展：join `af_cohort_user_acquisition_v2_view` 按 campaign 补 retention_1/6。

## 关联

- 方法论 SOP：`../analysis_sop/20260616_报告看板数据可信度反查SOP.md`
- ROI 口径：`../../ai_ck/agent_knowledge/metrics/ROI360指标语义.md`
- 现场：`../../raw_exports/点位s2s验证/point_roi.sql`
