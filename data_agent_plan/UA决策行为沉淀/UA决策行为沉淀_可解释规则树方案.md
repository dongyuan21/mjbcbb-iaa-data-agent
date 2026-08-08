# UA 决策行为沉淀 — 可解释规则树方案

> 日期：2026-07-27
> 状态：design_draft（待用户确认）
> 上游：`UA决策行为沉淀交接文档.md` + `tools/scripts/ua_predict.py`

## 一、为什么做规则树

当前 RF 模型 macro_f1=0.64，但 300 棵深树人看不懂，UA 无法验证。规则树用 1 棵浅树（depth=3~4）把 UA 的决策逻辑挖成可读的 if-then 规则，让 UA 团队能直接验证。

## 二、输入输出

### 输入

两种模式（跟 ua_predict.py 一致）：

**模式 1**：campaign 名称 → 自动从 CK 拉特征
```bash
python3 ua_rule_tree.py --campaign "EU-036-PUR-RC-250911-HK"
```

**模式 2**：手动输入表现数据
```bash
python3 ua_rule_tree.py --manual '{"cost_7d": 50000, "revenue_7d": 2500, "cost_change_pct": 0.35}'
```

### 输出

```json
{
  "campaign_name": "EU-036-PUR-RC-250911-HK",
  "predicted_action": "status_pause",
  "predicted_label": "status_pause",
  "rule_path": "IF roi_7d < 0.30 AND lifecycle_days > 62 → status_pause",
  "rule_support": 142,
  "rule_confidence": 0.72,
  "diD_effect": {
    "did": 28623,
    "ci": [10638, 51884],
    "label": "effective"
  },
  "all_rules": [
    {
      "action": "status_pause",
      "conditions": "roi_7d < 0.30 ∧ lifecycle_days > 62",
      "support": 142,
      "confidence": 0.72,
      "did_d14": 28623
    },
    {
      "action": "observe",
      "conditions": "roi_7d ≥ 0.50 ∧ cost_change_pct < 0.20",
      "support": 76,
      "confidence": 0.58,
      "did_d14": null
    },
    {
      "action": "budget_decrease",
      "conditions": "roi_7d ≥ 0.80 ∧ cost_change_pct < 0.10",
      "support": 89,
      "confidence": 0.65,
      "did_d14": -17654
    }
  ],
  "model_info": {
    "algorithm": "DecisionTreeClassifier (depth=4, min_samples_leaf=30)",
    "train_macro_f1": "~0.50",
    "n_rules": 12,
    "n_training_samples": 3347,
    "boundary": "rule_based_not_prescriptive: 提取 UA 历史决策规则供参考，不输出投放建议"
  }
}
```

### 跟 RF 预测的区别

| 维度 | RF（ua_predict.py） | 规则树（ua_rule_tree.py） |
|------|--------------------|-------------------------|
| 输出 | 5 类概率排序 | 6 类含 observe + **规则路径** |
| 能看规则吗 | 不能 | **能**（IF roi<0.3 AND lifecycle>62 → pause） |
| 规则支持度 | 无 | **有**（142 条案例支持这条规则） |
| DiD 效应 | 无 | **有**（按这条规则操作的案例 D14 利润 +28623） |
| UA 能验证吗 | 不能 | **能**（规则是人话，UA 一眼看懂） |
| f1 | 0.64 | ~0.50 |

## 三、标签体系

6 类（比 RF 多一个 observe）：

| 标签 | 含义 | 样本量 | 占比 |
|------|------|--------|------|
| geo_exclude | 排除国家 | 757 | 22.6% |
| observe | 继续观察（不操作） | 729 | 21.8% |
| budget | 调预算 | 558 | 16.7% |
| status | 开关 campaign | 556 | 16.6% |
| bid | 调出价 | 474 | 14.2% |
| creative | 换素材 | 273 | 8.2% |

observe 来自 MI 备注（l0=observe），表示 UA 看了数据但选择不操作。这让规则树能输出"继续观察"而不只是"做什么操作"。

方向在规则树预测后再用方案 A 的规则判断（跟 ua_predict.py 一致）。

## 四、数据够不够

**够。** 3347 条训练数据，6 类分布均衡（最少 273 条）。规则树是浅树（depth=4），不需要太多数据——实际上 3347 条对 depth=4 的树来说绰绰有余。

## 五、实现方案

### 脚本：`tools/scripts/ua_rule_tree.py`

**核心流程**：
1. 加载 all_rows.jsonl（3347 条，含 observe）
2. 用 sklearn DecisionTreeClassifier (depth=4, min_samples_leaf=30) 训练
3. 从树中提取所有叶节点规则（IF...THEN...）
4. 每条规则附加：支持度（多少案例命中）、置信度、DiD 效应
5. 预测时：输入 campaign → 拉特征 → 走树到叶节点 → 输出规则 + 效应

**关键参数**：
```python
DecisionTreeClassifier(
    max_depth=4,           # 浅树，规则不超过 4 层 if-else
    min_samples_leaf=30,   # 每个叶节点至少 30 条案例，保证统计意义
    class_weight='balanced',
    random_state=42,
)
```

