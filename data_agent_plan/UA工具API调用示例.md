# UA 工具 API 调用示例

> 线上地址：`https://pgp-v1-xgboost.youxi123.com`
> 全部接口不走 SSO，可直接 curl 调用
> 当前线上版本：`79b8877f`

## 工具列表

| # | 工具 | 方法 | 接口 | 说明 |
|---|------|------|------|------|
| 1 | 国家排除效应 | GET | `/api/ua/country-effect` | 查 DiD 因果效应 |
| 2 | 重建效应表 | POST | `/api/ua/country-effect/rebuild` | 拉数据+跑 DiD |
| 3 | RF 操作预测 | GET | `/api/ua/predict` | 概率排序 |
| 4 | RF 手动预测 | POST | `/api/ua/predict/manual` | 手动输入数据 |
| 5 | 规则树预测 | GET | `/api/ua/rule-tree` | 可读规则+效应 |
| 6 | 规则树手动 | POST | `/api/ua/rule-tree/manual` | 手动输入+规则 |
| 7 | 导出全部规则 | GET | `/api/ua/rule-tree/rules` | 列出所有规则 |

---

## 1. 国家排除效应 — 查某国家

```bash
curl -s "https://pgp-v1-xgboost.youxi123.com/api/ua/country-effect?country=Germany" | python3 -m json.tool
```

返回 Germany 排除后的 D7/D14 DiD 效应 + CI + 安慰剂 + 标签。

## 2. 国家排除效应 — 查某 campaign

```bash
curl -s "https://pgp-v1-xgboost.youxi123.com/api/ua/country-effect?campaign=US-035-HK-XH-TachiPer020-%E6%A8%AA-260602" | python3 -m json.tool
```

返回该 campaign 排除了哪些国家 + campaign 级 DiD + 每个国家的参考效应。

## 3. 国家排除效应 — 全局摘要

```bash
curl -s "https://pgp-v1-xgboost.youxi123.com/api/ua/country-effect" | python3 -m json.tool
```

不传参数，返回全局 DiD + 所有国家效应列表。

## 4. RF 操作预测 — 按 campaign

```bash
curl -s "https://pgp-v1-xgboost.youxi123.com/api/ua/predict?campaign=US-035-HK-XH-TachiPer020-%E6%A8%AA-260602" | python3 -m json.tool
```

返回 5 类操作概率排序 + 方向 + 置信度。

## 5. RF 操作预测 — 手动输入

```bash
curl -s -X POST "https://pgp-v1-xgboost.youxi123.com/api/ua/predict/manual" \
  -H "Content-Type: application/json" \
  -d '{
    "cost_7d": 50000,
    "revenue_7d": 2500,
    "cost_change_pct": 0.35,
    "app_group": "BlockBlast"
  }' | python3 -m json.tool
```

必填 `cost_7d`、`revenue_7d`。可选：`cost_change_pct`、`daily_budget`、`lifecycle_days`、`app_group` 等。

## 6. 规则树预测 — 按 campaign

```bash
curl -s "https://pgp-v1-xgboost.youxi123.com/api/ua/rule-tree?campaign=KR-035-HK-XH-Tachi-%E6%A8%AA-260328" | python3 -m json.tool
```

返回可读规则路径 + 支持度 + 置信度 + DiD 效应。

## 7. 规则树预测 — 手动输入

```bash
curl -s -X POST "https://pgp-v1-xgboost.youxi123.com/api/ua/rule-tree/manual" \
  -H "Content-Type: application/json" \
  -d '{
    "cost_7d": 50000,
    "revenue_7d": 2500,
    "cost_change_pct": 0.35,
    "lifecycle_days": 100,
    "roi_day30": 0.15,
    "retention_day2": 0.35,
    "app_group": "BlockBlast"
  }' | python3 -m json.tool
```

支持传入 cohort 指标：`roi_day1/7/14/30/60/90/180/360`、`roi_ratio_7_1`、`arpu_day1/7/30`、`retention_day2/7/30` 等。不传默认 0。

## 8. 导出全部规则

```bash
curl -s "https://pgp-v1-xgboost.youxi123.com/api/ua/rule-tree/rules" | python3 -m json.tool
```

返回规则树全部叶节点规则（约 36 条），每条含操作类型 + 条件 + 支持度 + 置信度 + DiD 效应。

**注意**：`python3 -m json.tool` 会把中文转义成 `\uXXXX`，直接 `curl -s` 看就是正常中文。

---

## 真实完整调用示例（带 cohort 指标）

以下数据来自 `US-035-HK-XH-TachiPer045-横-260602`（Block Blast，2026-07-25 的真实数据）。

### RF 预测 + 规则树预测 同时调用

```bash
# 真实数据：cost_7d=1458520, revenue_7d=24586, ROI7=1.7%, ROI360=123%, 留存38%
curl -s -X POST "https://pgp-v1-xgboost.youxi123.com/api/ua/predict/manual" \
  -H "Content-Type: application/json" \
  -d '{
    "cost_7d": 1458520,
    "revenue_7d": 24586,
    "cost_change_pct": -0.48,
    "lifecycle_days": 53,
    "daily_budget": 52000,
    "app_group": "BlockBlast",
    "channel_type": "MULTI_CHANNEL",
    "last_op_type": "budget",
    "shows_7d": 13478462,
    "clicks_7d": 158359,
    "registers_7d": 32860,
    "roi_day30": 0.4797,
    "roi_day360": 1.2277,
    "roi_ratio_7_1": 2.71,
    "retention_day2": 0.38,
    "arpu_day1": 0.417
  }'

# 规则树同样的数据
curl -s -X POST "https://pgp-v1-xgboost.youxi123.com/api/ua/rule-tree/manual" \
  -H "Content-Type: application/json" \
  -d '{
    "cost_7d": 1458520,
    "revenue_7d": 24586,
    "cost_change_pct": -0.48,
    "lifecycle_days": 53,
    "daily_budget": 52000,
    "app_group": "BlockBlast",
    "channel_type": "MULTI_CHANNEL",
    "last_op_type": "budget",
    "shows_7d": 13478462,
    "clicks_7d": 158359,
    "registers_7d": 32860,
    "roi_day30": 0.4797,
    "roi_day360": 1.2277,
    "roi_ratio_7_1": 2.71,
    "retention_day2": 0.38,
    "arpu_day1": 0.417
  }'
```

