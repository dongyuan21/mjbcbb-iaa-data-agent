# TODO · DataAgent 只读 Runtime POC

> 状态：ready_to_start（触发条件已满足，待排期）
> 性质：独立工程，与知识库治理不同量级；不在本轮结构治理内展开。
> 来源：`data_agent_plan/DataAgent推进路线图.md` Phase 6；控制面已由本轮治理理顺。

## 目标

实现一个**只读**的自研 DataAgent runtime，消费现有控制面（路由图 + task_routes + catalog/manifest + 表卡 + 语义契约 + verified SQL + 门禁），把自然语言投放/数据问题跑成"带证据、带 freshness、带 needs_decision"的回答。**只读分析，不做停投/放量/降预算等自动动作，不建闭环数据库。**

## 触发条件（已满足）

| 条件 | 路线图门槛 | 当前 |
|---|---|---|
| verified SQL | ≥10 | 27 |
| 分析 SOP | ≥3 | 已具备 |
| 端到端复盘 case | ≥1 | 已具备（如 mi_roi360 反推、BB 预装 ARPU 闭环）|
| 门禁 + 回归 | 全过或仅 freshness 阻断 | 全过（含 metric_layer_boundary、顶层覆盖、task_routes 校验）|

## Runtime 六步（只读闭环）

1. **任务识别**：自然语言 → 标准化为任务类型、产品、端、时间、维度、指标、freshness 要求。任务类型对齐 `task_routes/INDEX.yaml`。
2. **检索路由**：读 `task_routes/INDEX.yaml` 选任务 → 只加载该 `task_routes/<id>.yaml` 的 `first_read` / `allowed_assets`；命中表再读对应表卡。**禁止整包加载 agent_knowledge。**
3. **门禁执行**：强制 freshness / PII / source / owner / raw-draft gate；未连通 MC/CK 时只输出 snapshot_only / connectivity_unverified。
4. **SQL 路径**：优先复用 `da_assets/verified_sql/`；缺口场景只生成带字段证据（`Text2SQL字段证据模板.md`）的 candidate SQL，写入 `da_assets/candidate_sql/`。
5. **结果校验**：检查分区、行数、空值、指标方向、候选状态、业务动作边界。
6. **资产回写**：candidate/validated SQL、SOP、decision case、待拍板事项写回既有目录，更新 `da_assets/index.yaml`。

## 消费的控制面（本轮已就绪）

- `AGENT_RETRIEVAL_MAP.yaml`：default_bootstrap（已瘦身）、canonical_owners、never_default_recall、reference_only_dirs、promotion_paths、metadata_contract、task_routing。
- `task_routes/<id>.yaml`：一任务一文件的 first_read / allowed_assets / output_guardrails / completion_boundary / conditional_next_hops。
- 三库 `agent_manifest.yaml` + `agent_knowledge/catalog.yaml`。
- 语义契约 `knowledge/agent_knowledge/semantic_contract/model.json`。
- 门禁：`tools/scripts/check_*.py` + `eval/agent_regression/run_regression.py`（runtime 应把这些作为自检/CI）。

## 非目标（明确不做）

- 不做自动停投 / 放量 / 降预算 / 改预算等写动作。
- 不建 question→action→aftereffect 闭环数据库（第一阶段仍用 `da_assets/decision_cases/` markdown 沉淀）。
- 不依赖外部 agent 框架；自研开源 runtime。
- 不执行源包 telemetry 或独立 MaxCompute/CK 配置脚本。

## AI 自主边界与可跑完性

### AI 可自主决策并执行（其本职：检索 / 执行 / 验证 / 总结，不新增业务事实、不动架构取舍）

- 搭建消费 `task_routes/INDEX.yaml` + 门禁的 runtime 骨架（任务识别 → 路由 → 只取命中资料）。
- 复用 `da_assets/verified_sql/`；按 `Text2SQL字段证据模板.md` 生成 candidate SQL（默认 candidate，不自升 verified）。
- 用现有门禁套件自检（确定性、可无人值守）。
- 把 candidate / SOP / case / 待拍板事项回写既有目录并更新 `da_assets/index.yaml`。

### 需人先拍板（方向 / 取舍 / 重大架构，AI 先给权衡再做）

- runtime 落地形态：CLI / 常驻服务 / 库。
- 输入输出契约（IO contract）。
- candidate → verified 的最终采信（门禁之外的信任判断）。

### AI 永远不替决定（按只读基座设计）

- organic 是否计入 KPI、SDK/AF 回收口径取舍、红线 / 达标阈值。
- 停投 / 放量 / 降预算等任何投放动作。

### 能不能自动跑完

- **只读分析骨架：能。** AI 可端到端搭完并用门禁自检，这部分可无人值守跑完。
- **完整跑通真实问答：不能完全无人值守**，有三个硬依赖：
  1. **架构前置**：落地形态 + IO 契约需你先拍，否则 AI 在猜方向。
  2. **真实跑数**：依赖 MC / CK 实时连通 + 分区新鲜（本轮就有 `tj_ad_sdk_revenue` 延迟阻断）；数据不到时按设计阻断，不伪造当前结论。
  3. **业务结论按设计止于"待人拍板"**，跑完 ≠ 给最终动作。
- 结论：**技术骨架 AI 能自主跑完并自检；最终业务结论与架构取舍仍需你拍板。**

### 建议的"第一刀"（AI 现在就能无依赖做）

- 实现"任务识别 + 路由 + 门禁兜底"最小骨架：只读 `task_routes/INDEX.yaml`，对 verified SQL 做复用与 dry-run 自检；不碰真实跑数、不定架构形态。
- 落地形态 / IO 契约给 2~3 个方案 + 权衡，等你选定再展开。

## 验收（POC v1）

- [ ] 能对 `task_routes` 9 类任务各跑通至少 1 个真实问题，输出带 route_taken / data_source / freshness_status / verified_asset_or_sql_source / needs_decision。
- [ ] 单轮上下文以"控制面 + 命中卡"为主，不整包加载表卡层。
- [ ] freshness blocker 时正确降级为历史成熟窗口或排查路径，不伪造当前结论。
- [ ] 生成的新 SQL 默认 candidate，经 `SQL晋升治理.md` 门禁才进 verified。
- [ ] runtime 自检调用现有门禁套件，回归保持绿。

## 下一步动作

1. 选 runtime 落地形态（CLI / 服务），定 IO 契约（输入 NL，输出 `output_contract` 结构）。
2. 实现"任务识别 + 检索路由"最小骨架，直接读 `task_routes/INDEX.yaml`。
3. 接门禁为 runtime 的硬约束层。
4. 用 `eval/agent_regression/regression_cases.yaml` 扩出 runtime 端到端用例。
