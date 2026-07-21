# MI 平台其他模块业务协议

> **来源**：nexus 工程 `backend/boards/internal/` 下投放内容池、Google 实验、GP Store、KOL 视频效果、预测服务集成五个模块的源码蒸馏。
>
> **蒸馏日期**：2026-06-20
>
> **用途**：为 Data Agent 回答涉及 MI 平台非 ROI360 核心链路的报表、实验、商店数据、KOL 效果、预测服务问题时提供业务语义参考。

---

## 投放内容池（Delivery Content）

### 模块用途

管理 KOL / 官号视频在 TikTok 等社媒平台的投放素材池，提供内容筛选、播放/互动指标查看、投放状态追踪和停投预警。共包含四个子报表：

| 报表类型标识 | 说明 |
|---|---|
| `delivery_content` | 投放内容池列表（主报表） |
| `delivery_content_funnel` | 内容漏斗分析 |
| `sparkcode_query` | Spark Code 查询 |
| `delivery_content_stop` | 停投内容明细 |

### 核心维度

- **视频属性**：video_id、video_name、title、origin_title、link、video_type、platform、duration、creative、video_first_label、video_second_label、spark_code、sparkcode_remark、code_remark
- **达人属性**：kol_name、influencer_type、sparkcode_unique_id、sparkcode_iterm_id
- **分类筛选**：media_source（媒体）、country（国家）、language（语言）、kol_type（视频源：拓展/官号）、has_sparkcode（Spark Code 标识：有/无）
- **人员**：delivery_user（投流人）、kol_user（拓展人）
- **时间**：publish_time（发布时间）、first_delivery_date（首次投流时间）、last_delivery_date（最近投流时间）、sparkcode_start_at、sparkcode_end_at、created_at（Spark Code 上传时间）
- **状态**：delivery_status（投放状态）、can_delivery（是否可投放）、has_delivery（是否已投流）、yesterday_delivery（昨日是否投流）

### 核心指标

| 指标名 | 说明 |
|---|---|
| delivery_cost | 总花费 |
| day_one_views | Day1 播放数 |
| all_views | 总播放数 |
| all_delivery_views | 总投流播放数 |
| all_ua_views | 总 UA 播放数 |
| all_nature_views | 总自然播放数 |
| all_likes | 总点赞数 |
| all_comments | 总评论数 |
| all_shares | 总分享数 |
| stop_delivery_days | 停投天数 |

### 关键业务规则

1. **投放状态枚举**：spark_code_timeout（授权过期）、stop_more_7/15/30/45（停投 7-15/15-30/30-45/>45 天）、wait_delivery（待投放）、spark_code_missing（无 Spark Code 标记）、cannot_deli（无法投放）、stop_less_7（近 7 天投放）。
2. **kol_type 映射**：CLUE → 拓展，OA → 官号。
3. **publish_time 日期字段实际存储为 ClickHouse `date` 整型**，筛选条件中通过 `toString(toDate(toString(date)))` 转换。
4. **权限资源**：`KOL_VIDEO_EFFECT_PAID`。

### 涉及的数据表

MI 平台内部 MySQL / ClickHouse 表，通过 `Repository` 查询，字段 `Where` 映射直接指向表列名（如 `media_source`、`video_id`、`country` 等）。

### 与投放/ROI 体系的关系

投放内容池是 KOL 投放素材的运营管理视图，为投流人提供可投放内容的筛选和状态追踪。其播放/花费指标与 KOL 视频效果报表共享底层数据，但粒度和关注点不同：内容池侧重素材资源管理和投放可用性，KOL 效果报表侧重投放效果归因和 CPM 计算。

---

## Google 实验（GP Experiment）

### 模块用途

消费 Kafka 消息，将 Google Play Console 的商品详情页 A/B 实验（Listing Experiment）数据采集入库并持续更新。记录实验每日安装数时序（Day1–Day100）和实验素材（icon、横图、视频、版式等）。

### 消息结构

Kafka 消息反序列化为 `GoogleMessage`，核心结构：

- **GoogleData**：experimentId、experimentName、appId、metricCode、experimentStartTime（北京时间）
- **Variant[]**：每个实验组包含 name、series（时序点位）和 imgs（icon/top/phone/7inch/10inch 图片集合）
- **VariantsSeriesPoints**：timeBeijing + value，取 15:00 点位数据作为每日安装数

### 涉及的数据库表

