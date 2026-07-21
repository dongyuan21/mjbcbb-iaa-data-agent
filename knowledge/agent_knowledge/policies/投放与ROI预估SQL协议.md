# 投放与 ROI 预估 SQL 协议

> 状态：active  
> 创建日期：2026-06-19  
> 适用范围：UA 投放、AppsFlyer 激活、campaign / adset / ad、素材、成本、SDK 收入、ROAS / ROI、ROI 预估 SQL。

## 使用边界

本文定义投放 SQL 的表选型、日期语义、join 口径和预估 / 真实边界，不直接提供 verified SQL。

可作为当前默认规则使用：

- 判断投放问题应走 AF 激活、消耗、成本、SDK 收入、素材映射、SKAN 还是 ROI 预估表。
- 规范 campaign、adset、ad、country、bundle_id 的 join 口径。
- 区分真实回收、预估回收、SKAN 聚合和成本日期。

不可直接作为 verified 事实使用：

- 未进入 `ai_hive` 表卡的候选表字段。
- 文档中的 SQL 样例结果、历史数据分布和样例日期。
- ROI 预估结果对应的停投 / 放量动作；最终动作仍需投放 owner 或治理策略确认。

MI ROI360 页面分析仍优先使用 `ai_ck/agent_knowledge/metrics/ROI360指标语义.md` 和 MI skill；本文主要服务 MaxCompute / ODPS 投放 SQL。

## 表选型

| 场景 | 首选表族 | 粒度 | 关键规则 |
|---|---|---|---|
| AF 激活归因、新增用户 campaign / adset / ad 分析 | AppsFlyer 激活全量表 | 用户级激活 | `dt` 是截止日全量快照；查近 N 天新增用最新 `dt` + `active_time_utc8` 过滤。 |
| 前端消耗、曝光、点击、IPM、CPI | spend / cost 表 | campaign / ad / country × 天 | 必须带 `bundle_id`；成本口径优先说明是否折后。 |
| 素材映射 | material 映射表 | campaign / ad / material | 只做素材维度补充，不替代消耗或收入事实。 |
| 前后端串联投放明细 | ad_detail 表族 | campaign / ad / country / retention day | 先确认产品表族和 `retention_days`；未表卡化则 candidate。 |
| AF ODS 标准安装 | installs ODS | 设备级安装 | 标准 install；适合安装链路字段和 CPI 分摊，但 PII 风险高。 |
| AF 归因后安装 | post-attribution installs ODS | 设备级安装 / reinstall | 适合重装 / reattribution 分析，不能与标准 install 混口径。 |
| SKAN 安装 | SKAN installs ODS | iOS SKAN 聚合 | 无设备级 ID，不能行级 join；只做聚合对照。 |
| AF 全量应用内事件 | all in-app events | AF event 明细 | 超大表；必须限制事件名，仅用于 AF 激活 / 事件补充。 |
| SDK 收入归因 | SDK revenue attributed | 用户级收入 | `dt` 是收入日期，不是安装日期；算 LTV_N 要收入窗口覆盖 install_date 到 install_date+N-1。 |
| campaign 级成本 | campaign cost | campaign / country / adset / ad × 天 | 数值字段可能是 string，使用前必须 cast。 |
| ROI 预估 | ROI predict 表 | active_date × bundle × media × campaign × country × retention_days | `dt` 取最新预测分区；`active_date` 是投放 / 激活日期。 |

如果表未进入 `ai_hive/agent_knowledge/catalog.yaml`，输出 `candidate_table_requires_intake`；继续写 SQL 前必须做 schema probe 或小窗口验证。

## 日期语义

| 字段 / 表族 | 日期含义 | SQL 风险 |
|---|---|---|
| AF 激活全量表 `dt` | 截止日全量快照 | 不等于新增日期；新增窗口用 `active_time_utc8`。 |
| spend / cost `dt` | 投放 / 消耗日期 | 与收入日期 join 时必须用安装 / 投放 cohort 对齐。 |
| SDK 收入归因 `dt` | 收入发生日期 | 计算 ROAS7 时，收入窗口为 install_date 到 install_date+6。 |
| ROI 预估 `dt` | 预测快照分区 | 通常取最新可用分区；不要当 active_date。 |
| ROI 预估 `active_date` | 投放 / 激活日期 | 与成本表的 `dt` 或 `active_date` 对齐。 |
| `retention_days` | 回收 / 留存周期下标 | ROI_N 通常对应 `retention_days = N-1`。 |

输出中必须写明每个日期字段的含义，尤其是全量快照 `dt`、收入日期 `dt` 和投放日期。

