# 红黄线 ROI 双日 review 筛选 SOP

## 状态

| 项 | 内容 |
|---|---|
| 状态 | `trial_active` |
| 入口脚本 | `tools/scripts/run_redline_bidaily_review.py` |
| Runbook | `tools/runbooks/红黄线ROI双日review.md` |
| 决策纪要 | `da_assets/decision_cases/20260625_红黄线双日review规则DA确认.md` |

## 何时用

- 双日投放 review 会前/会后
- 用户或 Agent 问「哪些 campaign 红黄线命中」「早期 ROI 跌破」「双日 review 报表」

## 执行

```bash
python3 tools/scripts/run_redline_bidaily_review.py
```

读取 `eval/红黄线双日review_latest.md`。

## 口径要点

1. **主判据**：达红线门槛法（非单独 ROI360 vs 红线）。
2. **命中清单**：全部 `命中(需看)`，不做 TopN 裁剪。
3. **阈值**：`PACKAGE_ROI_TARGET_THRESHOLDS.csv`；投放达标线 ≠ 包维度标准。
4. **边界**：只预警；`action_boundary=alert_only_no_auto_placement`。

## Agent 输出要求

- 引用报表中的 `标记原因` / `失败明细` 作为证据
- 包体干净但 campaign 命中 → 标明 `object_grain=campaign`
- 不得建议自动停投/放量/改预算

## 长任务 / Runtime 档位

| 档位 | 场景 | PI max_turns | bash 上限 |
|---|---|---:|---:|
| `default` | 常规问答/SQL | 20 | 6 |
| `long_report` | 本 SOP（读报表或跑 1 次脚本） | 12 | 3 |
| `long_investigation` | PI 日志复核等 | 40 | 20 |

环境变量（`runtime/backend/.env`）：`DATA_AGENT_PI_MAX_TURNS_LONG_REPORT`、`DATA_AGENT_LONG_SCRIPT_TIMEOUT_SEC=900`

**定时任务优先**：cron 产出 latest → Agent 只读 md，不走长对话。
