# TODO · 上下文工程与 Runtime 下一步规划

> 状态：planning（规划，非当前事实；按相位推进，每步先出设计再实施）
> 来源：2026-06-20 控制面治理 + bootstrap 瘦身 + 只读 runtime POC 之后的延续。
> 关联：`DataAgent只读Runtime_POC.md`、`../data_agent_plan/知识库三层结构规范.md`、`../showoff/Agent知识按需加载与上下文预算.md`。
> 度量基线（真实 tiktoken o200k，2026-06-20）：default_bootstrap ~14.4K；每轮强制规则 ~6K；SQL 类问答累计 ~55–65K；表卡层全量 ~302K（永不整包）。

## 总原则

上下文工程不是为了"防溢出"（200K 窗口远没到顶），而是省钱、降延迟、避免 lost-in-the-middle、给推理留余量。压缩有地板：硬安全规则（PII / 不输出密钥 / freshness / 不自动动作）+ 路由入口 INDEX + 召回边界 ≈ 3–4K 不可再砍。压多狠取决于消费者：交互式 Cursor agent 不宜过激（更多 on-demand 读 = 更多 round-trip）；自研 runtime 可极简（精确控制每次喂什么）。

## 相位 A：每轮强制项压到底（乘轮数，最值钱）

| 项 | 现状 | 动作 | 预计省 |
|---|---|---|---|
| 父 `点位/AGENTS.md` | 已断掉(globs frontmatter) | 验证 Cursor Settings→Rules 不再生效;必要时迁 `点位/.cursor/rules/*.mdc` | ~3–4K/轮 |
| `数仓/AGENTS.md` 的"业务SQL"枚举段 | ~15 条 policy 枚举常驻 | 移到 `task_routes/text2sql_or_sql_planning.yaml`(已含这些 policy);AGENTS 只留硬规则+技能入口 | ~1.3K/轮 |

验收：每轮强制规则 6K → ~1.3K；改 AGENTS 后跑 `check_knowledge_consistency.py`(AGENTS 在 stale-scan 内)。

## 相位 B：每会话 bootstrap 重排（default_bootstrap 14.4K → ~3–4K）

| 项 | 现状 | 动作 | 预计省 |
|---|---|---|---|
| README | 3.8K | 拆出精简 agent-bootstrap(~1K,路由入口+硬边界);人读 README 移出 default_bootstrap | ~2.8K |
| AGENT_RETRIEVAL_MAP | 2.5K | `canonical_owners`/`promotion_paths` 属治理参考,移到治理任务 first_read;bootstrap 只留路由必需 | ~1.5K |
| 3 个 `agent_manifest.yaml` | 3K | 移到按表/SQL 任务的 first_read,不进 always-on | ~3K |
| `TODO/README` | 0.6K | 移出 bootstrap,归 backlog 任务 first_read | 0.6K |
| 默认召回边界 1.3K + INDEX 0.8K | 2.1K | 保留(核心) | — |

依赖：相位 B 改 default_bootstrap 后必须跑 `check_agent_retrieval_map.py` + agent regression（路由用例从 task_routes 加载，需保持 6/6）。
权衡：bootstrap 越瘦，agent on-demand 读越多；交互式 agent 建议保守，runtime 可激进。

## 相位 C：Stage2 单体索引可检索化（剩余最大上下文收益）

SQL 类问答的大头是三个被整包加载的索引；目标改为"按问题切片/检索",单题只取相关片段。

| 索引 | 现状 token | 方案(先出设计) |
|---|---|---|
| `semantic_contract/model.json` | ~19.3K | 按问题涉及的 entity/metric/join 切片(语义子模型检索);定切片粒度与检索方式 |
| `da_assets/index.yaml` | ~12.4K | 建轻量检索(tag/向量)命中 verified SQL,不整包;与 runtime `retriever.py` 对接 |
| `ai_hive/ai_ck catalog.yaml` | ~10.9K / 4.5K | 选表改 关键词/embedding 检索,不整包扫 |

预计：SQL 问答 ~60K → ~25–30K。
依赖：与 runtime `retriever.py`、`router.py` 对接;需先定检索方式(关键词 vs embedding)。本相位之前先不动（用户已指示）。

## 相位 D：Runtime 延续（tools/data_agent_poc）

- `recognizer` 从关键词升级为 embedding 相似度(仍离线),提升意图识别鲁棒性;保留可插拔接口。
- 加 per-stage token 计量:每个问答打印 bootstrap/任务/索引/卡片各阶段 token,使上下文预算可观测、可设预算上限、可回归。
- SQL 规划路径:缺口场景按 `Text2SQL字段证据模板.md` 生成 candidate SQL,经 `SQL晋升治理.md` 门禁才升 verified。
- 落地形态/IO 契约已定(库优先 + 固定 output_contract);如需常驻服务，再在库外包一层。

## 相位 E：数据 / 质量（并行）

- freshness：当前 2 个 CK 表延迟(tj_ad_sdk_revenue 等);建"分析前刷快照"固定动作(`probe_freshness.py`),区分数据延迟与真实劣化。
- 表卡 5 个 `known_pitfalls` 待人确认 → 闭环。
- 北极星覆盖 ~46% → 继续沉淀 verified SQL / 语义指标。
- 待人拍板项(organic 是否计 KPI、回收口径、红线阈值)→ 解阻后升 confirmed。

## 推进顺序建议

1. 相位 A（每轮强制，已做一半：父级已断；剩 AGENTS 精简）。
2. 相位 D 的 token 计量（让后续压缩可量化验证）。
3. 相位 B（bootstrap 重排）。
4. 相位 C（索引可检索化，最大收益，但工程量最大，需先定检索方式）。
5. 相位 E 并行。

每一步遵循：先出设计/权衡 → 人拍板 → 实施 → 跑门禁+回归 → 度量 token 变化。
