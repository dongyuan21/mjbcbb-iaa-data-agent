# UA 决策沉淀 Data Agent 预警能力建设待办

> 创建日期：2026-07-24
> 上游：`data_agent_plan/UA决策行为沉淀/UA决策沉淀v2评估报告.md` §8 DiD Uplift
> 状态：TODO（未开始）

## 一句话说明

UA 决策沉淀 v2 已经产出了 7 组通过安慰剂检验的因果效应估计（DiD），但这些结果目前只存在于评估报告和 `/tmp/` 下的 JSON 文件里，Data Agent 还不能在运行时引用它们。这个 TODO 记录的是"怎么把 DiD 发现变成 Agent 能用的预警能力"。

## 当前成果（已验证）

DiD Uplift 估计结果（安慰剂 10/10 通过，7 组 CI 不含 0）：

| 操作 | 时间窗 | DiD | 95% CI | 解读 |
|------|--------|-----|--------|------|
| status（开关 campaign） | D14 | +28,623 | [+10,638, +51,884] | 关停亏损 campaign 后利润显著提升 |
| status | D7 | +10,205 | [+1,965, +20,867] | 7 天就有效果 |
| geo_exclude（排除国家） | D7 | +5,175 | [+1,030, +8,549] | 排除低价值国家后利润提升 |
| creative（换素材） | D14 | -44,829 | [-67,445, -25,214] | 换素材后利润大幅下降（学习期） |
| creative | D7 | -11,763 | [-19,183, -5,295] | 同上 |
| budget（调预算） | D14 | -17,654 | [-31,577, -2,513] | 调预算后利润下降 |
| budget | D7 | -10,558 | [-17,577, -3,968] | 同上 |

## 需要建设的能力

### 1. DiD 效应表持久化

**问题**：DiD 结果目前在 `/tmp/ua_phase3_v2_did/v2_results.json`，重启就没了。

**方案**：把 DiD 结果写入 `knowledge/agent_knowledge/report_knowledge/` 或 `da_assets/verified_sql/` 下的一个 YAML/JSON 文件，作为 Agent 默认召回的事实。

**内容**：
```yaml
# ua_did_effects_v0.1.yaml
version: v0.1
verified_at: 2026-07-24
method: DiD (双重差分)
placebo_pass: 10/10
data_window: 2026-06-17 ~ 2026-07-24 (Google) + 2025-11-11 ~ 2026-07-24 (MI)
effects:
  - operation: status
    direction: pause
    outcome_window: D14
    did: 28623
    ci_lo: 10638
    ci_hi: 51884
    placebo: 8
    n_treated: 556
    n_control: 2062
    interpretation: "关停亏损 campaign 后 14 天利润平均提升 28623 元"
    confidence: high
    caveat: "DiD 假设平行趋势；非 RCT 因果证明"
  # ... 其余 6 组
```

### 2. Agent 预警规则

**状态**：TODO（未开始）

**场景**：UA 问"这个 campaign ROI 跌破 70%，要不要关停？"

**当前 Agent 回答**：标 `threshold_status: below_red_line`，提示人工跟进。

**增强后 Agent 回答**：
> 该 campaign 7 日 ROI=65%，低于 70% 红线。
> 历史上类似情况关停后，D14 利润平均提升 +28,623 元（CI [+10,638, +51,884]，安慰剂通过）。
> 注意：关停决策需 UA 综合判断，此为参考效应而非建议。

**实现方式**：在 `task_routes/roi_or_campaign_analysis.yaml` 或 `knowledge/agent_knowledge/policies/` 中新增一条规则：当 campaign 触发 `threshold_status=below_red_line` 且 UA 提及"关停/暂停"时，自动召回对应操作类型的 DiD 效应。

### 3. 按 app 分层的效应召回

**状态**：进行中（app 分层 DiD 已在跑，效应表 YAML 持久化在进行）

**问题**：当前 DiD 是全局的，但不同 app 的操作效应可能不同。

**方案**：跑 app 分层 DiD 后，把效应表扩展为按 app 分层的版本。Agent 根据 campaign 的 bundle_id 匹配对应 app 的效应。

**依赖**：app 分层 DiD（进行中）、效应表 YAML 持久化（进行中）。

### 4. 效应刷新机制

**问题**：Google change_event 每天有新数据，DiD 效应应该定期刷新。

**方案**：在 freshness worker 的 cron 中加入每周一次的 DiD 重算任务，刷新效应表。或者手动触发——考虑到 38 天数据量不大，每周手动跑一次也可以。

## 不做什么（边界）

- **不输出"建议立即关停/加预算"**：只提供效应证据，决策由 UA 做
- **不自动执行广告平台写操作**：只读分析
- **不把 DiD 当 RCT 因果证明**：DiD 有平行趋势假设，标 `observational_causal`

## 依赖

- [x] v2 pipeline + DiD 代码（已完成，`tools/scripts/ua_phase3_v2.py`）
- [x] DiD 结果验证（已完成，安慰剂 10/10）
- [ ] DiD 效应表 YAML 文件（待创建）
- [ ] Agent 预警规则配置（待创建）
- [ ] app 分层 DiD（待跑，当前代码支持）

## 版本

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-07-24 | 初版：记录 4 个建设项 + 依赖 + 边界 |
