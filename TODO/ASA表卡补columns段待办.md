# ASA 表卡补 columns 段 + market_api_asset_spend_v1_local 漂移

> 创建：2026-07-22
> 来源：软3 schema 漂移治理过程中的遗留项

## 1. tj_ad_af_revenue_asa / tj_ad_sdk_revenue_asa 缺 columns 段

这两张 ASA 表卡当前只有 `join_keys` 段，没有 `columns` 段。2026-07-22 CK 漂移检测发现它们新增了 `channel_first` / `channel_second` 列，但因表卡无 columns 段，无法直接补字段。

### 待办

- [ ] 给 `ai_ck/agent_knowledge/tables/tj_ad_af_revenue_asa.yaml` 补完整 columns 段（参考 `tj_ad_revenue_v2.yaml` 的字段结构 + ASA 专有字段）
- [ ] 给 `ai_ck/agent_knowledge/tables/tj_ad_sdk_revenue_asa.yaml` 补完整 columns 段（参考 `tj_ad_sdk_revenue.yaml` 的字段结构 + ASA 专有字段）
- [ ] 补字段时需 CK live probe `DESCRIBE` 确认完整字段清单，不靠猜测
- [ ] 补完后重跑 `check_table_card_quality.py` 确认无 hard errors

### 证据

- CK `system.columns` 确认两表都有 `channel_first` (String, 一级渠道分类) 和 `channel_second` (String, 二级渠道供应商名称)
- 表卡 `join_keys` 段有 `bundle_id` / `media_source`，说明字段存在但未在 columns 段登记

## 2. market_api_asset_spend_v1_local spend_usd 列间歇性漂移

`market_api_asset_spend_v1_local`（`_local` 物理分片）的 `spend_usd` 列在 CK 端间歇性出现/消失，导致漂移检测反复报 1 张表。

### 当前处置

- `market_api_asset_spend_v1` 的 profile 已明确记录：`spend_usd` 是 `_local` 物理列，Distributed 逻辑表不暴露，Agent 不直接查。
- 这是 CK 端 `_local` 表的动态变化，不是表卡问题。
- 不反复刷基线（刷了还会变）。

### 待办

- [ ] 若 CK 端 `_local` 表 schema 稳定后仍报漂移，再刷基线
- [ ] 若 DA 确认 `spend_usd` 应暴露到 Distributed 逻辑表，更新 profile + 建完整表卡
