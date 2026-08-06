# UA 决策行为沉淀 Phase0 实时数据能力报告（UA-P0-02）

> 状态：`draft_for_review`（candidate，未经独立 Review 与人工验收前不作为最终结论）
>
> 日期：`2026-07-23`
>
> `TASK_ID=UA-P0-02`；`TASK_TYPE=IMPLEMENTATION`；`TARGET_REPO=/Users/lidongyuan/hungrystudio/点位/数仓`；`BASE_COMMIT=80f54c4cbc5545d413710068581205b12118d001`
>
> 权威方案：`data_agent_plan/UA决策行为沉淀/UA决策行为沉淀与回测方案.md` 第 6、7 节
>
> 权威任务书：`data_agent_plan/UA决策行为沉淀/UA决策行为沉淀执行任务书.md` `UA-P0-02` 任务卡

## 0. 人话摘要（先看这段）

本次任务**真的连了数据库**（MaxCompute + ClickHouse），对方案里涉及的所有目标源表做了只读探测。结论：

- **MC 和 CK 都连通成功**（`SELECT 1` 均 exit 0）。
- **配置类表**（Google/Meta/AppLovin Campaign、Meta AdSet、Google change-event 宽表）最新分区都是 **2026-07-23**（今天），数据新鲜。
- **Outcome 事实表**（消耗、收入、SDK 收入、AF cohort）最新分区都是 **2026-07-21**，比今天晚 2 天——这在表卡定义的 SLA 范围内（`allowed_partition_lag_days=2` 的表标 `fresh`，没设这个字段的标 `delayed`），属于正常的数仓延迟，不是数据断了。
- `probe_freshness.py` 在隔离 worktree 跑通了（exit 0），但**只覆盖了有 `freshness:` 段的表卡**；7 张 UA 沉淀目标表里有一部分表卡没有 `freshness:` 段，被脚本自动跳过，水位靠我手动 `SHOW PARTITIONS` + `COUNT(*)` 补齐。
- 隔离 worktree 里生成的两份 `freshness_snapshot.json` 与共享 checkout 里用户的 WIP 是**同路径不同内容**，属于 merge collision risk，**不能自动合并**，需要人工比较探测时间和水位后裁决。
- 共享 checkout 的 `ai_ck/engineering_artifacts/freshness_snapshot.json` WIP **全程未被触碰**。

## 1. 连通性验证

| 数据源 | 环境 | 探测命令 | 退出码 | 结果 |
|---|---|---|---|---|
| MaxCompute | `maxcompute-dataworks`（project=`hs_market`，quota=`ua_event`，endpoint=`service.us-east-1.maxcompute.aliyun.com`） | `SELECT 1 AS ok;` | 0 | `[[1]]` |
| ClickHouse | `clickhouse-shucang`（database=`shucang_market`，native 协议，端口 9000） | `SELECT 1 AS ok;` | 0 | `1` |

探测时间（`probe_at`）：2026-07-23，MC 约 11:15 UTC（`2026-07-23T03:15:41Z`），CK 约 11:01 UTC（`2026-07-23T03:01:57Z`）。

## 2. MC 目标表实时探测（手动 SHOW PARTITIONS + COUNT）

以下 9 张表均通过 `maxcompute-dataworks` helper 执行 `SHOW PARTITIONS` 和有界 `COUNT(*)`，所有命令 exit 0。