**规则提取**：用 `sklearn.tree.export_text()` 或手动遍历 `tree_.children_left/right`，把每个叶节点的路径转成可读规则。

### 特征（跟 RF 一致）

```python
NUMERIC_FEATS = [
    'cost_14d', 'cost_7d', 'revenue_7d', 'roi_7d',
    'cpi_7d', 'ctr_7d', 'cvr_7d', 'shows_7d', 'clicks_7d', 'registers_7d',
    'cost_change_pct',
    'days_since_last_op', 'op_type_count_14d',
    'daily_budget', 'target_cpa', 'lifecycle_days',
]
CAT_FEATS = ['app_group', 'channel_type', 'last_op_type']
```

### 规则跟 DiD 的结合

每条规则命中一批历史案例。对这批案例：
- 如果是 operate 类（budget/bid/status/geo_exclude/creative），查它们对应的 DiD 效应
- 如果是 observe，DiD 为 null（没有操作就没有效应）

### API 接口

```python
# CLI
python3 ua_rule_tree.py --campaign "X"
python3 ua_rule_tree.py --manual '{"cost_7d": 50000, "revenue_7d": 2500}'
python3 ua_rule_tree.py --export-rules  # 导出全部规则到 JSON

# FastAPI
GET  /api/ua/rule-tree?campaign=X
POST /api/ua/rule-tree/manual
GET  /api/ua/rule-tree/rules  # 列出所有规则
```

### 工具注册

在 `tool_registry.py` 加第 4 个工具：
```python
UA_RULE_TREE_TOOL_ID = "ua_rule_tree"
```

## 六、预期输出样例

### 场景 1：低 ROI + 老 campaign

输入：`roi_7d=0.05, lifecycle_days=281, cost_change_pct=-0.43`

```
规则路径: IF roi_7d < 0.30 AND lifecycle_days > 62 → status_pause
支持度: 142 条案例
置信度: 72%
DiD 效应: +28623 (CI [+10638, +51884], 安慰剂通过)

→ 建议: 关停。历史上 ROI<30% 且上线>62天的 campaign，
  UA 关停后 14 天利润平均提升 28623 元。
```

### 场景 2：中等 ROI + 消耗稳定

输入：`roi_7d=0.65, cost_change_pct=0.05, lifecycle_days=100`

```
规则路径: IF roi_7d ≥ 0.50 AND cost_change_pct < 0.20 → observe
支持度: 76 条案例
置信度: 58%
DiD 效应: null（不操作）

→ 建议: 继续观察。ROI 还行且消耗稳定，UA 历史上这种情况选择不动。
```

### 场景 3：高 ROI + 消耗稳定

输入：`roi_7d=2.0, cost_change_pct=0.05`

```
规则路径: IF roi_7d ≥ 0.80 AND cost_change_pct < 0.10 → budget_decrease
支持度: 89 条案例
置信度: 65%
DiD 效应: -17654 (CI [-31577, -2513], 安慰剂通过)

→ 建议: 降预算。ROI 高且消耗稳定，UA 历史上这种情况收缩预算。
  注意：降预算后 14 天利润平均下降 17654（可能是收缩导致量级减少）。
```

## 七、验证方式

规则树的最大价值是 UA 能验证。验证步骤：

1. `python3 ua_rule_tree.py --export-rules` 导出全部规则
2. UA 团队逐条审核：
   - "ROI < 30% 且上线 > 62 天就关停"——这条对不对？
   - "ROI ≥ 80% 且消耗稳定就降预算"——这条对不对？
3. 如果某条规则不对，说明：
   - 要么 UA 有隐性规则没被特征捕捉（比如竞品动态、素材库存）
   - 要么数据有偏差（比如 MI observe 样本不纯）
4. 如果规则对，说明模型学到了 UA 的真实决策逻辑

## 八、跟现有工具的关系

| 工具 | 回答的问题 | 方法 |
|------|----------|------|
| ua_predict | UA **会**做什么 | RF 概率 |
| **ua_rule_tree** | UA 在什么条件下做什么 | **规则树 + DiD 效应** |
| ua_country_effect | 做了之后**效果如何** | DiD 因果估计 |

三个工具互补：规则树给可验证的规则，RF 给概率，country effect 给因果证据。

## 九、工作量

- `ua_rule_tree.py`：~150 行（训练 + 规则提取 + 预测 + CLI）
- `ua_rule_tree_service.py`：~30 行（FastAPI 薄包装）
- `tool_registry.py`：+20 行（注册第 4 个工具）
- `main.py`：+15 行（API 路由）
- 测试：~50 行

总计 ~265 行，半天能做完。

## 十、风险

| 风险 | 缓解 |
|------|------|
| depth=4 的规则太粗 | 可以调 depth=5~6，但规则会变难读 |
| observe 样本不纯（MI 备注"持续关注"可能包含非 Google 操作） | 在规则输出时标注 evidence_tier |
| 规则置信度低（<50%） | 输出时标 `low_confidence`，提示"参考价值有限" |
| 某类操作（creative 273 条）规则不显著 | min_samples_leaf=30 保证统计意义，不够就不出规则 |
