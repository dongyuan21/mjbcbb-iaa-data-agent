# UA 决策行为沉淀 — 可解释规则树方案 v2（含完整 ROI/LTV/留存特征）

> 日期：2026-07-27
> 状态：design_draft（待用户确认）
> 上游：`UA决策行为沉淀_可解释规则树方案.md`（v1）+ CK cohort 表验证
> 替代：v1 方案（v1 特征不足，只有 16 个自算指标；v2 加入 20 个 cohort 指标）

## 一、为什么从 v1 升级到 v2

v1 的规则树只用 16 个特征（cost_7d/revenue_7d/roi_7d 等自算指标），f1≈0.50。问题在于 UA 决策时看的是 ROI360/LTV 倍率/留存这些长线指标，而不是 7 天窗口的自算 ROI。

v2 从 CK `ads_market_roi_cohort_sdk_multidim` 表加入 20 个 cohort 指标（ROI1~360、LTV 倍率、ARPU、留存），让模型看到 UA 的真实决策依据。不调 MI API，数据量可控。

## 二、输入输出

### 输入

**模式 1**：campaign 名称 → 自动从 CK 拉特征（cohort 表 + spend 表）
```bash
python3 ua_rule_tree.py --campaign "EU-036-PUR-RC-250911-HK"
```

**模式 2**：手动输入表现数据（含 cohort 指标）
```bash
python3 ua_rule_tree.py --manual '{
  "cost_7d": 50000,
  "roi_day360": 0.80,
  "roi_day30": 0.31,
  "retention_day2": 0.40,
  "roi_ratio_60_30": 1.32,
  ...
}'
```

模式 2 必填：`cost_7d`、`revenue_7d`。其余可选，不填默认 0。

### 输出

```json
{
  "campaign_name": "EU-036-PUR-RC-250911-HK",
  "predicted_action": "status_pause",
  "predicted_label": "status_pause",
  "rule_path": "IF roi_day360 < 0.85 AND retention_day2 < 0.45 AND lifecycle_days > 60 → status_pause",
  "rule_support": 142,
  "rule_confidence": 0.72,
  "did_effect": {
    "did": 28623,
    "ci": [10638, 51884],
    "label": "effective"
  },
  "all_rules": [
    {
      "action": "status_pause",
      "conditions": "roi_day360 < 0.85 ∧ retention_day2 < 0.45 ∧ lifecycle_days > 60",
      "support": 142,
      "confidence": 0.72,
      "did_d14": 28623
    },
    {
      "action": "observe",
      "conditions": "roi_day360 ≥ 0.85 AND cost_change_pct < 0.20",
      "support": 76,
      "confidence": 0.58,
      "did_d14": null
    },
    {
      "action": "creative_change",
      "conditions": "retention_day7 < 0.25 AND roi_ratio_7_1 < 2.0",
      "support": 40,
      "confidence": 0.55,
      "did_d14": -44829
    }
  ],
  "features_used": {
    "roi_day360": 0.80,
    "roi_day30": 0.31,
    "retention_day2": 0.41,
    "roi_ratio_60_30": 1.32,
    ...
  },
  "model_info": {
    "algorithm": "DecisionTreeClassifier (depth=4, min_samples_leaf=30)",
    "n_features": 31,
    "n_training_samples": 3347,
    "n_rules": 12,
    "boundary": "rule_based_not_prescriptive"
  }
}
```

## 三、全部特征清单（31 个）

### A. ROI 系列（8 个）— CK `ads_market_roi_cohort_sdk_multidim`

| # | 特征名 | CK 列 | 含义 |
|---|--------|------|------|
| 1 | `roi_day1` | `sdk_roi_day1` | 首日实际 ROI |
| 2 | `roi_day7` | `sdk_roi_day7` | 7 日实际 ROI |
| 3 | `roi_day14` | `sdk_roi_day14` | 14 日实际 ROI |
| 4 | `roi_day30` | `sdk_roi_day30` | 30 日实际 ROI |
| 5 | `roi_day60` | `sdk_roi_day60` | 60 日实际 ROI |
| 6 | `roi_day90` | `sdk_roi_day90` | 90 日实际 ROI |
| 7 | `roi_day180` | `sdk_roi_day180` | 180 日实际 ROI |
| 8 | `roi_day360` | `sdk_roi_day360` | 360 日实际 ROI |

