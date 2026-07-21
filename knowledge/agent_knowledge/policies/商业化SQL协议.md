# 商业化 SQL 协议

> 状态：active  
> 创建日期：2026-06-19  
> 适用范围：广告商业化链路、插屏 / 激励、load / action / ready、广告收入、ECPM、商业化实验和广告单元分析。

## 使用边界

本文定义商业化 SQL 的场景拆分、指标口径、事件字段和 join 护栏，不直接提供 verified SQL。

可作为当前默认规则使用：

- 区分商业化链路分析和商业化实验分析。
- 判断插屏 / 激励、高价 / 中价 / 兜底广告单元等业务词如何映射。
- 生成商业化 SQL 前列出事件、JSON path、配置表和验证状态。

不可直接作为 verified 事实使用：

- 未进入表卡的商业化实验汇总表或配置表。
- 未经过 schema / dry-run / 小窗口验证的 `properties` JSON 字段。
- 未经 SQL promotion 晋升的收入、ECPM 或实验效果 SQL。

## 核心概念

| 概念 | 标准解释 | SQL 要求 |
|---|---|---|
| 广告格式 | 广告展示形式，主要为插屏和激励 | 通过 `ad_type`、`s_ad_type`、`adFormat` 等字段识别，字段名需验证。 |
| 广告单元 | 游戏侧一次 Max 插屏 / 激励展示调用会拉取多个广告单元 | 价格层级不能只靠广告单元 ID 猜测。 |
| 高价 / 中价 / 兜底 | 广告单元价格层级，常见值为 `high` / `mid` / `low` | 非小包优先通过商业化配置表的 `price_type` 确认；小包使用 `小包广告单元映射.md` 和配套 CSV。 |
| 方案号 | 商业化实验分组标识 | 事件侧常见为 `s_ad_public_adwaynum`，汇总表常见为 `user_waynum`。 |
| ADX / network | 广告渠道或 network | 常见字段为 `s_ad_extra_platform`、`networkName`，需验证枚举。 |

用户提到“兜底 / 中价 / 高价”时，默认理解为广告单元价格层级；提到“插屏 / 激励”时，默认理解为广告格式。

## 场景拆分

| 场景 | 优先数据路径 | 标准指标 |
|---|---|---|
| 商业化核心链路 | 白名单事件表 | APP 启动、广告初始化、load 开始、load 结束、load 成功、load 成功率、action、ready、action 到 ready 转化率、收入、ECPM |
| 商业化实验 | 商业化实验汇总表；缺实验信息时补商业化配置表 | 插屏 action / ready / PV / 收入 / ECPM，激励 action / ready / PV / 收入 / ECPM |
| 广告单元价格层级 | 非小包：事件表提取方案号和广告单元，再 join 商业化配置表；小包：按 Clean Unit ID 映射 | 按 `price_type` / role 拆分 PV、load 成功率、收入、ECPM |
| 收入回传 | SDK 广告收入事件或已验证聚合收入表 | 收入、PV、ECPM；必须说明单位和是否含 banner |

## 商业化链路事件

| 事件 | 用途 | 常用字段 |
|---|---|---|
| `ta_app_start` | APP 启动数 | `#resume_from_background` |
| `s_moudle_ad_init` | 广告初始化成功 | `s_ad_extra_platform` |
| `ad_load_start` | 广告 load 开始 | `ad_type`、`s_ad_extra_platform` |
| `ad_load_end` | 广告 load 结束 / 成功 / 时长 / 广告单元 | `load_status`、`load_time`、`ad_unit_id`、`s_ad_public_adwaynum`、`s_ad_series_id`、`s_ad_extra_platform` |
| `s_ad_show_action` | action / ready 转化 | `s_ad_type`、`s_ad_ready`、`s_ad_public_adwaynum` |
| `appLovin_sdk_ad_revenue` | SDK 收入回传 | `adUnitId`、`networkName`、`adFormat`、`revenue` |

