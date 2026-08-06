# Task Routes 治理说明

> 范围：`task_routes/` 控制面、runtime route decision、route regression、trace 复盘。本文不定义业务口径，不替代表卡、SQL 协议或投放治理政策。

## 当前结构

当前 `task_routes/INDEX.yaml` 按领域聚合为 6 大类、18 个叶子路由：

| 大类 | 中文 | 小类 |
|---|---|---|
| `data_sql_foundation` | 数据与 SQL 基础能力 | `table_question`、`product_bundle_mapping`、`text2sql_or_sql_planning`、`data_foundation_health_or_freshness_audit` |
| `roi_campaign` | 投放 ROI 与 Campaign 分析 | `roi_or_campaign_analysis`、`redline_bidaily_review`、`google_ads_config_change_analysis`、`bb_us_ua_media_source_dnu_delta_analysis`、`bb_preinstall_day0_arpu_ecpm_analysis`、`mi_roi360_analysis` |
| `iaa_product_and_monetization` | IAA 变现、产品行为与实验 | `monetization_performance_analysis`、`product_behavior_or_experiment_analysis` |
| `point_material_special_topics` | 点位与素材专题分析 | `point_s2s_analysis`、`material_analysis` |
| `knowledge_governance` | 知识入库与治理 | `report_intake`、`knowledge_or_filesystem_governance`、`table_intake_or_catalog_update` |
| `answer_service_quality` | 问答链路观测与回归复核 | `answer_chain_quality_review` |

`domain_category` 只用于人类治理和报告聚合；runtime 真正执行策略来自每个 route 文件里的 `task_profile`、`first_read`、`allowed_assets`、`mandatory_protocols`、`conditional_protocols` 和 `output_guardrails`。

## 聚合逻辑

当前结构不是从底层表或目录自动聚类出来的，而是从任务边界自底向上收敛：

1. 先识别底层能力边界：表字段问答、业务 SQL、ROI 分析、报告入库、runtime trace 复核。
2. 再把共享证据链聚到同一 route：例如 ROI / campaign 共用投放政策、阈值、verified SQL 和 freshness 规则。
3. 对容易混淆的任务拆专门 route：例如 Google Ads 操作记录、MI ROI360 页面、表准入、runtime trace。
4. 最后用 `domain_category` 做人类可读大类，不把大类当默认召回包。

这个设计的关键不是分类漂亮，而是可审计、可回放、可防止误召回。

## Route 文件必须包含

每个 `task_routes/<id>.yaml` 必须至少包含：

- `id`：必须等于文件名 stem。
- `maturity` / `last_verified` / `regression_coverage`：说明成熟度和验证覆盖。
- `context_budget`：限制首读文件数、首读字符数、资产上下文字符数，避免大包召回。
- `lifecycle`：说明 owner area、复核节奏和是否被废弃。
- `first_read`：选中 route 后必须读的协议、SOP、manifest 或表卡入口。
- `allowed_assets`：允许召回的资产范围。
- `mandatory_protocols`：所有命中该 route 都必须注入的短协议。
- `conditional_protocols`：只在问题命中特定信号时注入的专项协议。
- `output_guardrails`：回答必须遵守的证据、freshness、边界和禁止项。
- `completion_boundary`：什么情况下可以认为任务完成。

## 成熟度判定

`maturity` 表示当前 route 契约能否作为稳定控制面使用，不等于“已经部署生产环境”，也不等于 N=3/N=5 的长期稳定性结论：

| 值 | 判定 |
|---|---|
| `seed` | 只有路由骨架或候选边界，尚未形成完整上下文、护栏和回归证据。 |
| `partial` | 契约可以运行，但仍缺与该路由类型匹配的关键验收证据，或已有已知边界未闭环。 |
| `production_ready` | 契约、上下文预算、输出护栏和静态回归均已通过；需要现场取数的外部 `live_sql` 路由还必须登记并通过至少一条真实 replay。 |

不同类型不能用同一条“必须线上跑数”规则硬套：

