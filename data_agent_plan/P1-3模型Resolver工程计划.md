# P1-3 模型 Resolver 工程计划

> 状态：`draft_pending_review`
> 创建日期：2026-07-18
> 分支：待开（从 main 切）
> 关联设计：`data_agent_plan/多轮对话与上下文压缩工程设计.md` §P1-2/P1-3
> 关联 TODO：`TODO/多轮对话建设.md` 第五节 P1-2/P1-3
> 关联精度报告：`eval/multi_turn/resolver_precision_report.md`

## 一、背景

当前 TurnResolver 是**纯规则版**（正则匹配固定模式）。精度报告（47 turns golden）显示：

| turn_kind | precision | recall | F1 |
|---|---:|---:|---:|
| correction | 1.000 | 0.875 | 0.933 |
| follow_up | 1.000 | 0.697 | 0.821 |
| standalone | **0.312** | 1.000 | 0.476 |
| topic_switch | 1.000 | 1.000 | 1.000 |

核心问题：**standalone precision 0.312**——11 个 follow_up 被误判成 standalone。这些都是自然语言追问，规则层匹配不到：

- `哪个媒体 ROI 最低`
- `具体数字是多少`
- `和美国整体比`
- `最终结论是什么`
- `那另一个呢`

规则层已到天花板。需要引入 LLM 模型 resolver 理解自然语言，判断 turn_kind + 提取 state_patch。

## 二、目标

1. LLM 模型 resolver 作为**规则层的补充**，只在规则层判 standalone 时兜底（规则层已覆盖的不重复判断）。
2. 模型 resolver 输出结构化 `TurnResolution`（turn_kind / confidence / state_patch / inherited_fields），和规则版同一 schema。
3. **先 shadow**：只写 metadata，不改 route。精度达标后再 enforce。
4. 有 schema 校验、超时 fallback、kill switch。
5. 不保存用户问题、答案、SQL 到模型 trace（metadata-only 隐私投影）。

## 三、非目标

- 不替换规则层（规则层高精度部分继续用）。
- 不引入 LangGraph / AutoGen 等框架。
- 不做 cross-session 记忆。
- 不改 Runtime 的 `--no-session`。

## 四、设计

### 4.1 调用时机

```text
resolve_turn(message, has_prior_state, ...)
  → 规则层先判（现有逻辑）
  → 如果规则层判 standalone 且 has_prior_state=True：
      → 调模型 resolver 兜底
      → 模型输出 confidence >= 0.70 → 采纳
      → 模型输出 confidence < 070 或超时/失败 → 保持 standalone
  → 规则层判非 standalone → 直接返回（不调模型）
```

只在"规则判 standalone + 有历史"时调模型，最小化 LLM 调用量。

### 4.2 模型 resolver 输入

```json
{
  "current_question": "哪个媒体 ROI 最低",
  "has_prior_state": true,
  "prior_topic": "roi360_analysis",
  "prior_slots": {
    "product": "BB",
    "platform": ["gp", "ios"],
    "metric": "roi360",
    "metric_mode": "forecast"
  }
}
```

不传完整历史文本（省 token + 隐私）。只传 slot 摘要让模型判断是否有指代。

### 4.3 模型 resolver 输出（JSON schema 校验）

```json
{
  "turn_kind": "follow_up",
  "confidence": 0.85,
  "reason_codes": ["model_natural_followup"],
  "state_patch": {},
  "inherited_fields": ["*"]
}
```

约束：
- `turn_kind` 必须是枚举值之一（standalone / follow_up / correction / topic_switch）
- `confidence` 0.0-1.0
- `state_patch` 只能含已知 slot key（`entities.*` / `metrics.*` / `time.*` / `constraints.*`）
- 非 JSON 或 schema 校验失败 → fallback 到规则层结果（standalone）

### 4.4 超时与 fallback

- 模型调用超时：3 秒（用现有 Runtime provider 的轻量模型，不是主分析模型）
- 超时/失败 → 保持规则层 standalone 判定，不阻塞用户
- 记录 `reason_codes: ["model_timeout"]` 或 `["model_schema_error"]`

### 4.5 shadow → enforce 分层

| 阶段 | 行为 | 开关 |
|---|---|---|
| shadow | 模型 resolver 结果只写 metadata，不改 route | `MODEL_RESOLVER_SHADOW=true, ENFORCE=false` |
| enforce-1 | confidence >= 0.90 的 follow_up/correction 才 enforce | `MODEL_RESOLVER_ENFORCE=true, THRESHOLD=0.90` |
| enforce-2 | confidence >= 0.70 的都 enforce | `THRESHOLD=0.70` |
| kill | 一键回退到纯规则 | `MODEL_RESOLVER_ENABLED=false` |