| 表名 | 用途 |
|---|---|
| `google_experiment_data` | 实验每日安装数（Day1–Day100），按 bundle_id + name + scheme 粒度 |
| `google_experiment_details` | 实验详情（方案、国家、期数、语言、开始/结束时间、置信度、最低检测效果、测试结果、应用情况） |
| `shop_material_library` | 商店素材库，关联 experiment_detail_id |
| `google_experiment_country` | 实验国家/地区字典 |
| `google_experiment_app_bundle_map` | appId ↔ bundleId 映射 |

### 关键业务规则

1. **实验名称解析**：格式为 `编号-测试主体-国家地区`，解析出测试主体（必须属于材料类型列表）和国家。
2. **材料类型白名单**：版式、icon、内容、横图、短描述、视频、本地化。
3. **时序数据取 15:00 点位**：遍历 Variant.Series.Points，仅取 timeBeijing 中 15:00 的点位作为当日安装数。最后一天取当天最晚时间点的数据。
4. **Day 索引计算**：以所有 Variant 中最早的正值 15 点日期为 Day1，后续按自然日递增，范围 Day1–Day100。
5. **实验开始时间归一化**：入库时统一截断到当天 00:00:00。
6. **默认对照组**：第一个 Variant 为默认对照组（scheme="默认"），其余为实验组。
7. **素材入库**：图片下载后上传 UCloud，路径格式 `/material/google/image/{MD5(filename)}.{ext}`。
8. **消息幂等**：先按 bundleId + experimentName 查已有实验详情，命中则直接更新数据；未命中才创建新实验。

### 与投放/ROI 体系的关系

Google 实验关注商品页素材（icon、截图、视频、描述等）对自然量安装转化率的影响，属于 ASO（App Store Optimization）范畴。其结果影响自然量获取效率，间接影响整体 ROI 计算中的自然用户占比和获客成本分摊。

---

## GP Store 数据采集与报表

### 模块用途

自动化采集 Google Play Console 的商店表现数据（国家维度和关键词维度的访问量、下载量），包含：

1. **定时采集任务**：cron / HTTP 触发，拼接 Google Play Console URL → 生成 workflow → 下发设备任务 → Kafka 回调入库
2. **国家维度报表**（`gp_store_country`）：按国家/来源/新老用户展示访问量、下载量、转化率、中位数趋势
3. **关键词维度报表**（`gp_store_keyword`）：按关键词/来源展示搜索词的访问量、下载量、转化率

### 核心维度

**国家报表**：
- date（日期）、bundle_id（项目/应用包名）、group_by（分组维度：国家/来源/新老用户）
- country（国家地区）、source（来源：浏览/搜索/引荐）、user_type（新用户/老用户/全部用户）

**关键词报表**：
- date（日期）、bundle_id（项目）、group_by（分组维度：关键词/来源）
- keyword（关键词）、source（来源：浏览/搜索）、country（国家：全球/美国）

### 核心指标

| 指标 | 国家报表 | 关键词报表 | 计算方式 |
|---|:---:|:---:|---|
| visits（访问量） | ✓ | ✓ | SUM(visits) |
| download（下载量） | ✓ | ✓ | SUM(download) |
| conversion_rate（转化率） | ✓ | ✓ | download / visits × 100，保留两位小数 |
| median（第50个百分位） | ✓ | ✗ | 仅按来源分组时可用，来自独立中位数表 |

### 涉及的数据库表

| 表名 | 用途 |
|---|---|
| `google_store_data_by_country` | 国家维度日粒度数据（date + bundle_id + country + source + user_type） |
| `google_store_data_by_keyword` | 关键词维度日粒度数据（date + bundle_id + keyword + country + source） |
| `google_store_data_by_median` | 按来源的下载量中位数（第50百分位）日粒度数据 |
| `google_store_data_config` | 应用与 GP Console 的映射配置（device_id、developers、app、peerset_keys、bundle_id、project） |
| `google_store_data_stask_execution` | 采集任务执行记录（工作流ID、设备ID、状态、主/子任务关系） |

### 关键业务规则

1. **采集 URL 拼接**：基于 `google_store_data_config` 中的 developers 和 app ID，结合 label（如 `country_browse`、`keyword_search_us` 等）和日期拼接 Google Play Console 的报告页面 URL。
2. **Label 体系**：每个 label 定义了目标表（country/keyword/median）、来源（browse/search/referral）、用户类型（新/老/总）、国家（全球/美国），以及对应的 URL 查询模板和 CSV 文件名。
3. **子任务补采**：主任务 Kafka 回调时，检测库中最大日期 < 本次日期，自动为缺失日期派发子任务。同一 date+bundle_id+main_task_id 下跳过已有子任务，避免重复。
4. **任务状态机**：初始化(1) → 成功(2) / 失败(3)。任务类型分主任务(1)和子任务(2)，来源分 http 和 crontab。
5. **默认 bundle_id**：国家报表和关键词报表默认选中 `com.block.juggle`（Block Blast GP 包名）。
6. **图表规则**：
   - 国家报表：TOP 10 维度折线 + 灰色汇总线（默认不选中），支持下载量/访问量/转化率/中位数趋势图
   - 关键词报表：TOP 10 关键词折线 + 汇总线，支持下载量/访问量/转化率趋势图
   - X 轴为连续自然日，缺失日期补 0