## campaign / adset / ad join

默认 join 粒度：

```text
bundle_id + media_source + campaign_name + country
```

能补齐时再加：

```text
adset_id / adset_name + ad_id / ad_name
```

执行规则：

- 保留 `campaign_name` 原始字符串，不做规范化改写。
- `campaign_id` 可作为稳定 join fallback，但不能替换用户明确要求的 `campaign_name` 展示。
- AF installs 表可能叫 `campaign` / `country_code`，成本表可能叫 `campaign_name` / `country`，join 前必须显式列出字段映射。
- SKAN campaign 字段不是普通 AF campaign_id，不直接 join 普通 campaign 表。
- organic 必须按 `all` 和 `paid_only` 需求区分，不要默认混在 paid ROI。

## opt_target 派生

投放优化目标 `opt_target` 由 `media_source` 和 `campaign_name` 关键词派生，按优先级首个命中：

| 优先级 | 规则 | 输出 |
|---|---|---|
| 1 | UA 渠道内关键词匹配 | `Roas` / `CPE` / `CPI` / `Other` |
| 2 | `media_source = 'Apple Search Ads'` | `ASA` |
| 3 | `media_source = 'organic'` | `Organic` |
| 4 | 预装、厂商商店、厂商分发、PAI 等非 UA 渠道 | `非UA` |
| 5 | 其余 campaign_name 含 `ROAS` | `Roas` |
| 6 | 其他 | `Other` |

UA 渠道关键词：

| media_source | 匹配顺序 |
|---|---|
| `googleadwords_int` | `3.0` -> Roas；`2.5` -> CPE；`2.0` / `1.0` -> CPI |
| `applovin_int` | `ROAS` -> Roas；`CPE` -> CPE；`CPI` -> CPI |
| `tiktokglobal_int` | `VBO` / `VO` -> Roas |
| `moloco_int` | `ROAS` -> Roas；`CPI` -> CPI |
| `Facebook Ads` | `AEO` / `CEO` -> CPE；`VO` -> Roas |
| `liftoff_int` / `bigoads_int` | `ROAS` -> Roas |
| `unityads_int` | `ROAS` -> Roas；`CPE` -> CPE |

非 UA 渠道包括名称含 `preload` / `preinstall` 的渠道，以及 `oppo_int`、`hihonor_int`、`oppoglobal_int`、`vivoglobal_int`、`xiaomiglobal_int`、`xiaomipai_int`、`shalltry_int`、`shalltrypai_int`、`aura_int`、`digitalturbine_int`、`coolpadzhf_int`、`lenovotabpai4p_int`、`nubia8rk_int`、`ztepai_int`、`ztesw_int`、`tctmobilewp_int`、`simeji_int`、`mediago_int`、`makeuptest_int`。

`opt_target` 是分类辅助维度，不是投放动作决策。

## 自然量分摊给 UA 渠道

适用问题：

- “如何将自然量分摊给 UA 渠道？”
- “自然量是否要摊回 Google / Applovin / TikTok 等买量渠道？”
- “含自然量的渠道 DNU / ROI 怎么做经营试算？”

边界：

- 自然量分摊是**经营试算口径**，不是 MMP / AF 真实归因。
- 默认先输出 `all` 与 `paid_only` 两版；若用户明确要求分摊，再输出 `allocated_organic` 试算版。
- 默认自然量池取 `channel_category='自然'`，UA 付费池取 `channel_category='Media Buy'`。
- 默认分摊权重用各 UA `media_source` 的 `paid_dnu` 占比；如果业务指定按消耗分摊，可把权重替换为 `cost_zhe`；如果要求真实增量贡献，必须有实验 / holdout / MMM 证据，不从普通明细表直接推断。
- `channel_category='其他'` 不默认并入自然量；如需广义 organic（自然 + 其他），标 `needs_decision`。

默认公式：

```text
allocated_organic_dnu = organic_dnu * media_paid_dnu / total_ua_paid_dnu
adjusted_dnu = media_paid_dnu + allocated_organic_dnu
```

MaxCompute 设备口径 SQL 模板：