## 五、改动点

| 文件 | 改动 | 风险 |
|---|---|---|
| `turn_resolver.py` | 新增 `_resolve_with_model()` 函数，在 `resolve_turn()` 末尾规则判 standalone 时调用 | 中：影响多轮 route |
| `turn_resolver.py` | 新增 `MODEL_RESOLVER_ENABLED / SHADOW / THRESHOLD` 配置 | 低 |
| `config.py` | 新增模型 resolver 配置项（model name / timeout / threshold） | 低 |
| `agent.py` | 无需改（`resolve_turn` 接口不变） | 无 |
| `eval/multi_turn/run_resolver_precision.py` | 加模型 resolver 精度对比（规则 vs 模型 vs 混合） | 低 |
| `eval/multi_turn/conversations.yaml` | 补自然追问 golden（当前 11 个误判的） | 低 |
| `tests/test_turn_resolver.py` | 加模型 resolver mock 测试 | 低 |

## 六、分步实施（TDD）

### Step 1：模型 resolver 函数 + schema 校验
- [ ] 新增 `_resolve_with_model(question, prior_slots) -> TurnResolution | None`
- [ ] 输入构造：从 ConversationState 提取 slot 摘要
- [ ] 输出 schema 校验：turn_kind 枚举、confidence 范围、slot key 白名单
- [ ] 超时 3s + fallback None
- [ ] 单测：mock 模型返回，验证 schema 通过/失败/超时
- [ ] 退出标准：单测全绿，不改 `resolve_turn()` 主逻辑

### Step 2：接入 resolve_turn（shadow）
- [ ] `resolve_turn()` 末尾：规则判 standalone + has_prior_state → 调 `_resolve_with_model()`
- [ ] shadow 模式：模型结果只写 `resolution.reason_codes`，不改 `turn_kind`
- [ ] 加配置开关 `MODEL_RESOLVER_SHADOW`
- [ ] 单测：shadow 模式下 turn_kind 不变，reason_codes 有 model 标记
- [ ] 退出标准：单测全绿，现有行为零回归

### Step 3：精度对比报告
- [ ] `run_resolver_precision.py` 加 `--mode rule/model/hybrid` 对比
- [ ] 跑 47 turns golden，对比三组 precision/recall
- [ ] 重点看 11 个 standalone 误判是否被模型纠正
- [ ] 退出标准：hybrid 模式 standalone precision > 0.70

### Step 4：enforce-1（高置信度）
- [ ] `MODEL_RESOLVER_ENFORCE=true, THRESHOLD=0.90`
- [ ] 模型判 follow_up/correction 且 confidence >= 0.90 → 采纳，改 turn_kind
- [ ] 单测 + 集成测试
- [ ] 退出标准：精度报告 hybrid F1 > 规则版，无 standalone→follow_up 误判（precision 不降）

### Step 5：自然追问 golden 补充
- [ ] `conversations.yaml` 补 5-10 个自然追问 golden（来自线上真实样本）
- [ ] 跑多轮回归确认 PASS
- [ ] 退出标准：新增 golden 全 PASS

### Step 6：线上 shadow 验证
- [ ] 部署到 test，shadow 模式跑一周
- [ ] 收集 model resolver 的 reason_codes 分布
- [ ] 人工复核 shadow 结果 vs 实际行为
- [ ] 退出标准：shadow 精度达到 enforce-1 标准

## 七、风险与回退

| 风险 | 缓解 |
|---|---|
| 模型 resolver 增加延迟（3s） | 只在规则判 standalone 时调；超时 fallback |
| 模型幻觉 turn_kind | schema 校验 + confidence 阈值 + shadow 先验证 |
| 模型调用量大 | 只在 standalone + has_prior_state 时调，大部分轮次不触发 |
| 回退 | `MODEL_RESOLVER_ENABLED=false` 一键回到纯规则 |

## 八、完成定义

1. 模型 resolver 函数实现 + schema 校验 + 超时 fallback。
2. hybrid 模式 standalone precision > 0.70（当前 0.312）。
3. shadow 模式零回归（现有行为不变）。
4. enforce-1 模式 F1 优于纯规则。
5. kill switch 可一键回退。
6. backend 全量 + 多轮回归无新增 hard failure。
7. 线上 shadow 验证一周，精度达标。

## 九、建议时机

- **现在可以做**：Step 1-3 是纯本地开发 + 测试，不需要线上环境。
- Step 4-6 需要部署验证，建议和 compaction 一起部署。