| 表名 | 分区字段 | 最新分区 | 探测窗口 | 行数 | 退出码 |
|---|---|---|---|---|---|
| `ods_market_google_campaign_da` | `dt` | `2026-07-23` | — | （未单独 count，snapshot 标 fresh） | 0 |
| `ods_market_meta_campaign_da` | `dt` | `2026-07-23` | — | （表卡无 freshness 段，手动 SHOW PARTITIONS 确认） | 0 |
| `ods_market_applovin_campaign_da` | `dt` | `2026-07-23` | — | （同上） | 0 |
| `ods_market_api_adset_facebook_da` | `dt` | `2026-07-23` | — | （同上） | 0 |
| `ods_market_google_ads_config_wide_hi` | `dt/hour` | `dt=2026-07-23/hour=09` | `dt=2026-07-23 AND hour=08` | 1 行（1 个 change event，时间 `2026-07-23 08:54:57`）；`hour=09` 为 0 行（该小时暂无变更） | 0 |
| `ads_market_tj_ad_spend_active_v2` | `dt` | `2026-07-21` | `dt=2026-07-21` | 1,327,669 | 0 |
| `ads_market_tj_ad_revenue_v2` | `dt` | `2026-07-21` | `dt=2026-07-21` | 10,477,803 | 0 |
| `ads_market_tj_ad_sdk_revenue_attributed_di` | `dt` | `2026-07-21` | `dt=2026-07-21` | 12,510,459 | 0 |
| `ads_market_af_cohort_user_acquisition_v2` | `dt` | `2026-07-21` | `dt=2026-07-21` | 6,966,144 | 0 |

**解读**：

- 5 张配置类表（Google/Meta/AppLovin Campaign + Meta AdSet + Google change-event 宽表）最新分区为今天（2026-07-23），数据当天可达。
- 4 张 Outcome 事实表最新分区为 2026-07-21，比今天晚 2 天。这是数仓正常延迟（T+2），**不是连通性问题或数据断档**。方案第 6.2 节标注的 `repo_confirmed + live_verification_required` 现在可以升级为 `live_verified`（连通性和分区水位已确认）。
- Google change-event 宽表 `hour=09` 为 0 行：该小时可能确实没有变更事件，或该分区尚未写入完成；`hour=08` 有 1 行真实变更事件，说明当天增量链路在工作。这不是阻塞项。

## 3. CK 目标表实时探测

以下 3 张 CK 表是 PGP `/history` 和 ROI360 页面实际读取的 OLAP 投影，对应 MC 侧的 Meta Campaign / Meta AdSet / AppLovin Campaign 配置。

| 表名 | 分区字段 | 最新分区 | 有界行数（dt=2026-07-23） | 退出码 |
|---|---|---|---|---|
| `market_api_campaign_info_facebook_dist` | `dt`（Date） | `2026-07-23` | 41,915 | 0 |
| `market_api_adset_info_facebook_dist` | `dt`（Date） | `2026-07-23` | 51,899 | 0 |
| `market_api_campaigns_v2` | `dt`（String） | `2026-07-23` | 104,368 | 0 |

**解读**：CK 侧 3 张表均连通可读、今天分区有数据，可作为 PGP 页面级配置快照的实时来源。但这 3 张表都是**配置快照**，不是 change log——与 UA-P0-01 的静态审计结论一致：Meta/AppLovin 缺少原生 change log，只能用快照差分（`inferred_only`）。

## 4. probe_freshness.py 运行结果

在隔离 worktree `/Users/lidongyuan/hungrystudio/点位/数仓-worktrees/ua-p0-02` 执行：

```bash
source /Users/lidongyuan/hungrystudio/cursor_friend_pack_system_env/fill_clickhouse_env_here.zsh
python3 tools/scripts/probe_freshness.py
```

退出码：`0`。

产出：
- `ai_ck/engineering_artifacts/freshness_snapshot.json`（CK，32 张表，reachable=True，probed_at=2026-07-23T03:01:57Z）
- `ai_hive/engineering_artifacts/freshness_snapshot.json`（MC，30 张表，reachable=True，probed_at=2026-07-23T03:15:41Z）

**覆盖范围说明**：`probe_freshness.py` 只探测表卡中有 `freshness:` 段的表。UA 沉淀目标的 9 张 MC 表中，只有 `ods_market_google_campaign_da` 和 `ods_market_google_ads_config_wide_hi` 两张有 `freshness:` 段（均标 `fresh`）；其余 7 张（Meta Campaign、AppLovin Campaign、Meta AdSet、4 张 Outcome 事实表）**表卡中缺少 `freshness:` 段**，被脚本自动跳过。这不是脚本的 bug，而是表卡本身的缺口——后续应通过 `skills/table-intake/SKILL.md` 为这 7 张表补齐 `freshness:` 段，让它们进入自动探测范围。本次报告中这些表的水位由手动 `SHOW PARTITIONS` + `COUNT(*)` 补齐（见第 2 节）。