### B. ROI 倍率/回收趋势（6 个）— 同表

| # | 特征名 | CK 列 | 含义 |
|---|--------|------|------|
| 9 | `roi_ratio_7_1` | `sdk_roi_ratio_7_1` | ROI7/ROI1，回收速度 |
| 10 | `roi_ratio_30_14` | `sdk_roi_ratio_30_14` | ROI30/ROI14，中期增速 |
| 11 | `roi_ratio_60_30` | `sdk_roi_ratio_60_30` | ROI60/ROI30，长期增速 |
| 12 | `roi_ratio_90_60` | `sdk_roi_ratio_90_60` | ROI90/ROI60，长线增速 |
| 13 | `roi_ratio_180_150` | `sdk_roi_ratio_180_150` | ROI180/ROI150，半年增速 |
| 14 | `roi_ratio_360_300` | `sdk_roi_ratio_360_300` | ROI360/ROI300，终极增速 |

### C. ARPU（3 个）— 同表

| # | 特征名 | CK 列 | 含义 |
|---|--------|------|------|
| 15 | `arpu_day1` | `sdk_arpu_day1` | 首日 ARPU |
| 16 | `arpu_day7` | `sdk_arpu_day7` | 7 日 ARPU |
| 17 | `arpu_day30` | `sdk_arpu_day30` | 30 日 ARPU |

### D. 留存（3 个）— 同表

| # | 特征名 | CK 列 | 含义 |
|---|--------|------|------|
| 18 | `retention_day2` | `sdk_retention_day2` | 次日留存率 |
| 19 | `retention_day7` | `sdk_retention_day7` | 7 日留存率 |
| 20 | `retention_day30` | `sdk_retention_day30` | 30 日留存率 |

### E. 消耗/成本/转化（5 个）— CK `tj_ad_spend_active_v2`（已有）

| # | 特征名 | 来源 | 含义 |
|---|--------|------|------|
| 21 | `cost_7d` | spend 表 7天 sum | 7 天折后消耗 |
| 22 | `cost_change_pct` | spend 表近3天 vs 前3天 | 消耗趋势 |
| 23 | `cpi_7d` | cost_7d / registers_7d | 注册成本 |
| 24 | `ctr_7d` | clicks / shows | 点击率 |
| 25 | `cvr_7d` | registers / clicks | 转化率 |

### F. 历史/元数据（3 个）— 已有

| # | 特征名 | 来源 | 含义 |
|---|--------|------|------|
| 26 | `lifecycle_days` | campaign_start_date → 操作日 | 上线天数 |
| 27 | `daily_budget` | Google change_event 宽表 | 日预算 |
| 28 | `last_op_type` | 历史操作序列 | 上次操作类型 |

### G. 类别特征（3 个）— 已有

| # | 特征名 | 取值 |
|---|--------|------|
| 29 | `app_group` | BlockBlast / BlockCrush / Mahjong / Other |
| 30 | `channel_type` | MULTI_CHANNEL / SEARCH / ... |
| 31 | `last_op_type` | budget / bid / status / geo_exclude / creative / observe / none |

### 不加入的指标

- **预估指标**：roi_360_3d/7d/14d/30d、roi_trend_360（用户要求先不加）
- **卸载率**：uninstall_rate_*（跟留存强相关，避免冗余）
- **逐日收入**：revenue_0~revenue_359（已被 ROI 和 ARPU 覆盖）
- **逐日 LTV**：ltv_1~ltv_360（已被 ROI 和 ROI 倍率覆盖）

## 四、标签体系

6 类（含 observe）：

| 标签 | 含义 | 样本量 | 占比 |
|------|------|--------|------|
| geo_exclude | 排除国家 | 757 | 22.6% |
| observe | 继续观察（不操作） | 729 | 21.8% |
| budget | 调预算 | 558 | 16.7% |
| status | 开关 campaign | 556 | 16.6% |
| bid | 调出价 | 474 | 14.2% |
| creative | 换素材 | 273 | 8.2% |

方向在规则树预测后用方案 A 规则判断（跟 ua_predict.py 一致）。