7. **中位数规则**：仅当 group_by=source 时中位数列有值，其他分组下显示 "-"。中位数来自 `google_store_data_by_median` 表，source="all" 的记录作为图表汇总线。
8. **新老用户**：user_type=1 新用户，2 老用户，3 全部用户。老用户 = 总 - 新。
9. **来源枚举**：browse（浏览）、search（搜索）、referral（引荐）。关键词报表仅支持浏览和搜索。

### 与投放/ROI 体系的关系

GP Store 数据反映 Google Play 商店页面的自然获客表现，是投放与自然量对比分析的重要参照。国家维度的访问量/下载量/转化率可用于评估各国商店页优化效果，辅助投放国家选择和 ASO 策略制定。关键词数据用于评估搜索排名和品牌词 / 竞品词的流量贡献。

---

## KOL 视频效果报表（KOL Video Effect）

### 模块用途

展示 KOL/KOC 视频投放的全链路效果数据，涵盖签约成本、投放花费、播放数、互动数据（点赞/评论/分享）、CPM、互动率等指标，支持按视频粒度的明细查看和下钻图表。同时提供按月汇总的产品成本统计。

### 核心维度

| 分组 | 维度字段 |
|---|---|
| 时间 | published_at（发布日期）、campaign_start_date（投放开始日期=首次有消耗日期）、created_at（上传日期） |
| 业务 | media_source（媒体平台）、campaign（Campaign）、user（发布人员） |
| 达人 | kol_name（达人名称）、kol_resource_type（达人分类：KOL/KOC）、is_first_video（资源拓展：新签/复用） |
| 视频 | video_id、video_name、video_type（视频分类）、video_first_label（一级标签）、video_second_label（二级标签）、link（视频地址）、duration（时长） |
| 地域 | country（国家和地区）、language（语言） |
| 审核 | review_status（通过/不通过/未审核）、review_remark（审核备注） |

筛选新增：material_type（素材类型：社媒素材/TTCC素材/TTCS素材）、campaign_date（投放日期，筛选在指定日期有消耗的视频）。

### 核心指标

| 分组 | 指标 | 说明 |
|---|---|---|
| 成本 | ex_group_total_cost | 总花费 = 签约花费 + 奖励花费 +（负）核减金额 |
| 成本 | contract_cost | 签约花费 |
| 成本 | paid_cost | 投放花费 |
| 成本 | reward_cost | 奖励花费 |
| 成本 | deduction_cost | 核减花费 |
| 播放 | cumulative_view_count | 累计播放数（含自然+投放） |
| 播放 | paid_view_count | 投放播放数 |
| 播放 | organic_view_count | 自然播放数 = 累计 - 投放 |
| 播放 | day_3/7/30_view_count | D3/D7/D30 播放数 |
| CPM | paid_cpm | 投放 CPM = 投放花费 / 投放播放 × 1000 |
| CPM | paid_cumulative_cpm | 投放累计 CPM = 投放花费 / 累计播放 × 1000 |
| CPM | ex_group_day_3/7/30_cpm | D3/D7/D30 CPM = 总花费 / 对应天数累计播放 × 1000 |
| CPM | ex_group_cumulative_cpm | 累计 CPM = 总花费 / 累计播放 × 1000 |
| 互动 | paid/organic/cumulative_like_count | 投放/自然/累计点赞数 |
| 互动 | paid/organic/cumulative_comment_count | 投放/自然/累计评论数 |
| 互动 | paid/organic/cumulative_share_count | 投放/自然/累计分享数 |
| 互动 | cumulative/paid_engagement_count | 累计/投放总互动数（点赞+评论+分享） |
| 互动率 | paid_engagement_rate | 投放互动率 = 投放总互动 / 投放播放 × 100% |
| 互动率 | organic_engagement_rate | 自然互动率 = 自然总互动 / 自然播放 × 100% |
| 互动率 | cumulative_engagement_rate | 累计互动率 = 累计总互动 / 累计播放 × 100% |

### 关键业务规则

