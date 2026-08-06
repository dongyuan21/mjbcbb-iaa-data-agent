# UA 决策行为沉淀 Phase1C + Phase2 完成报告

> 日期：`2026-07-24`
>
> `WORKTREE=ua-phase1c-2`；`BRANCH=codex/ua-phase1c-2-20260724`
>
> `BASE_COMMIT=a1d9c24a`；`COMMITS=ae2fa823, 2a0509cc`

## 0. 人话摘要

Phase 1C（PGP 三选项反馈）和 Phase 2（案例检索 MVP）全部完成。5 份设计文档 + 4 个脚本 + 4 个测试文件，共 31 个测试全绿。无物理 PGP/CK 表（MaxCompute 无 CreateTable 权限），全部用内存 mock + fixture 实现，输出 JSONL。不依赖向量库或 LLM，不保存 PII，未触碰共享 freshness_snapshot。

## 1. 任务产出与测试结果

### Phase 1C

| 任务 | 产出 | 测试 | 状态 |
|---|---|---|---|
| UA-1C-01 | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase1C_产品API合同.md` | 文档（无代码测试） | ✅ |
| UA-1C-02 | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase1C_DB与Outbox设计.md` + `tools/scripts/ua_pgp_feedback_store.py` + `test_ua_pgp_feedback_store.py` | 9 测试全绿 | ✅ |
| UA-1C-03A | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase1C_OpportunityProjection设计.md` | 文档 | ✅ |
| UA-1C-04 | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase1C_三选项UI合同.md` | 文档 | ✅ |
| UA-1C-05A | `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀Phase1C_Outbox导出合同.md` + `tools/scripts/ua_pgp_outbox_export.py` + `test_ua_pgp_outbox_export.py` | 6 测试全绿 | ✅ |

### Phase 2

| 任务 | 产出 | 测试 | 状态 |
|---|---|---|---|
| UA-P2-01 | `tools/scripts/ua_build_case_index.py` + `test_ua_build_case_index.py` | 6 测试全绿 | ✅ |
| UA-P2-02 | `tools/scripts/ua_case_retrieval.py` + `test_ua_case_retrieval.py` | 10 测试全绿 | ✅ |

## 2. 测试用例总数

**31 个测试**，分布在 4 个测试文件：

| 测试文件 | 测试数 |
|---|---|
| `test_ua_pgp_feedback_store.py` | 9 |
| `test_ua_pgp_outbox_export.py` | 6 |
| `test_ua_build_case_index.py` | 6 |
| `test_ua_case_retrieval.py` | 10 |
| **合计** | **31** |

运行命令与结果：
```bash
cd /Users/lidongyuan/hungrystudio/点位/数仓-worktrees/ua-phase1c-2
for t in test_ua_pgp_feedback_store test_ua_pgp_outbox_export test_ua_build_case_index test_ua_case_retrieval; do
  echo "--- $t ---"
  PYTHONPATH=. python3 tools/scripts/${t}.py 2>&1 | tail -3
done
```
4 套件均输出 `=== All tests passed ===`。

## 3. 关键设计决策

### 3.1 PGP 反馈存储（UA-1C-02）
- **append-only**：feedback 表不允许 UPDATE/DELETE，修改 = 追加新 revision + `supersedes_feedback_id`
- **幂等键**：`(opportunity_id, recorded_at, interaction_mode)`，revision 由服务端分配；同一幂等键二次提交返回已存记录
- **feedback_id** 基于幂等键 hash，保证重复提交同 id
- **无曝光 Control**：`advisor_experiment` 模式 `exposure_id=null` 允许入库（分桶未曝光）
- **PII 不落盘**：`free_note_sanitized` 入库前脱敏（邮箱/手机/URL token 化），outbox 不含自由备注
- **七层分离**：feedback 合同只覆盖 assignment/generation/exposure/feedback 层，operation/outcome 独立

### 3.2 Outbox 安全导出（UA-1C-05A）
- **cursor 分页**：cursor = last event_id，append-only 顺序
- **supersedes 不合并**：旧 event 永久保留，消费方自行 resolve 当前有效反馈
- **PII projection**：导出 20 个安全字段，`free_note_sanitized` 不导出
- **重复读取不改变事实**：导出只读，mark_exported 只回填时间戳

### 3.3 案例索引（UA-P2-01）
- **合格 case 携带检索维度**：platform/budget_tier/lifecycle_stage/observed_treatment/data_maturity + numeric_features
- **future_case_leakage 检测**：`case_close_time > query_as_of` 不进索引
- **排除原因列表化**：支持多原因（not_retrieval_eligible / source_unavailable / test_episode / missing_case_close_time / future_case_leakage）

### 3.4 案例检索（UA-P2-02）
- **硬过滤 5 维度**：platform / 预算层级 / 生命周期 / 动作类型 / 数据成熟度（query 未指定的维度开放）
- **数值相似度**：5 维标准化距离的补（cost/roi/cpi/budget_utilization/trend），无可比维度返回 0.5
- **综合排序**：相似度 0.6 + 证据完整度 0.15 + 结果成熟度 0.15 + 时间距离 0.10
- **结果成熟度**：`estimand_status=confirmed` → 1.0，`unconfirmed` → 0.4
- **不以低相似度补足 Top-K**：min_similarity 门槛（默认 0.3）过滤后再 Top-K，无合格案例返回 `no_eligible_similar_case`
- **不依赖向量库或 LLM**

## 4. 当前状态

- 全部代码为 `design_candidate` 阶段，内存版 mock + fixture，输出 JSONL
- 无物理 PGP DB / CK 表（待 MaxCompute CreateTable 权限 + CK DDL 授权）
- 无 advisor 前端，`advisor_experiment` 模式仅靠 fixture 验证
- 未部署、未触碰共享 WIP（freshness_snapshot）
- 分支 `codex/ua-phase1c-2-20260724` 两个 commit：`ae2fa823`（基础实现）+ `2a0509cc`（案例检索增强）

## 5. 后续依赖

1. **物理 PGP DB 落地**：feedback 表 + outbox 表 DDL（待 DB 权限），内存版接口可直接切换
2. **物理 CK OpportunityProjection 表**：待 CK DDL 授权，typed read API 切为 ClickHouse 查询
3. **outbox 消费 ETL**：UA-1C-05A 导出 → 回填 `has_feedback` / `current_feedback_decision`
4. **advisor 渲染服务**：接入 typed read API + 三选项 UI 合同
5. **案例检索物理化**：Episode JSONL 落到 MC 物理表后，case index builder 切为 MC 查询
6. **人工 Gate**：所有 `design_candidate` 文档需人工确认冻结
