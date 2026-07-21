# AppLovin / Partner / XMP / admarket 草稿

```yaml
id: draft_applovin_partner_ops
status: draft
needs_review: true
target_layer:
  - 语义层待补清单.md
  - TODO/后续待办.md
source_docs:
  - ~/hungrystudio/obsidain/lzyzsere/8方块/02_知识库/投放/AppLovin渠道扫盲.md
  - ~/hungrystudio/obsidain/lzyzsere/8方块/02_知识库/投放/XMP.md
  - ~/hungrystudio/obsidain/lzyzsere/8方块/02_知识库/产品与公司/admarket平台速查_20260508.md
as_of_date: 2026-05
conflicts_with: []
review_notes:
  - API key、平台 URL、权限细节不进入正式 agent 召回。
  - AppLovin 自动化属于 future agent POC，不是当前只读 data agent 范围。
```

## AppLovin 角色

8方块中将 AppLovin 拆成：

| 模块 | 角色 |
|---|---|
| AppDiscovery / Axon Ads Manager | 广告主侧 UA 投放平台 |
| MAX | App 发行商侧广告变现 mediation |
| AXON | 连接 UA 与变现侧的算法引擎 |

对纯 IAA 游戏的关键点：

- IAA ROAS 依赖广告变现回传。
- MAX 接入完整度会影响能否跑 IAA ROAS / Blended ROAS。
- AppLovin 对数据回传完整性敏感，MMP 配置和自然量回传会影响训练样本。

## AppLovin campaign 类型草稿

| 类型 | 适用性 | 备注 |
|---|---|---|
| CPI | 起步、新国家试水 | 适合冷启动 |
| CPE | 自定义参与事件 | 可作为虚拟点位过渡目标 |
| CPP / IAP ROAS | IAP 主导 | 纯 IAA 默认不适用 |
| IAA ROAS | 纯 IAA 核心方向 | 依赖 MAX / ad revenue 回传 |
| Retargeting | 召回老用户 | 待 LTV 倍率体系成熟后评估 |

待审核：

- 当前公司 AppLovin 具体可用 campaign 类型、MAX 接入状态、IAA ROAS 是否全产品可跑。

## AppLovin 操作风险候选

| 风险 | 业务含义 |
|---|---|
| MMP 回传不全 | AXON 训练样本偏，影响 CPI 与 LTV |
| 预算/出价频繁调整 | 学习期中断；需要观察窗口 |
| 国家切太碎 | 单 campaign 每日事件不足，学习不稳定 |
| 素材疲劳 | 视频 / playable 需定期换新 |
| 首日高、长期倍率低 | 需要看 AppLovin cohort 的 LTV1/LTV30 倍率 |

## XMP 与 admarket 分工

8方块中对公司实际工作流的候选认知：

| 平台 | 角色 |
|---|---|
| admarket | 公司投放运营 BI，看跨产品、跨渠道、长周期数据 |
| XMP | 投放优化师日常操作工具，跨渠道改 bid/budget、上素材、AI 盯盘 |
| AF | MMP，归因与数据基础设施 |
| partner 后台 | 特定功能/补充排查，不是 PM 日常主入口 |

候选结论：

- PM 看数优先 admarket。
- 投放操作优先 XMP。
- AF 是归因基础设施，不能被 XMP 替代。

## 对 data agent 的价值

本草稿适合 future agent POC，而不是当前 SQL-only 知识库：

- 可用于回答“某渠道怎么查/怎么操作”的路径问题。
- 可用于解释为什么 AppLovin 需要看 LTV 倍率而不只看 D1。
- 可用于后续自动化投放 agent 的安全边界：默认只读，不直接改 budget/bid。

## 不 promote 的内容

- API key 获取路径、key 类型、具体鉴权细节。
- 内网 URL、账户权限、个人权限状态。
- IM 原文和个人名字。

## 待审核点

1. AppLovin IAA ROAS 对 MAX 接入的要求是否已经在当前产品上满足。
2. XMP 是否有可供 agent 使用的只读 API / 导出能力。
3. admarket 与 `ai_ck` / MI ROI360 的数据关系是否能打通。
4. AppLovin 的 7/28 天优化窗口是否进入正式语义层。
