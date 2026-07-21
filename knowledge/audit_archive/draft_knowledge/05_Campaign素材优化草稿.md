# Campaign / 素材 / 优化目标草稿

```yaml
id: draft_campaign_material_optimization
status: draft
needs_review: true
target_layer:
  - 语义层待补清单.md
  - da_assets/analysis_sop
  - da_assets/decision_cases
source_docs:
  - ~/hungrystudio/obsidain/lzyzsere/8方块/00_进行中/P1-素材冷启动优化工作方案.md
  - ~/hungrystudio/obsidain/lzyzsere/8方块/00_进行中/根据capaign承接/README.md
  - ~/hungrystudio/obsidain/lzyzsere/8方块/00_进行中/根据capaign承接/02_命名规范_v1.md
  - ~/hungrystudio/obsidain/lzyzsere/8方块/02_知识库/投放/老板口径沉淀_优化目标分层_20260508.md
  - ~/hungrystudio/obsidain/lzyzsere/8方块/02_知识库/投放/广告优化目标分层金字塔_20260508.md
as_of_date: 2026-05
conflicts_with: []
review_notes:
  - campaign gameplay metadata 仍是 v1.1 草稿，不能作为生产规范。
  - 老板口径中的 CPA 数字是案例锚点，不可泛化为全局阈值。
```

## 优化目标分层候选

8方块中的内部优化目标分层：

| 层级 | 含义 | 用途 |
|---|---|---|
| 1.0 Install | 按安装优化 | 广泛拉新、冷启动、新地区试水 |
| 2.0 Event | 浅层关键行为 | 次留、关键动作等早期质量信号 |
| 2.5 CPE / Event | 中深层事件 + 价值出价 | 成本与质量平衡，反馈比 ROAS 更早 |
| 3.0 ROAS | 价值回收优化 | 更硬的商业结果，但成本可能更高 |

草稿结论：

- 当 ROAS 路径 CPA 过高时，可以用 2.5 CPE/Event 做“成本-质量平衡点”。
- 2.5 事件需要证明与长期 ROAS/LTV 有相关性。
- 具体 CPA 数字只作为历史案例，不作为全局阈值。

## 素材冷启动候选知识

素材冷启动的目标：

- 提升冷启动起量率。
- 减少无效素材预算浪费。
- 降低人工筛选工作量。

候选特征体系：

| 维度 | 示例 |
|---|---|
| 内容类型 | 玩法实机、UGC 小剧场、Meme、吉祥物动画 |
| 情绪调性 | 搞笑、紧张、治愈、爽快 |
| 时长结构 | 前 3 秒钩子、中段节奏、结尾 CTA |
| 元素识别 | 人物出镜、文字占比、BGM、素材尺寸 |
| 投放上下文 | 地区、时段、受众、渠道 |
| 历史相似素材 | CTR、IPM、CPI、ROAS、起量率 |

候选评分：

```text
冷启动评分 = w1 × 起量概率预测 + w2 × 历史相似素材表现 + w3 × 标签质量分
```

待审核：

- 权重 60/30/10 是方案草稿，不应直接作为生产规则。
- 评分区间 >80、60-80、<60 是草稿，需历史数据验证。

## Campaign gameplay metadata 草稿

8方块 campaign 承接方案提出：不要改 partner 端 `campaign_name`，而是维护 metadata 表：

```text
dim_campaign_gameplay_mapping:
  campaign_id
  campaign_name
  media_source
  bundle_id
  gameplay
  gameplay_purity
  primary_creative_type
  review_owner
  reviewed_at
  status
  notes
```

候选规则：

| 字段 | 含义 |
|---|---|
| `gameplay=2he` | 主跑二合方向素材 |
| `gameplay=4gong` | 主跑四宫方向素材 |
| `mixed` | 方向混合，不进实验 |
| `other` | 无明确方向或召回等非实验 |

重要原则：

- 不强制改 partner 端 campaign_name，避免归因连续性风险。
- 客户端/后端用 `campaign_id` lookup metadata，决定玩法分支。
- 异常/缺失时默认走原玩法。

待审核：

- 该方案是 MJB 玩法承接场景，不应直接泛化到 BB 点位平台。
- 表名、schema、owner、是否已落地都需要确认。

## 可进入 data agent 的判断规则候选

| 现象 | 候选判断 |
|---|---|
| 新素材无量 | 先看 IPM / CTR / 前 3 秒标签，不只看 CPI |
| 素材起量后 ROI 差 | 拆 LTV1、LTV7、LTV 倍率，不只看 D1 |
| campaign 内容与玩法不匹配 | 需要 metadata 或命名规范补充业务语义 |
| ROAS 成本过高 | 可评估是否用中深层事件 CPE 过渡 |
| campaign_name 异构 | 不 parse 名称作为唯一依据，优先 metadata lookup |

## Promote 建议

- `../语义层待补清单.md`：补“素材冷启动指标”和“campaign metadata”待补项。
- `da_assets/analysis_sop/`：沉淀“素材冷启动分析 SOP”“campaign玩法承接分析 SOP”。
- `da_assets/decision_cases/`：MJB 二合/四宫实验可作为后续 decision case。

## 风险

- 进行中文档时效性强，需标 `as_of_date` 和 `status=draft`。
- 人名、IM 草稿不进入正式知识库。
- 玩法承接 SQL 示例中的日期/表名/字段需要重新验证。