## 五、数据来源与查询方式

### cohort 指标（#1-#20）

```sql
SELECT
  campaign_name,
  sdk_roi_day1, sdk_roi_day7, sdk_roi_day14, sdk_roi_day30,
  sdk_roi_day60, sdk_roi_day90, sdk_roi_day180, sdk_roi_day360,
  sdk_roi_ratio_7_1, sdk_roi_ratio_30_14, sdk_roi_ratio_60_30,
  sdk_roi_ratio_90_60, sdk_roi_ratio_180_150, sdk_roi_ratio_360_300,
  sdk_arpu_day1, sdk_arpu_day7, sdk_arpu_day30,
  sdk_retention_day2, sdk_retention_day7, sdk_retention_day30
FROM shucang_market.ads_market_roi_cohort_sdk_multidim
WHERE active_date = '{操作前1天}'
  AND media_source = 'googleadwords_int'
  AND dim_level = 'bundle_media_campaign'
  AND bundle_id = '{bundle_id}'
  AND campaign_name = '{campaign_name}'
  AND cost_zhe > 0
```

**point-in-time 保证**：取操作前一天的 `active_date` 分区。ROI360 是该 campaign 从上线到那天的累计回收率，不会泄漏未来数据。

**注意**：`dim_level='bundle_media_campaign'` 是 campaign 级聚合。如果同一天同一 campaign 有多行（不同 country_group），需要先聚合或确认 dim_level 过滤后是一行。

### spend 指标（#21-#25）— 已有

从 `tj_ad_spend_active_v2` 按 campaign_name + active_date 聚合 7 天。

### 元数据（#26-#28）— 已有

从 all_rows.jsonl 或 Google change_event 宽表取。

## 六、实现方案

### 新增脚本

| 脚本 | 行数 | 说明 |
|------|------|------|
| `tools/scripts/ua_rule_tree.py` | ~200 行 | 规则树训练 + 规则提取 + 预测 + CLI |
| `runtime/backend/app/services/ua_rule_tree_service.py` | ~30 行 | FastAPI 薄包装 |

### 核心流程

```
1. 加载 all_rows.jsonl（3347 条，含 observe）
2. 对每条样本，按 change_date 前一天从 CK cohort 表拉 20 个指标
3. 合并已有 11 个特征 → 31 个特征
4. DecisionTreeClassifier(depth=4, min_samples_leaf=30) 训练
5. 从树中提取所有叶节点规则
6. 每条规则附加：支持度 + 置信度 + DiD 效应
7. 预测：输入 campaign → 拉特征 → 走树 → 输出规则 + 效应
```

### 关键参数

```python
DecisionTreeClassifier(
    max_depth=4,           # 浅树，规则不超过 4 层 if-else
    min_samples_leaf=30,   # 每个叶节点至少 30 条案例
    class_weight='balanced',
    random_state=42,
)
```

### 规则提取

用 `sklearn.tree` 的 `tree_` 属性遍历节点，把每个叶节点的路径转成可读规则：

```python
# 示例输出
IF roi_day360 < 0.85
  AND retention_day2 < 0.45
  AND lifecycle_days > 62
  → status_pause (support=142, confidence=0.72)
```

### API 接口

```python
# CLI
python3 ua_rule_tree.py --campaign "X"
python3 ua_rule_tree.py --manual '{"cost_7d": 50000, "roi_day360": 0.80}'
python3 ua_rule_tree.py --export-rules  # 导出全部规则

# FastAPI
GET  /api/ua/rule-tree?campaign=X
POST /api/ua/rule-tree/manual
GET  /api/ua/rule-tree/rules  # 列出所有规则
```

### 工具注册

在 `tool_registry.py` 加第 4 个工具 `ua_rule_tree`。

## 七、预期规则样例

### 规则 1：低 ROI360 + 低留存 → 关停

```
IF roi_day360 < 0.85
  AND retention_day2 < 0.45
  AND lifecycle_days > 62
  → status_pause
  support: 142, confidence: 0.72
  DiD D14: +28623 (CI [+10638, +51884], 安慰剂通过)
```

解读：360 天回收不到 85%、次日留存低于 45%、上线超 2 个月的 campaign，UA 倾向关停。历史上关停后 14 天利润提升 28623。

