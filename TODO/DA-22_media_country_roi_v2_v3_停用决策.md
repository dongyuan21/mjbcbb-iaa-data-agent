# DA-22 media_country_roi v2/v3 canonical 决策与 v2 停用

> 创建：2026-07-21
> 来源：`ai_ck/engineering_artifacts/table_version_registry.yaml` 的 `canonical_note: 多版本并存,需 DA 确认 canonical(见 DA-22)`
> 关联表卡：`ai_ck/agent_knowledge/tables/media_country_roi_v2.yaml`（已标 `deprecated_stale`）

## 背景

`shucang_market.media_country_roi` 家族三版本并存：

| 版本 | 最新分区 | lag_days | 状态 |
|---|---|---|---|
| media_country_roi（无版本号） | 2026-01-26 | 169 | dead |
| media_country_roi_v2 | 2026-06-16 | 28 | alive 但 stale |
| media_country_roi_v3 | 2026-07-13 | 1 | alive，最新 |

`table_version_registry.yaml` 自动判定为"多版本并存，需 DA 确认 canonical"，未自动选 v3。

## 待决策

1. **canonical 确认**：v3 是否为唯一 canonical？v2 是否可进入 `deprecated_pending_removal`？
2. **数值差异归因**：`ai_ck/engineering_artifacts/queries/verified/media_country_roi_v2_v3_diff.sql` 显示 v2/v3 同口径差异 ~7-10%，非精度差。需 DA 确认是口径变更还是数据回填差异。
3. **MI 后端依赖**：表卡注明"MI 后端不读此表（2026-06-15 nexus 零命中）"，v2/v3 基准口径不以 MI 为准，由离线管线/DA 定。

## 当前处置（2026-07-21 已落地）

- `ai_ck/agent_knowledge/tables/media_country_roi_v2.yaml` 已标 `documentation_status: deprecated_stale`，Agent 不应默认召回。
- `ai_ck/agent_knowledge/catalog.yaml` 的 v2 条目已对齐为 `documentation_status: deprecated_stale`，`deprecation: pending_removal_pending_da_confirmation`。
- v2 保留为 v2-v3 diff SQL 的对比基线，**不立即删除**，等 DA 确认后再做物理下线。

## 完成条件

- [ ] DA 确认 v3 为 canonical
- [ ] DA 归因 v2/v3 数值差异
- [ ] 若 v3 确认 canonical，更新 `table_version_registry.yaml` 的 `canonical` 字段为 `[media_country_roi_v3]`
- [ ] 若 v2 确认可下线，从 catalog 移除 v2 条目，表卡移到 `audit_archive/`，重跑 `build_ai_ck_profile_index.py`