### 可传入的完整字段列表

| 字段 | 必填 | 说明 | 示例值 |
|------|------|------|--------|
| `cost_7d` | ✅ | 7 天折后消耗 | 1458520 |
| `revenue_7d` | ✅ | 7 天 SDK 收入 | 24586 |
| `cost_change_pct` | 建议 | 近 3 天 vs 前 3 天消耗变化 | -0.48 |
| `lifecycle_days` | 建议 | campaign 上线天数 | 53 |
| `daily_budget` | 建议 | 日预算 | 52000 |
| `app_group` | 建议 | BlockBlast/BlockCrush/Mahjong/Other | BlockBlast |
| `channel_type` | 可选 | MULTI_CHANNEL/SEARCH 等 | MULTI_CHANNEL |
| `last_op_type` | 可选 | 上次操作类型 | budget |
| `shows_7d` | 可选 | 7 天展示 | 13478462 |
| `clicks_7d` | 可选 | 7 天点击 | 158359 |
| `registers_7d` | 可选 | 7 天注册 | 32860 |
| `roi_day30` | 可选 | CK cohort: 30 天实际 ROI | 0.4797 |
| `roi_day360` | 可选 | CK cohort: 360 天实际 ROI | 1.2277 |
| `roi_ratio_7_1` | 可选 | CK cohort: ROI7/ROI1 倍率 | 2.71 |
| `retention_day2` | 可选 | CK cohort: 次留 | 0.38 |
| `arpu_day1` | 可选 | CK cohort: 首日 ARPU | 0.417 |

**ROI/LTV/留存/ARPU 指标从 CK `ads_market_roi_cohort_sdk_multidim` 表获取**，不调 MI。

---

## 真实 Campaign 列表（可直接用）

以下 campaign 在 CK 有真实消耗数据，可直接用于测试：

| Campaign 名 | App | 用途 |
|-------------|-----|------|
| `US-035-HK-XH-TachiPer020-横-260602` | Block Blast | 消耗最大（~20万/天） |
| `KR-035-HK-XH-Tachi-横-260328` | Block Blast | 老 campaign（~15万/天） |
| `US-035-HK-XH-TachiPer045-横-260602` | Block Blast | ~12万/天 |
| `UK-035-HK-XH-Tachi-横-260328` | Block Blast | ~10万/天 |
| `DE-035-HK-XH-Tachi-横-260328` | Block Blast | ~7万/天 |
| `CA-036-PUR-XH-250926-HK` | Block Crush | 历史上有 status 操作 |
| `EU-036-PUR-RC-250911-HK` | Block Crush | 历史上有 geo_exclude 操作 |

**注意**：campaign 名含中文（如"横"）需要 URL 编码，`横` → `%E6%A8%AA`。

---

## 输出字段说明

### 规则树输出

```json
{
  "prediction": {
    "predicted_action": "status",        // 操作类型
    "predicted_label": "status_pause",   // 完整标签（含方向）
    "direction": "pause",                // 方向
    "rule_path": [                       // 可读规则路径
      "lifecycle_days > 0.5000",
      "roi_day30 <= 0.2100",
      "cvr_7d <= 0.0200"
    ],
    "rule_support": 142,                 // 支持度（多少案例命中）
    "rule_confidence": 0.72              // 置信度
  },
  "did_effect": {                        // DiD 因果效应
    "did": 28623,                        // D14 效应
    "ci": [10638, 51884],               // 95% 置信区间
    "d7": 10205                          // D7 效应
  }
}
```

### RF 预测输出

```json
{
  "prediction": {
    "predicted_op": "status",            // 最可能操作
    "predicted_label": "status_pause",   // 完整标签
    "direction": "pause",                // 方向
    "probability": 0.39,                 // 概率
    "confidence": "medium"               // high/medium/low
  },
  "all_probabilities": [                 // 5 类排序
    {"label": "status_pause", "probability": 0.39},
    {"label": "budget_decrease", "probability": 0.19},
    ...
  ]
}
```

### 国家效应输出

```json
{
  "effect": {
    "14d": {
      "did": -1854,                      // DiD 效应
      "ci": [-5062, -78],               // 95% CI
      "placebo": -87,                    // 安慰剂（接近0=通过）
      "label": "effective"              // effective/harmful/insufficient_data
    }
  }
}
```

---

## 7 个标签含义

| 标签 | 含义 |
|------|------|
| `budget_increase` | 加预算 |
| `budget_decrease` | 降预算 |
| `bid_increase` | 加 tROAS（放量） |
| `bid_decrease` | 降 tROAS（收紧） |
| `status_pause` | 关停/暂停 |
| `geo_exclude_exclude` | 排除国家 |
| `creative_change` | 换素材 |
| `observe` | 继续观察（不操作） |
