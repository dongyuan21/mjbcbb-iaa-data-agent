# TODO · KV缓存命中与压缩关系观测计划

> 状态：**模板就绪，待执行采集**（2026-07-16 更新：D-1 per-stage token 计量已就绪，工具链阻塞已部分解除）
> 约束：仅建设文档，不写实现代码；采集执行前不创建原始数据文件
> 关联：`上下文工程与Runtime下一步规划.md`、`../showoff/02-控制面与检索/Agent知识按需加载与上下文预算.md`
> 归档模板：`tools/runbooks/KV缓存命中观测归档模板.md`（模板文件可追踪；真实观测产物仍归档到 `eval/kv_cache_observation/`）

## 要回答的问题

1. 上下文压缩后，`cached_tokens / prompt_tokens` 是否提升？
2. 命中变化主要来自 token 变少，还是来自前缀稳定度提升？
3. 对实际体验（TTFT、prefill latency、总响应时长）影响多大？

## 实验边界

- 只观测读路径（不涉及写库、不改业务逻辑）。
- 只做 A/B 观测设计与记录规范，不在本任务中执行。
- 先做 Stage0 范围：`default_bootstrap` 与任务路由加载策略，不扩展 Stage2 索引检索化。

## A/B 观测设计（待执行）

- **A 组（对照）**：较重上下文加载方式（保留更多固定前缀）。
- **B 组（实验）**：当前瘦身后的加载方式（bootstrap + 按需路由）。
- **任务样本**：覆盖 `table_question`、`text2sql_or_sql_planning`、`roi_or_campaign_analysis` 三类高频问答，各 10~20 条。
- **重复次数**：每条样本至少 3 次，分冷启动与热启动记录。

## 指标定义

> 字段与类型已在 `tools/runbooks/KV缓存命中观测归档模板.md` 第一节完整定义，此处仅列指标名。

- `prompt_tokens`
- `cached_tokens`
- `cache_hit_rate`（`cached_tokens / prompt_tokens`）
- `ttft_ms`（首 token 延迟）
- `prefill_ms`
- `total_latency_ms`
- `route_taken`（命中的任务路由）

辅助字段（需相位 D-1 token 计量就绪）：
- `bootstrap_tokens` / `route_prompt_tokens` / `index_tokens` / `table_card_tokens` / `generation_tokens`

## 记录模板

> 已固化到 `tools/runbooks/KV缓存命中观测归档模板.md` 第二节（CSV 模板）与第三节（Markdown 汇总表）。
> 原始 CSV 归档路径：`eval/kv_cache_observation/raw/kv_cache_obs_{YYYYMMDD}_{A|B}.csv`
> 汇总 Markdown 归档路径：`eval/kv_cache_observation/kv_cache_obs_{YYYYMMDD}_summary.md`
> 结论归档路径：`eval/kv_cache_observation/kv_cache_obs_{YYYYMMDD}_conclusion.md`

快速参考——必录 CSV 表头：
```
date,task_type,variant,sample_id,run_seq,prompt_tokens,cached_tokens,cache_hit_rate,ttft_ms,prefill_ms,total_latency_ms,route_taken,notes
```

## 验收口径（样板已固化，待执行验证）

✅ 统计口径已固化在 `tools/runbooks/KV缓存命中观测归档模板.md` 第四节：

- **P50（中位数）** 反映典型体验，**P90** 反映长尾体验；均值仅作补充。
- **每组每任务类型 n ≥ 30** 条有效记录方可参与 P50/P90 对比；不足 30 条标注 `样本不足(n=XX)`。
- **冷/热分列**：`run_seq=1` 为冷启动（命中率预期为 0 或极低），`run_seq≥2` 为热启动。
- **异常值剔除**：延迟超同组 P95 3× → 标 outlier；cached > prompt → invalid 剔除；请求错误 → 标 error_flag，不参与延迟分析。
- 命中率提升阈值：**+10%** 为可接受，**+15%** 为显著。
- 若命中率提升不明显，`prompt_tokens` 下降仍可作为主要收益标准（推理成本下架）。
- 若延迟收益与命中收益冲突，优先级由人拍板（成本优先 vs 交互体验优先）。

## 执行清单（TODO）

- [x] 确认 A/B 方案最终定义与采样窗口。
- [x] 确认统计口径（P50/P90 + n≥30 + 冷热分列）。
- [x] 结果归档路径与模板（`eval/kv_cache_observation/`，CSV/Markdown/结论模板已固化）。
- [ ] 执行采集并回填记录模板。（阻塞条件：① ~~工具链就绪~~ ✅ D-1 per-stage token 计量已于 2026-07-14 完成，Runtime 可输出 `prompt_tokens` / `cached_tokens`；② 样本采集环境确认）
- [ ] 形成结论：继续压缩 / 保守回调 / 进入 Stage2。
- [ ] 结论沉淀到 `TODO/上下文工程与Runtime下一步规划.md` 相位 F 段落。

## 缺口与阻塞

- [ ] **样本采集环境**：未确定在哪个环境（dev/staging/prod）采集；若在 prod，需确认是否会影响线上推理。
- [x] **工具链就绪**：✅ 相位 D-1（per-stage token 计量）已于 2026-07-14 完成（见 `TODO/上下文工程与Runtime下一步规划.md`），Runtime 已能输出 `prompt_tokens` / `cached_tokens`。可直接使用 Runtime 输出做 A/B 采集。
  - 备选路径：若直接调用模型 API（如 Anthropic Messages API），可从响应 `usage.cache_read_input_tokens` 提取。
- [ ] **对照组回退成本**：A 组（较重上下文）若已下线，是否需要临时恢复；若需要，估算恢复代价。

## 迁移规则

本文件在任务未执行前保留在 `TODO/`。观测执行完成后：
1. 原始 CSV → `eval/kv_cache_observation/raw/`
2. 汇总与结论 → `eval/kv_cache_observation/`
3. 结论要点回写 → `TODO/上下文工程与Runtime下一步规划.md` 相位 F 段落
4. 本文件更新状态并在顶部保留指向 `eval/kv_cache_observation/` 的链接
