# 数据底座维护 Harness

> 状态：低风险路径已验证；**未**升正式 runbook。
> 更新：2026-07-25（清掉 2026-06-20 已完成验收流水）
> 现行 adapter：`ai_ck/engineering_artifacts/CK维护流程.md`、`ai_hive/engineering_artifacts/Hive维护流程.md`
> 预检入口：`python3 tools/scripts/maintain_data_base.py`（只分流，不自动修/probe/回归）

## 已完成（不再当待办）

- CK / Hive adapter、三层 README、`agent_manifest` asset layers
- 低风险 Hive 表卡 freshness 真实变更
- CK schema drift（含 `schema_drift.json` 分流）
- candidate SQL live revalidation、verified SQL 正向晋升
- knowledge 默认召回负向门禁 + 正向晋升（`默认召回边界与晋升规则.md` + K7）
- semantic governance 真实变更（Day0 ARPU / ROI 动作边界 + R10）
- healthcheck / 表卡 / 检索 / 语义 compose / Agent 回归串联

细节不在 TODO 复述；需要时看各库维护流程与 `tools/scripts/maintain_data_base.py`。

## 仍开

| 项 | 缺口 | 完成标准 |
|---|---|---|
| P0 深卡验证 | 尚无「会改默认选表 / join / PII 边界」的真实 CK/Hive 变更跑过全局分流 | 至少 1 次此类变更：影响面判断正确，门禁全绿或明确 `BLOCKED` |
| P0 默认召回联动 | 业务语义新知识进 `catalog.yaml` 默认召回时，semantic / vsql / 表卡联动未用高风险案例压过 | 1 次真实晋升，联动清单可复现 |
| P1 入口能力 | `maintain_data_base.py` 不执行修复 / live probe / 回归 | 要不要扩成半自动执行：另议；扩前先过 P0 |
| P2 迁 runbook | 仍在 TODO，避免被当成正式流程 | P0 通过后迁 `tools/runbooks/数据底座维护Harness.md`，并改 `tools/runbooks/README.md`、检索图 |

## 决策边界

Agent 可以先做：结构分层、召回边界、表卡/manifest/README 一致性、脚本门禁串联、TODO/blocker 显性化。

需要人确认：Hive 高风险默认召回与 L3 晋升；官方口径 / 默认指标 / 阈值 / canonical；默认选表、join、PII 边界；高风险投放治理动作。