1. **权限分离**：
   - 签约成本类指标（总花费、签约花费、奖励花费、核减花费、D3/D7/D30/累计 CPM）受 `KOL_VIDEO_EFFECT_CONTRACT` 权限控制
   - 投放成本类指标（投放花费、投放 CPM、投放累计 CPM）受 `KOL_VIDEO_EFFECT_PAID` 权限控制
   - 字段级权限过滤通过 `FilterFieldsByPermission` 实现
2. **数据范围过滤**：通过 IAM `BuildDataScopeCondition` 按发布人员（user）维度限制数据可见范围。
3. **发布日期兜底**：当 `published_at = '0000-00-00 00:00:00'` 时，使用 `date` 整型字段作为后备筛选条件。
4. **月度成本汇总**：`SummaryCostByMonth` 支持最多 5 个月的按产品汇总成本查询，月份格式 YYYY-MM，不允许未来月份。
5. **视频明细与下钻**：每个指标支持图表下钻（DrillDown），按日期维度展示累计值和增量值的趋势图。

### 涉及的数据表

主查询涉及 `video_base`（视频基础信息）、`kol_cost`（KOL 投放消耗明细）、`kol_resource`（达人资源分类）等 MI 平台内部表，通过 JOIN 关联查询。

### 与投放/ROI 体系的关系

KOL 视频效果是投放体系中"内容营销"分支的核心报表。其投放花费（paid_cost）是 ROI 计算中的成本组成部分（KOL 渠道），播放数和互动数据用于评估内容投放的效率（CPM）和用户参与度。与媒体投放（Facebook/Google/TikTok 等程序化广告）的 ROI 分析互补，共同构成完整的获客效率评估体系。

---

## 预测服务集成（Forecast Integration）

### 模块用途

封装 ROI / LTV 预估算法服务的 HTTP 调用，为 MI 平台 ROI360 报表提供收入预测能力。包含两套预估接口和批量预估支持。

### 接口架构

| 接口 | 地址 | 模式 | 说明 |
|---|---|---|---|
| ltv_pred（Base 模型） | `http://10.9.70.60:8090/ltv_pred` | 单条预估 | 毫秒级轻量推理，QPS 天花板约 142 |
| PredRevenue（CPP 模型） | `http://10.9.70.60:1099/PredRevenue` | 单条预估 | 与 Base 模型互斥调用 |
| roi-forecast/run-ban | `http://10.9.83.92:8000/api/v1/roi-forecast/run-ban` | 预估（旧） | XY 预估服务 |
| roi-forecast/run | `http://10.9.83.92:8000/api/v1/roi-forecast/run` | 批量预估 | 支持多条并发，大 batch 效果显著 |

### 请求参数

| 字段 | 说明 |
|---|---|
| project | 项目标识（如 BB、BBVN） |
| version | 模型版本 |
| bundle_id | 应用包名 |
| media_source | 媒体渠道 |
| country | 国家 |
| data | 已有收入数据序列（float64 数组） |
| start_dt | 起始日期 |
| convert_type | 转化类型 |
| days_num | 预估天数 |
| pre_model_day | 快照日期（可选） |
| campaign | Campaign 级别预估（仅 XY 批量接口支持） |
| roi_range | 是否返回 ROI 范围（仅 XY 批量接口支持） |

### 关键业务规则

1. **渠道名映射**：`tiktokglobal_int` → `bytedanceglobal_int`，模型侧统一使用 bytedance 标识。
2. **BlockBlast VN 包替换**：BBVN 项目的预估请求需替换为 BB 项目，包名 `com.blockblast.vn` → `com.block.juggle`，`com.blockblast.vn.ios` → `com.blockpuzzle.us.ios`。仅走 Base 模型。
3. **Base 模型限制**：不支持 campaign 级别预估和 roi_range，调用前强制清空这两个字段。
4. **响应结构**：
   - Base/CPP 单条：返回 `preds`（Base）或 `pred_data`（CPP）浮点数组
   - XY 批量：返回 `data[]`，每条包含 preds、version、roi_range
5. **性能特征**（基于压测报告）：
   - ltv_pred：单请求 ~9ms，推荐并发 c=10，7.5 万条约 11 分钟
   - roi-forecast：单批 ~8.5s（b=50），增大 batch size 是核心加速手段，b=1000 时 items/s 可达 ~593
   - ltv_pred 长时间运行会出现吞吐衰减，roi-forecast 吞吐全程稳定

### 与投放/ROI 体系的关系

预测服务是 ROI360 页面的核心依赖：基于已有的 D1–Dn 收入数据，预估未来收入趋势和最终 LTV，从而计算预估 ROI。Base 模型和 XY 模型提供不同精度和粒度的预估结果，XY 模型支持 campaign 级别预估和 ROI 置信区间，用于更细粒度的投放决策。
