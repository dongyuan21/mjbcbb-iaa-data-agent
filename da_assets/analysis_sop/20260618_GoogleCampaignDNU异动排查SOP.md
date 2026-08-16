# SOP: Google campaign DNU 异动与 change log 排查

## 元信息

| 项 | 内容 |
|---|---|
| ID | `sop_20260618_google_campaign_dnu_changelog_triage` |
| 状态 | verified_sql_available |
| 来源 | `data_agent_plan/snapshots/POC01_示例产品美国UA_DNU拆解路线.md`、`../verified_sql/vsql_20260618_google_campaign_dnu_changelog_triage.md` |
| 适用问题 | Google DNU 下滑、Google campaign 掉量、是否存在预算/状态/定向/ad_group/ad 操作记录 |
| 适用范围 | MaxCompute `示例表` + `示例表` |
| 最后验证 | 2026-06-18 |

## 分析目标

当 DNU 或 campaign 下滑已经定位到 `googleadwords_int` 时，把“掉量 campaign”与 Google Ads change log 同窗口联查，判断是否存在同期预算、状态、定向、广告组、广告或文案操作记录，为 UA / DA / 业务复盘提供证据。

## 触发条件

满足任一条件时使用本 SOP：

- DNU / activation / install 下滑的 media_source 贡献显示 Google 是主要缺口来源。
- campaign / adset / ad 下钻显示 Google 某些 campaign 明显低于 baseline。
- 用户追问“是不是有人改预算、状态、出价、素材、定向”。
- POC 或周报需要把 Google campaign 掉量和平台操作记录串起来。

## 输入

| 输入 | 说明 |
|---|---|
| `bundle_id` | 例如 `com.example.demo.game01`。 |
| `country` | 例如 `US`；无国家限制时需明确为全量。 |
| `baseline_start` / `baseline_end` | 对照窗口，建议同 weekday 或前 7 天。 |
| `baseline_days` | baseline 日期数；前 7 天填 `7`。 |
| `anomaly_day` | 异常业务日期。 |
| `示例产品_scan_start` / `示例产品_scan_end` | activation 分区扫描窗口，必须按 `sop_20260618_dnu_install_time_示例产品_lag_guardrail` 扫到 latest 或至少 T+1。 |
| `change_示例产品_start` / `change_示例产品_end` | change log 分区日期，通常覆盖异常日前后。 |
| `change_hour_start` / `change_hour_end` | change log 小时范围，通常 `00` 到 `23`。 |

## 分析步骤

1. 先完成 DNU / media_source / campaign 下钻，确认 Google campaign 是候选解释对象。
2. 按 `sop_20260618_dnu_install_time_示例产品_lag_guardrail` 检查 activation 表 latest partition，设定 `示例产品_scan_end`。
3. 运行 `../verified_sql/vsql_20260618_google_campaign_dnu_changelog_triage.md`。
4. 按 DNU delta 绝对值排序，优先看大缺口 campaign 是否有 change log 命中。
5. 对命中 campaign 记录操作类型：
   - `campaign_budget_event_cnt`
   - `campaign_status_change_cnt`
   - `campaign_criterion_event_cnt`
   - `ad_group_event_cnt`
   - `ad_event_cnt`
   - `ad_text_change_cnt`
6. 输出结论时分三层：
   - DNU 事实：哪个 campaign 下滑多少。
   - 操作事实：同窗口是否有 Google Ads change log 命中。
   - 解释边界：命中只是同期证据，不自动等同因果；未命中也不证明无人操作。

## SQL / 资产依赖

| 名称 | 路径 |
|---|---|
| DNU 迟到分区护栏 | `20260618_DNU安装时间与分区迟到护栏SOP.md` |
| Google campaign DNU + change log 联查 SQL | `../verified_sql/vsql_20260618_google_campaign_dnu_changelog_triage.md` |
| Google Ads 配置变更单表监控 SQL | `../verified_sql/vsql_20260618_google_ads_config_change_monitoring.md` |
| Google Ads change_event 宽数据资产目录 | `../../数据资产目录/agent_knowledge/tables/示例表.yaml` |
| 6/17 验证 case | `../decision_cases/20260618_GoogleCampaignDNU异动与变更记录案例.md` |

## 输出格式

```text
问题识别：
业务日期窗口：
示例产品 扫描窗口：
change log 窗口：
freshness_status：
掉量 campaign：
同期 change log 命中：
解释边界：
下一步：
```

## 判断规则

- `change_log_hit_status = change_log_hit`：写“发现同期配置操作记录”，并列出操作类型计数。
- `change_log_hit_status = no_change_log_hit`：写“当前 MC change log 窗口未发现记录”，不要写“无人操作”。
- 有 `campaign_budget_event_cnt > 0` 或 `campaign_status_change_cnt > 0`：可作为“预算/状态变更候选证据”，但仍需结合消耗、展示、点击、registers 或 UA owner 复盘。
- 有 `campaign_criterion_event_cnt > 0`：优先解释为定向/criterion 类操作，可能影响覆盖范围，但需结合对象和量级。
- 有 `ad_group_event_cnt` / `ad_event_cnt` / `ad_text_change_cnt`：优先进入广告组、素材、标题描述变更排查。
- 如果 DNU 查询未纳入 T+1 迟到分区，必须先重跑 DNU，再联查 change log。

## 示例

2026-06-18 验证窗口中，示例产品 GP / US / Google 的 `2026-06-17` DNU 异动联查显示：

- `US-LH015-3.0--ARO-XH-260319-通用词`：DNU delta `-612.57`，同日命中 1 条 `CAMPAIGN_BUDGET` 事件，预算 `<提交标识> -> <提交标识>`；这不是预算下调证据。
- `US-LH015-3.0-ARO-XH-260423-品类APP`：DNU delta `-418.71`，同日 target ROAS `0.23 -> 0.25`，且 ad group status `ENABLED -> PAUSED`。
- `US-LH015-3.0--ARO-XH-260319-游戏大词`：DNU delta `-337.14`，同日 campaign status `ENABLED -> PAUSED`，6/18 campaign 快照仍为 `PAUSED`。
- `US-LH015-3.0--ARO-XH-260320-体育专项`：DNU delta `-225.86`，当前 change log 窗口未命中，应标 `no_change_log_hit_in_window` 而不是“无人操作”。

这些结果可以作为“同期操作记录候选证据”，但仍需结合消耗、展示、点击、registers 或 UA owner 记录判断是否为真正原因。
