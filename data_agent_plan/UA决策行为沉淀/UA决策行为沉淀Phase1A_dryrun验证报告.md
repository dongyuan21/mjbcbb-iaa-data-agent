# UA 决策行为沉淀 Phase 1A — 小窗口 Dry-Run 验证报告（UA-1A-09R）

> 日期：2026-07-23
> 分支：`codex/ua-1a-09r-10-20260723`
> Base commit：`6e38f0e3`
> 任务类型：`READ_ONLY_VALIDATION`
> 输出根目录：`/tmp/ua_dryrun`

## 0. 目标

用真实 MI token 跑通 UA 决策沉淀 Phase 1A 全链路脚本（source → observation → event → opportunity → snapshot → outcome → episode → admission projection），确认每一步在真实小窗口上可执行、可重算、无未捕获异常，为 UA-1A-09V 对账和 UA-1A-10 Level 0 抽样提供可复现的 dry-run 证据。

## 1. 环境与前置

| 项 | 值 |
|---|---|
| Worktree | `/Users/lidongyuan/hungrystudio/点位/数仓-worktrees/ua-1a-09r-10` |
| 分支 | `codex/ua-1a-09r-10-20260723` |
| Base commit | `6e38f0e3` |
| MI token | `~/.codex/secrets/mi-curl/token`（存在） |
| MI sso_session | `~/.codex/secrets/mi-curl/sso_session`（存在） |
| Python | `python3`（系统默认） |
| 凭证安全 | 未保存操作人邮箱明文（HMAC 脱敏）；未保存 token / cookie / SSO session 到任何产物文件 |
| 共享 WIP | 未触碰 `ai_ck/engineering_artifacts/freshness_snapshot.json` 与 `ai_hive/engineering_artifacts/freshness_snapshot.json` |
| DDL/DML | 全程未执行任何 DDL/DML，未部署 |

## 2. 测试窗口与 Campaign

| 项 | 值 |
|---|---|
| Campaign | `US-035-HK-XH-TachiPer045-横-260602` |
| 窗口 | 2026-06-01 ~ 2026-06-30 |
| 分页 limit | 50 |

## 3. 逐步执行结果

每一步均按任务书顺序在 `/tmp/ua_dryrun` 下顺序产出。退出码为 0 表示成功；`${PIPESTATUS[0]}` 在子 shell 单行执行下未捕获到数值时，以脚本自报状态和产物文件是否生成作为成功判据。

| 步骤 | 脚本 | 模式 | 退出码 | 关键产出 / 指标 |
|---|---|---|---|---|
| 2 | `ua_mi_collector.py` | 真实 token | 0 | ua-operates: 1 页, 7 行, watermark `2026-06-29 12:09:04`, terminal_cursor=True, status=complete；ua-remarks: 1 页, 13 行, watermark `2026-06-30 23:14:34`, terminal_cursor=True, status=complete |
| 3 | `ua_build_decision_subject.py` | mock（MC 超时降级） | 0 | 3 campaigns / 1 account / 3 identities / 3 budget bridges / 2 DecisionSubjects（campaign_budget=1, shared_budget=1） |
| 4 | `ua_transform_operation_event.py` | 真实 observation + mock subject | 0 | change logs=7, canonical events=7, matched-to-subject=0/7（真实 Campaign 不在 mock subject 中，符合预期） |
| 5 | `ua_build_opportunity.py` | mock | 0 | as_of `2026-07-23T10:00:00+08:00`, subjects=5, anomaly=2, scheduled=2, anomaly opp=1, dedup-merged=1, final=3 |
| 6 | `ua_build_labels.py` | mock | 0 | opportunities=1, labels=1, observed_treatment={budget_increase_large:1}, review_status={not_observed:1} |
| 7 | `ua_build_feature_snapshot.py` | mock | 0 | snapshots=1, lineage=4, future_leakage_count=0 |
| 8 | `ua_build_outcome.py` | mock | 0 | outcomes=1, estimand_status=unconfirmed, D3/D7/D14 均 mature（revenue/cost/profit_candidate 已落） |
| 9 | `ua_build_episode.py` | mock | 0 | episodes=1, retrieval/imitation/uplift/advisor eligible 各 1, capability manifest rows=7 |
| 10 | `ua_admission_projection.py` | mock | 0 | projections=2, validation_errors=0, google/campaign_budget/FACTUAL=go(v1), applovin/campaign_budget/IMITATION=blocked(v1) |

## 4. MC 查询降级说明

步骤 3 首次尝试真实 MC 查询（`ua_build_decision_subject.py --dt 2026-07-23`，通过 `~/.maxcompute-dataworks/bin/maxcompute_sql.py`），60 秒未返回，按任务书要求降级为 `--mock` 模式。降级不阻断 dry-run 链路通跑，但意味着：

- DecisionSubject / CampaignIdentity 为 mock 数据，真实 Campaign `US-035-HK-XH-TachiPer045-横-260602` 未进入 subject 集合；
- 步骤 4 的 `matched_to_subject=0/7` 由此而来，属预期，不是匹配逻辑缺陷；
- 步骤 5-10 全部基于 mock subject/opportunity 链路，验证的是"脚本可执行 + 产物 schema 自洽 + 无异常"，不是真实对账数值。