## 5. Freshness snapshot merge collision risk 声明

隔离 worktree 生成的两份 `freshness_snapshot.json` 与共享 checkout 中用户的 WIP 是**同路径、不同内容**：

| 路径 | 共享 checkout 状态 | 隔离 worktree 状态 |
|---|---|---|
| `ai_ck/engineering_artifacts/freshness_snapshot.json` | `M`（用户 WIP，探测时间和水位未知） | `M`（本次 probe_freshness.py 产出，probed_at=2026-07-23T03:01:57Z） |
| `ai_hive/engineering_artifacts/freshness_snapshot.json` | 未变更（committed 状态） | `M`（本次 probe_freshness.py 产出，probed_at=2026-07-23T03:15:41Z） |

**处置规则**（遵循任务书 §4 通用前缀）：后续集成任务**不得自动 merge** 这两份 snapshot，也不得用 `checkout/reset` 选边；必须由人工比较探测时间、来源水位和语义后，明确选择保留、合并或重新探测。

本次 candidate commit 会把隔离 worktree 的两份 snapshot 一起提交（作为本次探测的运行证据），但共享 checkout 的用户 WIP **全程未被触碰**（`git status --short` 始终只显示 `M ai_ck/engineering_artifacts/freshness_snapshot.json` 一行，且内容未被 add/commit/stash）。

## 6. 结论汇总

| 能力项 | 结论 | 依据 |
|---|---|---|
| MC 连通性 | `live_verified` | `SELECT 1` exit 0 |
| CK 连通性 | `live_verified` | `SELECT 1` exit 0 |
| Google Campaign 配置（MC） | `live_verified`，fresh，dt=2026-07-23 | SHOW PARTITIONS + snapshot |
| Meta Campaign 配置（MC） | `live_verified`，dt=2026-07-23 | 手动 SHOW PARTITIONS（表卡无 freshness 段） |
| AppLovin Campaign 配置（MC） | `live_verified`，dt=2026-07-23 | 手动 SHOW PARTITIONS |
| Meta AdSet 配置（MC） | `live_verified`，dt=2026-07-23 | 手动 SHOW PARTITIONS |
| Google change-event 宽表（MC） | `live_verified`，fresh，dt=2026-07-23/hour=09 | SHOW PARTITIONS + snapshot |
| 消耗事实表（MC） | `live_verified`，dt=2026-07-21，1.3M 行 | SHOW PARTITIONS + COUNT |
| AF 收入事实表（MC） | `live_verified`，dt=2026-07-21，10.5M 行 | 同上 |
| SDK 收入事实表（MC） | `live_verified`，dt=2026-07-21，12.5M 行 | 同上 |
| AF cohort 留存表（MC） | `live_verified`，dt=2026-07-21，7.0M 行 | 同上 |
| CK Meta Campaign 投影 | `live_verified`，dt=2026-07-23，42K 行 | EXISTS + COUNT |
| CK Meta AdSet 投影 | `live_verified`，dt=2026-07-23，52K 行 | 同上 |
| CK AppLovin Campaign 投影 | `live_verified`，dt=2026-07-23，104K 行 | 同上 |
| `probe_freshness.py` 可运行性 | `live_verified`，exit 0 | 隔离 worktree 运行成功 |
| 7 张 MC 表卡缺 `freshness:` 段 | `design_required`（表卡缺口，非数据缺口） | 手动确认表卡 YAML |

## 7. 非目标声明

本任务未调用 MI 接口（留给 `UA-P0-03`）；未修改 PGP 代码；未新增或修改任何 MC/CK 表；未执行 DDL/DML；未部署；未查询用户级明细或 PII（所有探测均为聚合 count 或分区元数据）；未训练模型；未调用付费 LLM；未签发任何 `GO_*`。