### 规则 2：高 ROI360 + 消耗稳定 → 观察

```
IF roi_day360 >= 0.85
  AND cost_change_pct < 0.20
  → observe
  support: 76, confidence: 0.58
  DiD: null（不操作）
```

解读：360 天回收达 85% 以上且消耗稳定，UA 倾向继续观察不动。

### 规则 3：低留存 + 慢回收 → 换素材

```
IF retention_day7 < 0.25
  AND roi_ratio_7_1 < 2.0
  → creative_change
  support: 40, confidence: 0.55
  DiD D14: -44829 (CI [-67445, -25214], 安慰剂通过)
```

解读：7 日留存低于 25%、7 天回收倍率不到 2 倍，UA 倾向换素材。注意换素材后 14 天利润会下降（学习期阵痛）。

### 规则 4：回收增速放缓 → 降预算

```
IF roi_day360 >= 0.85
  AND roi_ratio_60_30 < 1.25
  AND cost_change_pct < 0.10
  → budget_decrease
  support: 89, confidence: 0.65
  DiD D14: -17654 (CI [-31577, -2513], 安慰剂通过)
```

解读：360 天回收达标但 60→30 增速低于 1.25 倍（回收到顶），且消耗稳定，UA 倾向降预算收缩。

## 八、验证方式

1. `python3 ua_rule_tree.py --export-rules` 导出全部规则
2. UA 团队逐条审核：
   - "ROI360 < 85% 且留存低就关停"——对不对？
   - "回收增速放缓就降预算"——对不对？
   - "低留存 + 慢回收就换素材"——对不对？
3. 规则对→模型学到了 UA 真实逻辑；规则不对→发现隐性决策因素

## 九、跟现有工具的关系

| 工具 | 回答的问题 | 方法 | 特征数 |
|------|----------|------|--------|
| ua_predict | UA **会**做什么 | RF 概率 | 19 |
| **ua_rule_tree** | UA 在什么条件下做什么 | **规则树 + DiD** | **31** |
| ua_country_effect | 做了之后**效果如何** | DiD | — |

规则树特征比 RF 多 12 个（cohort 指标），且输出可读可验证。

## 十、工作量

| 项 | 工作量 |
|----|--------|
| `ua_rule_tree.py`（训练+规则提取+预测+CLI） | ~200 行 |
| cohort 特征拉取函数（CK 查询） | ~50 行 |
| `ua_rule_tree_service.py`（FastAPI） | ~30 行 |
| `tool_registry.py` + `main.py`（注册+路由） | ~35 行 |
| 测试 | ~50 行 |
| **总计** | **~365 行** |

## 十一、风险

| 风险 | 缓解 |
|------|------|
| cohort 表某些 campaign 缺数据（新 campaign 没有 ROI360） | 缺失值填 0，规则树自然处理 |
| cohort 表 dim_level 过滤后仍有多行 | 加 `GROUP BY campaign_name` 聚合 |
| 31 个特征在 depth=4 的树上可能过于稀疏 | min_samples_leaf=30 保证统计意义 |
| ROI360 对新 campaign 为 0（上线不到 360 天） | 规则树会学到"roi_day360=0 → 用 roi_day30 替代判断" |
| 某类操作规则不显著 | 不够 30 条不出规则，标 insufficient_data |

## 十二、与 v1 方案的区别

| 维度 | v1 | v2 |
|------|-----|-----|
| 特征数 | 19（16 数值 + 3 类别） | **31（28 数值 + 3 类别）** |
| ROI 指标 | 自算 roi_7d（1 个） | **ROI1/7/14/30/60/90/180/360（8 个）** |
| LTV 倍率 | 无 | **6 个（7/1, 30/14, 60/30, 90/60, 180/150, 360/300）** |
| ARPU | 无 | **3 个（1/7/30 天）** |
| 留存 | 无 | **3 个（次留/7留/30留）** |
| 数据来源 | CK spend 表自算 | **CK cohort 表（已算好）+ spend 表** |
| 预期 f1 | ~0.50 | **~0.60+**（cohort 指标信息量大） |
| 规则可读性 | IF roi_7d < 0.3 | **IF roi_day360 < 0.85**（UA 直接看懂） |