```sql
WITH organic AS (
  SELECT
    dt,
    country,
    SUM(dau) AS organic_dnu
  FROM hungry_studio.ads_market_device_dau_behavior_di
  WHERE dt BETWEEN '${start_date}' AND '${end_date}'
    AND age_bucket = 'D0'
    AND channel_category = '自然'
    AND bundle_id = '${bundle_id}'
    -- 可选：AND country = '${country}'
  GROUP BY dt, country
),

ua AS (
  SELECT
    dt,
    country,
    media_source,
    SUM(dau) AS paid_dnu
  FROM hungry_studio.ads_market_device_dau_behavior_di
  WHERE dt BETWEEN '${start_date}' AND '${end_date}'
    AND age_bucket = 'D0'
    AND channel_category = 'Media Buy'
    AND bundle_id = '${bundle_id}'
    -- 可选：AND country = '${country}'
  GROUP BY dt, country, media_source
),

ua_total AS (
  SELECT
    dt,
    country,
    SUM(paid_dnu) AS total_ua_paid_dnu
  FROM ua
  GROUP BY dt, country
)

SELECT
  u.dt,
  u.country,
  u.media_source,
  u.paid_dnu,
  o.organic_dnu,
  t.total_ua_paid_dnu,
  CASE
    WHEN t.total_ua_paid_dnu > 0
    THEN o.organic_dnu * u.paid_dnu / t.total_ua_paid_dnu
    ELSE 0
  END AS allocated_organic_dnu,
  u.paid_dnu
    + CASE
        WHEN t.total_ua_paid_dnu > 0
        THEN o.organic_dnu * u.paid_dnu / t.total_ua_paid_dnu
        ELSE 0
      END AS adjusted_dnu
FROM ua u
JOIN organic o
  ON u.dt = o.dt
 AND u.country = o.country
JOIN ua_total t
  ON u.dt = t.dt
 AND u.country = t.country
ORDER BY u.dt, u.country, u.paid_dnu DESC;
```

执行注意：

- 该模板是 candidate SQL；用于线上回答时应先跑最新分区 / 小窗口验证。
- MaxCompute 不允许无条件裸 `CROSS JOIN`；若聚合成单个自然量池，需要用常量 key join 或 `mapjoin`。
- 若用户不要求国家粒度，可从 CTE 和 join key 中移除 `country`，但必须保持 `dt` 粒度一致。

## 成本和收入

成本：

- 涉及 ROI / ROAS 时，优先说明使用原始消耗、概率消耗还是折后消耗。
- 数值字段为 string 的成本表必须 `CAST`。
- 计算 CPI 时过滤 `media_installs > 0` 和 cost > 0。

收入：

- SDK 收入归因表的 `dt` 是收入发生日期。
- `conversion_type = 'install'` 适合标准新安装回收；`reinstall`、`unknown` 是否纳入必须按问题说明。
- `attr_data_source` 说明收入归因链路，不能忽略 push / pull / revenue 直接匹配差异。

ROAS / ROI：

```text
ROAS_N / ROI_N = N 日累计收入 / 成本
```

若用户说 ROI 但实际 SQL 算的是 ROAS，输出中必须写清公式。

## ROI 预估

ROI 预估表使用规则：

- `dt` 取最新可用预测分区。
- `active_date` 是被预测 cohort 日期。
- 必须限定 `bundle_id`、`media_source`，按需求补 `campaign_name`、`country`、`adset`、`ad`。
- `country` 使用 ISO 2 位码，如 `US`。
- 常见周期映射：D30 -> `retention_days=29`，D60 -> 59，D90 -> 89，D180 -> 179，D360 -> 359。
- 若表含 `predict1` / `predict2` 双预测值，默认候选口径为 `(predict1 + predict2) / 2`，但晋升前必须验证模型说明。
- 预估 360 日 ROI = 预估 ROAS360 / 成本；成本口径必须与投放表一致。

预估值不能当成真实回收。若与 MI ROI360 页面口径对齐，必须同时说明 forecast 版本和真实 / 蓝底预估边界。

## SKAN 限制

SKAN 安装表：

- 无设备级 ID，不能与用户级激活、收入或行为表做行级 join。
- 只能做 media / campaign / country 等聚合粒度对照。
- SKAN campaign 字段需要单独映射，不默认等同普通 AF campaign。

## 输出要求

投放 SQL 输出必须包含：

- 表选型理由和未选表理由。
- `dt`、`active_date`、`install_time`、收入日期的语义。
- `bundle_id`、`media_source`、`country`、campaign / adset / ad join 字段映射。
- 成本口径、收入口径、真实 / 预估状态。
- 是否包含 organic。
- 验证状态：未跑、schema probe、dry-run、小窗口或 verified。

## 维护规则

本文只维护投放 SQL 的业务路由和口径边界。具体字段、分区、PII、freshness、join keys、example queries 继续回到 `ai_hive/agent_knowledge/tables/` 治理；可复用 SQL 必须按 `da_assets/SQL晋升治理.md` 晋升。