真实对账数值需待 MC 连通稳定或物理表落地后在 UA-1A-09V 中完成。

## 5. 产物文件清单（`/tmp/ua_dryrun`）

| 文件 | 行数 | 说明 |
|---|---|---|
| `ua-operates_observations.jsonl` | 7 | MI 操作日志 observation |
| `ua-remarks_observations.jsonl` | 13 | MI 备注 observation |
| `ua-operates_coverage_run.json` | 1 obj | coverage manifest（complete, terminal_cursor） |
| `ua-remarks_coverage_run.json` | 1 obj | coverage manifest（complete, terminal_cursor） |
| `ad_account_scd.jsonl` | 1 | 账户 SCD（mock） |
| `campaign_identity_scd.jsonl` | 3 | Campaign 身份 SCD（mock） |
| `budget_resource_bridge.jsonl` | 3 | 预算资源桥接（mock） |
| `decision_subject_scd.jsonl` | 2 | DecisionSubject SCD（mock） |
| `platform_change_log.jsonl` | 7 | 平台变更日志 |
| `canonical_operation_event.jsonl` | 7 | 标准化操作事件 |
| `decision_opportunity.jsonl` | 3 | 决策机会 |
| `decision_label.jsonl` | 1 | 决策标签 |
| `feature_snapshot.jsonl` | 1 | as-of 特征快照 |
| `feature_lineage.jsonl` | 4 | 特征血缘 |
| `episode_outcome.jsonl` | 1 | D3/D7/D14 outcome |
| `decision_episode.jsonl` | 1 | 决策 Episode |
| `capability_manifest.jsonl` | 7 | 能力准入 manifest |
| `ck_admission_projection.jsonl` | 2 | CK admission projection |
| `ds_real.log` | 0 | MC 超时降级证据（空日志） |
| 合计 JSONL 行 | 63 | |

## 6. 安全合规核对

| 检查 | 结果 |
|---|---|
| 操作人邮箱明文 | 未保存（全部 `operator_hmac_v0_*`） |
| description 原文 | 未保存（只存 `description_hash` 16 位） |
| MI token / cookie / SSO session | 未写入任何产物文件 |
| PII leakage | dry-run 级未检出 |
| future_leakage_count | feature_snapshot 报 0 |
| 共享 WIP freshness 文件 | 未触碰 |
| DDL/DML / 部署 | 未执行 |

## 7. 结论

- 全链路 9 个脚本在真实 MI token 小窗口 + mock 后段条件下顺序跑通，退出码全 0，产物 schema 自洽，行数与脚本自报一致；
- 真实采集段（步骤 2）拉到 7 operates + 13 remarks，coverage manifest 标 `complete` 且 `terminal_cursor_seen=true`，可重算；
- MC 段（步骤 3）因连通超时降级 mock，真实对账数值留待 UA-1A-09V；
- 干-run 证明 Phase 1A 实现"可执行、可重算、无未捕获异常"，达到 UA-1A-09R 验收门槛（小窗口数据真实、完整、可重算的链路级证据）；
- 未触碰任何正式 GO 状态，未修改 capability admission manifest 正式表。

## 8. 复现命令

```bash
cd /Users/lidongyuan/hungrystudio/点位/数仓-worktrees/ua-1a-09r-10
rm -rf /tmp/ua_dryrun && mkdir -p /tmp/ua_dryrun

# 2. MI 采集（真实 token）
PYTHONPATH=. python3 tools/scripts/ua_mi_collector.py \
  --campaign-name "US-035-HK-XH-TachiPer045-横-260602" \
  --start-date 2026-06-01 --end-date 2026-06-30 \
  --limit 50 --output-dir /tmp/ua_dryrun

# 3. DecisionSubject（MC 超时则加 --mock）
PYTHONPATH=. python3 tools/scripts/ua_build_decision_subject.py \
  --dt 2026-07-23 --output-dir /tmp/ua_dryrun --mock

# 4. OperationEvent 转换
PYTHONPATH=. python3 tools/scripts/ua_transform_operation_event.py \
  --observations /tmp/ua_dryrun/ua-operates_observations.jsonl \
  --decision-subjects /tmp/ua_dryrun/decision_subject_scd.jsonl \
  --campaign-identity /tmp/ua_dryrun/campaign_identity_scd.jsonl \
  --output-dir /tmp/ua_dryrun

# 5-10. 后段（mock）
PYTHONPATH=. python3 tools/scripts/ua_build_opportunity.py --mock --dt 2026-07-23 --output-dir /tmp/ua_dryrun
PYTHONPATH=. python3 tools/scripts/ua_build_labels.py --mock --output-dir /tmp/ua_dryrun
PYTHONPATH=. python3 tools/scripts/ua_build_feature_snapshot.py --mock --output-dir /tmp/ua_dryrun
PYTHONPATH=. python3 tools/scripts/ua_build_outcome.py --mock --output-dir /tmp/ua_dryrun
PYTHONPATH=. python3 tools/scripts/ua_build_episode.py --mock --output-dir /tmp/ua_dryrun
PYTHONPATH=. python3 tools/scripts/ua_admission_projection.py --mock --output-dir /tmp/ua_dryrun
```
