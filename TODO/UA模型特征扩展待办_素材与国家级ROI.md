# UA 模型特征扩展待办 — 素材库存量/年龄 + 国家级 ROI 分布

> 创建日期：2026-07-27
> 状态：TODO（等数据量扩大到 5000+ 条后启动）
> 上游实验：`tools/scripts/ua_enrich_features.py` + `data_agent_plan/ua_phase3_v2_data/all_rows_enriched.jsonl`

## 一句话说明

已经从 CK 验证了素材库存量/年龄和国家级 ROI 分布特征**有信号**（重要性排名前 5），但当前 2618 条训练样本撑不起 27 维特征（RF 过拟合，macro_f1 从 0.63 降到 0.62）。等加入 Meta/AppLovin 后样本量到 5000+ 再加入这些特征，预计 macro_f1 能从 0.63 提到 0.70+。

## 实验结论（2026-07-27）

| 特征集 | 维度 | RF macro_f1 | 结论 |
|--------|------|------------|------|
| 旧特征 | 16 | **0.6344** | 当前最佳 |
| 全新特征（+11个） | 27 | 0.6186 | 过拟合 |
| 精选 4 个新特征 | 20 | 0.6238 | 略好于全新但不如旧 |

### 新特征重要性排名（Top 15）

| 排名 | 特征 | 重要性 | 标记 |
|------|------|--------|------|
| 4 | country_roi_std | 0.0489 | **NEW** |
| 5 | adset_age_max | 0.0438 | **NEW** |
| 12 | adset_age_mean | 0.0393 | **NEW** |
| 15 | n_countries_cost | 0.0383 | **NEW** |

## 待加入的特征清单

### 素材类（从 CK `tj_ad_spend_active_v2` 按 `adset_name` 维度算）

| 特征 | 含义 | 计算方式 |
|------|------|---------|
| `n_adsets_total` | 广告组总数 | `count(DISTINCT adset_name)` |
| `n_adsets_active` | 近 7 天有消耗的广告组数 | `last_seen >= as_of - 7d` |
| `n_adsets_new` | 近 7 天首次出现的广告组数 | `first_seen >= as_of - 7d` |
| `adset_age_max` | 最老广告组年龄（天） | `as_of - min(first_seen)` |
| `adset_age_mean` | 平均广告组年龄（天） | `mean(as_of - first_seen)` |
| `n_adsets_stopped` | 已停投广告组数 | `last_seen < as_of - 7d` |

### 国家类（从 CK 按 `country` 维度算，必须在 bundle_id 前提下）

| 特征 | 含义 | 计算方式 |
|------|------|---------|
| `n_countries_cost` | 有消耗的国家数 | `count(DISTINCT country) WHERE cost > 0` |
| `n_countries_neg_roi` | ROI < 0 的国家数 | `count WHERE roi < 0` |
| `country_roi_std` | 各国家 ROI 的标准差 | `std(roi) GROUP BY country` |
| `country_roi_min` | 最低国家 ROI | `min(roi)` |
| `bottom3_cost_share` | ROI 最低 3 个国家的消耗占比 | `sum(cost of bottom3) / total_cost` |

## 启动条件

- [ ] 训练样本量 ≥ 5000 条（当前 2618，需加入 Meta/AppLovin 操作）
- [ ] `ua_enrich_features.py` 已就绪，可直接运行
- [ ] `all_rows_enriched.jsonl` 已保存增强后的训练数据

## 启动步骤

1. 扩展到 Meta + AppLovin（快照 diff），样本量到 5000+
2. 重新运行 `ua_enrich_features.py` 生成增强数据
3. 用精选特征集（旧 16 + 新 4 = 20 维）重训 RF
4. 如果 macro_f1 > 0.65，更新 `ua_predict.py` 的 `NUMERIC_FEATS` 和 `fetch_live_features`
5. 重新部署

## 关键约束

- 国家级数据**必须在 bundle_id 前提下**查询（不能跨 app 看国家）
- 素材年龄用 CK 的 `adset_name` 的 `first_seen` / `last_seen` 推断，不是 Google 后台的素材创建时间
- `all_rows_enriched.jsonl` 在 `.gitignore` 里，不入 git（太大），通过 `ua_enrich_features.py` 重新生成