商业化链路 SQL 必须带 `dt`、`event_name`，共享表必须带 `app_name`。白名单事件表使用规则见 `白名单事件表查询协议.md`；BB GP / iOS 商业化埋点的旧 `s_*` 事件族、新 `ad_*` 事件族、端差异和收入字段边界见 `BB商业化埋点查询规则.md`。

## 指标口径

| 指标 | 标准口径 |
|---|---|
| 广告初始化成功数 | `s_moudle_ad_init` 事件数 |
| load 开始数 | `ad_load_start` 事件数 |
| load 结束数 | `ad_load_end` 事件数 |
| load 成功数 | `ad_load_end` 且 `load_status = '1'` |
| load 成功率 / 填充率 | load 成功数 / load 结束数或 load 请求数；分母必须在输出中说明 |
| ready 数 | `s_ad_show_action` 且 `s_ad_ready = 'ready'` |
| action 数 | `s_ad_show_action` 事件数 |
| action 到 ready 转化率 | ready 数 / action 数 |
| 收入 | SDK 收入事件或聚合收入字段求和；必须说明单位 |
| ECPM | 收入 * 1000 / 展示 PV；若事件收入已是 ECPM 或已乘 1000，必须重新确认单位 |

## 广告单元 join 护栏

商业化广告单元价格层级分析中：

- 小包产品的兜底 / 中价 / 高价档位使用 `小包广告单元映射.md` 和 `小包广告单元映射.csv`，不用 BB 商业化配置表的 `price_type` 替代。
- 事件侧先提取 `s_ad_public_adwaynum` 作为方案号。
- 配置侧使用 `adwaynum` 对齐方案。
- `ad_unit_id = adunit` 只能作为辅助精确匹配。
- 不得只用 `ad_unit_id` 作为主 join key；同一个 `ad_unit_id` 可能对应多个方案，直接 join 会放大行数。

标准 join 说明：

```text
主键：event.s_ad_public_adwaynum = config.adwaynum
辅助键：event.ad_unit_id = config.adunit
输出维度：ad_format / adx / adwaynum / price_type
```

如果商业化配置表未进入表卡或 schema 未验证，输出 `candidate_table_requires_intake`，并将 SQL 标为 candidate。

## 商业化实验汇总

商业化实验汇总分析通常需要：

| 字段 | 用途 |
|---|---|
| `user_waynum` | 实验方案分组 |
| `life_type` | 生命周期范围 |
| `app_name` | 产品和端过滤 |
| `dt` / `hour` | 快照或统计分区 |
| `inter_ad_action_cnt` / `inter_ad_ready_cnt` / `inter_ad_pv` / `inter_ad_revenue` | 插屏链路和收入 |
| `reward_ad_action_cnt` / `reward_ad_ready_cnt` / `rewarded_ad_pv` / `rewarded_ad_revenue` | 激励链路和收入 |

常用过滤：

```text
dt、hour='23'、life_type、app_name、user_waynum
```

缺少方案号、批次、实验起止时间时：

- BB GP 商业化实验优先查商业化实验配置表。
- 不要用产品实验配置表替代商业化配置表。
- 配置表只补元信息，最终指标仍来自事件表或商业化实验汇总表。

## 输出要求

商业化 SQL 输出必须说明：

- 当前是商业化链路、商业化实验、广告单元价格层级还是收入回传分析。
- 广告格式和广告单元是否同时拆分。
- 使用的事件名、JSON path、配置表和 join key。
- load 成功率、ready 转化率、ECPM 的分母。
- 收入单位、是否含 banner、是否来自 SDK 事件或聚合表。
- 表和字段是否经过表卡 / schema / 小窗口验证。

## 维护规则

本文只维护商业化 SQL 的业务规则。涉及具体表的字段、分区、PII、freshness、join keys 和安全样例，应继续沉淀到 `ai_hive/agent_knowledge/tables/`；可复用 SQL 必须按 `da_assets/SQL晋升治理.md` 晋升。
