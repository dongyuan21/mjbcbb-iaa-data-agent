# MI 消耗 + 激活按 Campaign 聚合

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_mi_spend_activation_by_campaign` |
| 状态 | verified |
| 来源 | 用户增长Topic P0 表卡 |
| 适用场景 | MI 消耗、激活、CPI/IPM 等投放基础复盘 |
| 依赖表 | `h-s.ads_market_tj_ad_spend_active_v2` |
| 最后验证 | 2026-06-13 |

## 验证记录（续）

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-24 | AI | verified | MC `ads_market_tj_ad_spend_active_v2` 最新 `dt=2026-06-23`；`active_date=2026-06-22` Top campaign 查询成功（如 `KR-035-HK-XH-Tachi-横-260328` cost_zhe≈100870）。 |

## 口径说明

- 日期：`dt` 分区 + `active_date` 业务日期。
- 成本：`cost_zhe` 为折后消耗。
- 激活：`registers` 为 AF 安装，`media_installs` 为媒体安装。
- 粒度：`active_date × media_source × bundle_id × campaign_name`。

## SQL

```sql
SELECT
  active_date,
  media_source,
  bundle_id,
  campaign_name,
  COUNT(1) AS rows,
  SUM(cost_zhe) AS cost_zhe,
  SUM(registers) AS af_installs,
  SUM(media_installs) AS media_installs,
  SUM(shows) AS shows,
  SUM(clicks) AS clicks
FROM ads_market_tj_ad_spend_active_v2
WHERE dt = '${bizdate}'
  AND active_date = '${bizdate}'
GROUP BY active_date, media_source, bundle_id, campaign_name
ORDER BY cost_zhe DESC
LIMIT 100;
```

## 验证记录

2026-06-13 用 `bizdate=2026-06-12` 执行成功。Top 行为：

```text
googleadwords_int / com.kcolb.juggle / EU-036-PUR-RC-250911-HK
cost_zhe=163404.3779, af_installs=9486, media_installs=17134
```

## 风险与陷阱

- 这是 campaign 级聚合，不是点位达成率。
- `campaign_name` 精确匹配时需保留原始字符串。
- 如果对齐 MI 页面，需确认页面使用 `_view` 还是 MC ADS 表。

## 动作边界（不自动晋升）

- 本 SQL 只产出 **ROI / CPI / IPM 候选排序**；放量、观察、降预算阈值缺失，最终动作必须标 `needs_decision`。
- 冷启动观察周期、最低消耗等治理规则见 `knowledge/agent_knowledge/policies/投放ROI治理政策.md`。
- Agent 输出应包含 `decision_status=actionable_candidate` 或 `needs_decision`，不得直接写「建议放量」。

## 关联资产

- 排序候选：`da_assets/verified_sql/mi_spend_activation_by_campaign.md`（本文件）
- 素材 ROI join 草案：`da_assets/candidate_sql/material_ipm_with_sdk_revenue_join.md`
