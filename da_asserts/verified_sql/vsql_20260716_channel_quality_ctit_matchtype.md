# Verified SQL: 渠道质量与归因异常 - CTIT 分布 + match_type 分层

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260716_channel_quality_ctit_matchtype` |
| 状态 | verified |
| promotion_status | verified_sql |
| sql_status | verified |
| 运行来源 | 本文档 `### Canonical SQL` 下唯一的 `sql` fence |
| 关联 SOP | `../analysis_sop/20260615_渠道质量与归因异常分析SOP.md` |
| 适用场景 | 识别渠道质量风险候选：CTIT 异常（过短/过长/负值）、match_type 分布、gp_referrer 归因劫持候选 |
| 最后验证 | 2026-07-16 |
| validation_method | manual_small_window |
| owner | Cursor Agent |
| supersedes | [] |
| 源 candidate | `candidate_sql/channel_quality_ctit_matchtype.sql`（晋升后已移除） |

## 原始问题

> 识别渠道质量风险候选：CTIT 异常（过短/过长/负值）、match_type 分布异常、gp_referrer 与 AF 归因不一致。只输出风险提示，不自动给出停投结论。

## 口径说明

| 类型 | 内容 |
|---|---|
| 时间口径 | `dt` 按日 |
| 粒度 | `bundle_id × media_source × match_type` |
| CTIT | `install_time - gp_click_time`（秒），用 `substr` 截掉毫秒后计算 |
| CTIT 分段 | `<5s`, `5-10s`, `10-60s`, `60s-1h`, `1h-24h`, `>24h`, `negative`(安装早于点击) |
| organic_referrer_paid | `gp_referrer='organic'` 且 `media_source` 不是 organic/restricted 的记录数 |
| 无效记录排除 | `gp_click_time` 为空或 `1970-01-01 00:00:00.000` 的记录排除 |
| 最小样本 | `HAVING count(*) >= 10` |

## 依赖表

| 表 | 用途 |
|---|---|
| `h-s.dwd_market_appsflyer_activation_push_data_di` | AF 激活明细，含 install_time / gp_click_time / match_type / gp_referrer |

## 复用参数

| 参数 | 说明 |
|---|---|
| `${dt}` | 查询日期，如 `2026-07-14` |
| `${bundle_id}` | 包体 ID，如 `com.kcolb.juggle` |

## 风险与陷阱

- CTIT < 5s 只作 `risk_signal`，不自动进入扣量规则（需 DA 确认阈值）。
- SRN 渠道（google/tiktok）CTIT 负值是已知行为（归因时间戳差异），不是异常。
- `gp_referrer` 只覆盖 Android，iOS/SKAN 需另走 SKAN 口径。
- `dwd_market_appsflyer_activation_push_data_di` 不是安装/激活默认分母；分母问题按 `ai_hive/agent_knowledge/口径决策记录.md`。
- SRN/preload/gclid 渠道的 `gp_referrer=organic` 是正常例外，不是归因劫持。
- 不输出用户/设备级明细，只做聚合。

## 验证记录

### 2026-07-16 · MaxCompute 实时探测

探测：`dwd_market_appsflyer_activation_push_data_di` max(dt)=2026-07-15。

| 验证批次 | 日期 | 行数 | 结果摘要 |
|---|---|---|---|
| smoke-1 | 2026-07-14 | 15 行 | Google SRN: total=237858, <5s=10268, 5-10s=10889, 10-60s=48483, 1h-24h=54594, >24h=32984, negative=68623; organic: total=78053; AppLovin gp_referrer: total=22876 |

Top 5 渠道示例：

| media_source | match_type | total | <5s | 5-10s | 10-60s | 1h-24h | >24h | negative |
|---|---|---|---|---|---|---|---|---|
| googleadwords_int | srn | 237,858 | 10,268 | 10,889 | 48,483 | 54,594 | 32,984 | 68,623 |
| organic | null | 78,053 | 372 | 404 | 1,764 | 8,199 | 63,036 | 2,548 |
| oppopaipreinstall_int | preload_pai | 41,616 | 83 | 83 | 339 | 9,359 | 30,572 | 496 |
| xiaomipai_int | preload_conf | 23,778 | 205 | 231 | 845 | 6,246 | 14,379 | 1,224 |
| applovin_int | gp_referrer | 22,876 | 1,043 | 1,064 | 4,765 | 4,610 | 3,781 | 6,731 |

验证确认：CTIT 分段正确、match_type 分层正常、SRN 负值大量出现属预期行为。

## SQL

### Canonical SQL

```sql
/* CHANNEL_QUALITY_CTIT_MATCHTYPE */
SELECT
    bundle_id,
    media_source,
    match_type,
    count(*) AS total_installs,
    count(IF(datediff(to_timestamp(substr(install_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), to_timestamp(substr(gp_click_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), 'ss') < 5
          AND datediff(to_timestamp(substr(install_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), to_timestamp(substr(gp_click_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), 'ss') >= 0, 1, NULL)) AS ctit_lt_5s,
    count(IF(datediff(to_timestamp(substr(install_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), to_timestamp(substr(gp_click_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), 'ss') BETWEEN 5 AND 10, 1, NULL)) AS ctit_5_10s,
    count(IF(datediff(to_timestamp(substr(install_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), to_timestamp(substr(gp_click_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), 'ss') BETWEEN 10 AND 60, 1, NULL)) AS ctit_10_60s,
    count(IF(datediff(to_timestamp(substr(install_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), to_timestamp(substr(gp_click_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), 'ss') BETWEEN 60 AND 3600, 1, NULL)) AS ctit_60s_1h,
    count(IF(datediff(to_timestamp(substr(install_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), to_timestamp(substr(gp_click_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), 'ss') BETWEEN 3600 AND 86400, 1, NULL)) AS ctit_1h_24h,
    count(IF(datediff(to_timestamp(substr(install_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), to_timestamp(substr(gp_click_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), 'ss') > 86400, 1, NULL)) AS ctit_gt_24h,
    count(IF(datediff(to_timestamp(substr(install_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), to_timestamp(substr(gp_click_time, 1, 19), 'yyyy-MM-dd HH:mm:ss'), 'ss') < 0, 1, NULL)) AS ctit_negative,
    count(IF(gp_referrer = 'organic' AND media_source NOT IN ('organic', 'restricted'), 1, NULL)) AS organic_referrer_paid
FROM h-s.dwd_market_appsflyer_activation_push_data_di
WHERE dt = '${dt}'
  AND bundle_id = '${bundle_id}'
  AND platform = 'android'
  AND gp_click_time IS NOT NULL AND gp_click_time <> ''
  AND gp_click_time <> '1970-01-01 00:00:00.000'
GROUP BY
    bundle_id,
    media_source,
    match_type
HAVING count(*) >= 10
ORDER BY
    total_installs DESC
```
