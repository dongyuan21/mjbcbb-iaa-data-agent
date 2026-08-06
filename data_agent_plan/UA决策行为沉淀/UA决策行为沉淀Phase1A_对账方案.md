# UA 决策行为沉淀 Phase 1A — 对账方案（UA-1A-09V）

> 日期：2026-07-23
> 分支：`codex/ua-1a-09r-10-20260723`
> Base commit：`6e38f0e3`

## 0. 人话摘要

这个方案定义"怎么验证全链路数据是对的"——从采集到 Episode 每一步的数量、主键、水位都要能对上。

## 1. 数量对账检查点

| 检查点 | 公式 | 当前可做？ |
|---|---|---|
| Observation 数 = MI API 返回行数 | `len(observations.jsonl) == sum(rows across pages)` | ✅ dry-run 已验证（operates=7, remarks=13） |
| Change log 数 = Observation 数 | `len(change_log.jsonl) == len(observations.jsonl)` | ✅ dry-run 已验证（7=7） |
| Canonical event 数 = Change log 数 | `len(canonical_event.jsonl) == len(change_log.jsonl)` | ✅ dry-run 已验证（7=7） |
| Opportunity 数 ≤ DecisionSubject 数 | 每个 subject 每天最多 1 个主机会 | ✅ mock 已验证 |
| 标签数 = Opportunity 数 | 每个 opportunity 恰好一组标签 | ✅ mock 已验证 |
| 特征快照数 = Opportunity 数 | 每个 opportunity 恰好一个快照 | ✅ mock 已验证 |
| Outcome 数 = Opportunity 数 × 窗口数 | D3/D7/D14 各一行 | ✅ mock 已验证 |
| Episode 数 ≤ Opportunity 数 | 合并后可能少于 | ✅ mock 已验证 |
| Admission projection 数 = scope 数 | 每个 scope 一行 | ✅ mock 已验证 |

## 2. 主键/水位对账

| 检查点 | 规则 | 当前可做？ |
|---|---|---|
| Observation 去重 | 同一 (date+create_time+description_hash+operator_token) 不重复 | ✅ 采集器内置 |
| Coverage watermark | `source_watermark == max(event_at_raw across observations)` | ✅ dry-run 已验证 |
| Episode evidence_hash | 相同输入产生相同 hash | ✅ 测试已验证 |
| Admission version 唯一 | 同一 scope 内 admission_version 不重复 | ✅ 测试已验证 |

## 3. 需要物理表落地后才能做的

| 检查点 | 为什么现在做不了 |
|---|---|
| MC 表行数 vs JSONL 行数 | 物理表不存在 |
| CK projection vs MC manifest 一致性 | CK 表不存在 |
| Freshness 门禁 | 表卡无 freshness 段（design_candidate） |
| Agent regression | 不涉及表卡/knowledge 改动 |
| 跨日期分区连续性 | 物理表不存在 |

## 4. Freshness 门禁验证

当前状态：19 张表卡均为 `design_candidate`，无 `freshness` 段。待物理表落地后：
1. 为 19 张表补齐 `freshness` 段（partition_field / expected_latency_hours / probe）
2. 运行 `probe_freshness.py` 刷新 snapshot
3. 确认所有表 `fresh` 或 `delayed`（无 `unknown`/`stale`）

## 5. 部署验证（物理表落地后）

| 检查项 | 方法 |
|---|---|
| MC 表存在 | `SHOW TABLES LIKE '*decision*'` |
| MC 分区可写 | `SHOW PARTITIONS <table>` |
| CK projection 可读 | `SELECT count() FROM shucang_market.<projection_table>` |
| Admission projection fail closed | 空 manifest → projection 返回 not_admitted |
| 幂等重跑 | 重跑同一窗口，行数不变 |

## 6. 非目标声明

本方案未执行 DDL/DML；未部署；未触碰共享 WIP。