- 外部 `live_sql`：必须有正向/相邻边界静态回归、真实问题和已执行 replay；已执行证据不得从自由文本 `review_status` 推断，必须在 case 中登记 `live_validation.status=pass`、验证日期和仓库内证据文档。N=3/N=5 属于独立稳定性基线，用于识别 flaky，不反向把已经满足单次真实验收的 P0 重新标成未完成。
- `evidence.require_executed_sql_match=true` 的 route 必须使用 `task_profile=live_sql`，避免答案契约要求实际查数，Runtime 却按 `default` profile 执行。
- 外部 lookup / 解释类：可以用静态正例、hard negative、真实问题和 focused test 晋升，不强制制造无意义 SQL 或业务 job。
- `internal_codex_ops`：以技能入口、召回边界、focused test 和离线治理门禁为验收；远程 runtime 默认不可见，因此不要求线上用户 replay。
- 任何类型只要缺 freshness、PII、source 或 owner 边界，都不得仅凭 case 数量晋升。
- `regression_coverage` 引用的 static/replay case ID 必须在对应 registry 中真实存在，replay 的 `expect_route` 必须与声明 route 一致；不能用拼错 ID 或跨路由 case 让成熟度门禁误通过。

## 新增或修改 route 的流程

1. 修改 `task_routes/INDEX.yaml`：补 `domain_category`、正负信号、disambiguation、trigger examples。
2. 新建或更新 `task_routes/<id>.yaml`：补齐 route 契约、预算、生命周期和回归覆盖。
3. 更新 `eval/agent_regression/regression_cases.yaml`：至少补一个静态 route case；容易混淆时补 route golden case。
4. 如涉及 Runtime replay 或线上稳定性，更新 `eval/runtime_replay_regression/cases.yaml`。
5. 运行门禁和单测。

## 验证命令

```bash
python3 tools/scripts/check_agent_retrieval_map.py
PYTHONPATH=runtime/backend python3 -m pytest runtime/backend/tests/test_task_profiles.py -q
PYTHONPATH=runtime/backend python3 tools/scripts/runtime_replay_regression.py --validate-only
python3 eval/agent_regression/run_regression.py
```

线上 test 环境 smoke：

```bash
PYTHONPATH=runtime/backend python3 tools/scripts/runtime_deploy_smoke.py \
  --base-url https://pgp-v1-xgboost.youxi123.com \
  --env-id 811 \
  --timeout 180 \
  --machine-id codex-route-smoke \
  --expect-answer-contains runtime-smoke-ok \
  --expect-trace-provider runtime \
  --expect-route-decision-reason
```

如果线上 test 版本尚未部署 route trace 改动，可先不加 `--expect-route-decision-reason` 做基础链路 smoke；最终验收必须加该参数，证明 `retrieved.route_decision_reason` 和 `tool_calls.route_decision_reason` 已落库。

误路由复盘：

```bash
PYTHONPATH=runtime/backend python3 tools/scripts/audit_route_confusion.py --env-id 811 --limit 50
```

该脚本输出 `eval/route_confusion/route_confusion_latest.md` 和 `eval/route_confusion/route_confusion_latest.json`。

## 当前复盘基线

2026-07-02 对 `market-data-agent-test` 最近 50 条 trace 做复盘：

- 当前本地 router 与线上落库 route 一致率：`47/50 = 94%`。
- 3 条差异均为线上旧版落到 `text2sql_or_sql_planning`，当前本地 router 更倾向 `roi_or_campaign_analysis`。
- 线上 `b1e9b0c8` 尚未包含 `route_decision_reason` 落库字段，部署后需复验 trace 可解释字段。

## 维护原则

- 不因一个泛词把 route 合并回大包；优先用正负信号和 golden case 消除歧义。
- `mandatory_protocols` 必须短，只放所有问题都要读的协议。
- `conditional_protocols` 必须窄，只在专项信号明确时触发。
- `route_decision_reason` 必须可落库，便于 Runtime trace 复核和误路由回放。
- warning 也阻断 `check_agent_retrieval_map.py`，避免治理漂移。
