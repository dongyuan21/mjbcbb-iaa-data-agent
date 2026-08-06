# 低置信度 Fallback 与路由监控方案

> 状态：active_plan
> 创建：2026-07-24
> 更新：2026-07-26
> 范围：路由低置信度时的 fallback 通道、`search_catalog` 工具规格、route 命中率监控与长尾治理流程。
> 边界：本文件只定义检索/路由 fallback 策略和监控治理流程，不定义业务口径、不改表卡内容、不涉及投放动作。
> 关联：`TODO/上下文工程与Runtime下一步规划.md` 相位 C/D-2、`知识库三层结构规范.md`、`task_routes/INDEX.yaml`、`runtime/backend/app/services/knowledge.py`。

---

## 一、核心判断：为什么不用 embedding / 不用 agentic grep

### 1.1 本域特征

本 Data Agent 的知识域是**封闭且结构化**的：

- ~150 张表卡（ai_hive ~119 + ai_ck ~30）
- ~60 个策略文件（policies / SOP / report_knowledge）
- ~50 个语义契约指标（semantic_contract/metrics.yaml）
- 18 条 task route 已覆盖生产问题模式的 90%+

对检索系统的核心要求是 **precision（不能召错表、不能用错口径）**，而非 recall（尽可能多召回）。召回错误的表卡会让 LLM 用错 `must_filter` 和 `known_pitfalls`，后果比"没召回"更严重。

### 1.2 为什么不用 embedding

| 维度 | embedding 在本域的问题 |
|---|---|
| 域规模 | 全量 agent_knowledge ≈ 150-200K token，Anthropic 实测 <200K token 时直接全塞 prompt 比 RAG 效果还好 |
| 可审计性 | embedding 召回是黑盒，无法解释"为什么这张表排在第一"；确定性路由每个命中路径明确 |
| chunk 破坏 | 把表卡切成 512 token chunk 后，`query_rules` / `known_pitfalls` / `join_keys` 可能被切到不同 chunk，LLM 看不到完整约束 |
| 维护成本 | 更新表卡后需要重新 embedding 全部 chunk；YAML 修改即生效，git diff 可审计 |
| 门禁 | chunk 内容不可验证；`check_table_card_quality.py` 可以校验每张卡的字段完整性 |
| 行业教训 | Sourcegraph 尝试 embedding 后主动放弃，回归关键词匹配——"adding irrelevant context makes response worse" |

### 1.3 为什么不用 agentic grep（Runtime 自主搜索）

Runtime Framework 标准模式支持 LLM 自主调用 grep/find/read 迭代搜索文件系统。但本工程**已主动禁用**（`--no-builtin-tools`），原因：

| 维度 | agentic grep 在本域的问题 |
|---|---|
| 正确性下限 | 模型可能搜偏、遗漏；确定性路由规则覆盖的问题稳定命中 |
| 延迟 | 多轮 tool call，每次消耗 token |
| 成本 | 每次搜索消耗 LLM token |
| 可审计 | 搜索过程不确定，难以复现和调试 |
| 域匹配 | agentic grep 适合大文件库（10K+ files）的探索性搜索；本域知识量小（~200 files）且结构明确，确定性索引更高效 |

### 1.4 确认的主干路线

```
确定性路由（task_routes + 关键词评分）
  → first_read 精确文件加载
  → 5 通道预编译上下文（带 context_budget）
  → Runtime 只做 SQL 执行（3 个只读工具，零文件系统访问）
```

本方案只补一个能力：**当确定性路由置信度低时，如何 fallback**。

2026-07-26 的实现边界：低置信、跨域组合与长开放题不会仅因 route confidence 进入固定回答；探索模式会继续 Runtime 取证。它仍不开放 Runtime builtin grep/find/read/bash，也不扩大为任意文件搜索；只允许经 exploration registry 的 metadata-first、白名单只读知识工具。默认 mode 仍为 `off`，真实 A/B/Test 灰度前不作为线上质量结论。

---

## 二、长尾问题分析

确定性路由的短板是长尾覆盖。长尾有三类：

| 类型 | 描述 | 例子 | 当前行为 |
|---|---|---|---|
| A. 措辞偏移 | 问题属于已有 route，但触发词没命中 | "这个渠道花了多少钱"（trigger 没有"消耗"） | 可能 match 不到 `roi_or_campaign_analysis` |
| B. 跨 route 组合 | 问题需要同时命中多个 route 的知识 | "BB 美国 DNU 下滑，是素材还是预算改了？" | 需要同时加载 `bb_us_ua` + `material` + `google_ads_config` |
| C. 全新问题 | 18 条 route 都不覆盖的域外问题 | "竞品市场份额""归因窗口实验设计" | 无 route 命中，fallback 到默认行为（可能答偏） |

本方案的核心目标是覆盖 A 和 C，B 标 `deferred`（见第六节）。

---

## 三、Fallback 通道设计

### 3.1 整体流程

```
用户问题
  │
  v
KnowledgeRouter.route()  ── 现有关键词评分
  │
  ├── confidence >= 0.6 ──→ 走确定性 first_read（主干，不变）
  │
  └── confidence < 0.6 ──→ 进入 Fallback 通道（新增）
                               │
                               v
                    Step 1: LLM Route Selection
                    （轻量 LLM 调用，看 INDEX.yaml 18 条路由摘要选 route）
                               │
                               ├── 选中某 route ──→ 走该 route 的 first_read（回到主干）
                               │
                               └── 标 "none_match" ──→ Step 2
                                                          │
                                                          v
                                               search_catalog(query) 工具
                                               （搜 3 个 catalog + semantic_contract）
                                                          │
                                               ├── 有相关命中 ──→ LLM 从 top-5 选加载哪些
                                               │
                                               └── 无命中 ──→ 兜底（诚实告知 + 记录监控）
```

### 3.2 Confidence 阈值判断

现有 `KnowledgeRouter.route()`（`runtime/backend/app/services/knowledge.py`）已返回 `confidence_score`。新增逻辑：

```python
# knowledge.py 新增常量
FALLBACK_CONFIDENCE_THRESHOLD = 0.6  # 初值，待监控数据校准

# 路由后判断
if route_result.confidence >= FALLBACK_CONFIDENCE_THRESHOLD:
    # 主干：走 first_read
    context = build_knowledge_context_parts(route_result, ...)
else:
    # Fallback 通道
    context = build_fallback_context(question, route_result, ...)
```

阈值 0.6 是初始值，上线后根据监控数据（第四节）校准。校准原则：

- 阈值过高 → 太多问题进 fallback，增加延迟和成本
- 阈值过低 → 低质量路由命中混入主干，降低 precision
- 目标：fallback 占比 < 15%，fallback 后回答准确率 > 80%

### 3.3 Step 1: LLM Route Selection

当 confidence < 阈值时，发起一次轻量 LLM 调用：

**输入**（~2K token）：
- 用户原始问题
- `task_routes/INDEX.yaml` 的精简版（每条 route 只给 `id` + `objective` + `trigger_examples`，不给 `first_read` / `allowed_assets` 等重内容）

**Prompt 模板**：

```text
你是任务路由助手。根据用户问题，从以下路由中选择最匹配的一个。
如果没有路由匹配，回答 "none_match"。

路由列表：
{routes_summary}

用户问题：{question}

回答格式：只输出 route_id 或 "none_match"，不要解释。
```

**输出**：1 个 route_id 或 `none_match`

**成本**：~2K input + ~10 output token，单次调用延迟 < 1s。

**安全约束**：
- 只能选 `remote_default_task_ids` 中的 route（线上用户不可见 internal route）
- LLM 不能选 route 之外的路径，只能选或 none_match
- 选中的 route 仍走该 route 的 `first_read` 和 `output_guardrails`，安全边界不变

### 3.4 Step 2: search_catalog(query) 工具规格

当 LLM Route Selection 返回 `none_match` 时，给 Runtime 一个 `search_catalog` 工具。

#### 工具签名

```typescript
// runtime/pi/agent/extensions/readonly_data_query.ts 新增工具
search_catalog(query: string): array<{
  type: "table_card" | "policy" | "metric" | "entity" | "join",
  source: "ai_hive" | "ai_ck" | "knowledge" | "semantic_contract",
  id: string,          // 表名 / 文件名 / 指标名
  summary: string,     // 一行摘要（alias + domain + grain 或 title + status）
  score: number        // 关键词匹配分（0-1）
}>
```

#### 搜索范围与 scope 限制

| 可搜索 | 不可搜索 |
|---|---|
| `ai_hive/agent_knowledge/catalog.yaml` | `ai_hive/audit_archive/` |
| `ai_ck/agent_knowledge/catalog.yaml` | `ai_hive/engineering_artifacts/` |
| `knowledge/agent_knowledge/catalog.yaml` | `raw_exports/` / `da_assets/raw/` |
| `knowledge/agent_knowledge/semantic_contract/*.yaml` | `knowledge/audit_archive/draft_knowledge/` |
| | `TODO/` / `outputs/` / `tmp/` |

#### 搜索算法（关键词，不用 embedding）

```python
# runtime/backend/app/services/catalog_search.py（新增）

def search_catalog(query: str, top_k: int = 5) -> list[dict]:
    """
    在三个 catalog + semantic_contract 中做关键词搜索。
    不用 embedding，用 token overlap + tf-idf 权重评分。
    """
    query_tokens = tokenize(query)  # Latin words + CJK bigrams
    candidates = []

    # 1. 搜 ai_hive catalog（表名、alias、domain、grain）
    for table in load_catalog("ai_hive"):
        searchable = f"{table.fqn} {table.alias} {table.domain} {table.grain}"
        score = token_overlap_score(query_tokens, tokenize(searchable))
        if score > 0:
            candidates.append({
                "type": "table_card", "source": "ai_hive",
                "id": table.fqn, "summary": f"{table.alias} · {table.domain} · {table.grain}",
                "score": score
            })

    # 2. 搜 ai_ck catalog
    for table in load_catalog("ai_ck"):
        # 同上
        ...

    # 3. 搜 knowledge catalog（只搜 active/confirmed 状态的文档）
    for doc in load_catalog("knowledge"):
        if doc.status not in {"active", "confirmed_evidence", "trial_active"}:
            continue
        searchable = f"{doc.id} {doc.title} {doc.tags}"
        score = token_overlap_score(query_tokens, tokenize(searchable))
        if score > 0:
            candidates.append({
                "type": "policy", "source": "knowledge",
                "id": doc.path, "summary": f"{doc.title} · {doc.status}",
                "score": score
            })

    # 4. 搜 semantic_contract（metrics、entities、dimensions、joins）
    for metric in load_semantic_contract("metrics"):
        searchable = f"{metric.name} {' '.join(metric.aliases)} {metric.description}"
        score = token_overlap_score(query_tokens, tokenize(searchable))
        if score > 0:
            candidates.append({
                "type": "metric", "source": "semantic_contract",
                "id": metric.name, "summary": metric.description[:100],
                "score": score
            })

    # 排序，返回 top-k（只返回摘要，不返回全文）
    return sorted(candidates, key=lambda x: x["score"], reverse=True)[:top_k]
```

#### LLM 使用方式

Runtime 收到 `search_catalog` 工具后：

1. 调用 `search_catalog(question)` 获取 top-5 候选摘要
2. 从候选中选择需要加载的表卡/策略（可多次调用）
3. 被选中的文件通过现有 `first_read` 机制加载全文
4. 仍有 context_budget 约束（不超过该 route 的 `context_budget_chars`）

**示例交互**：

```
用户："竞品的市场份额数据怎么看？"

search_catalog("竞品 市场份额 下载量")
→ []  （无命中）

Runtime 回答：
"抱歉，当前知识库没有覆盖竞品市场份额数据。
我现有的数据范围是自有产品的投放 ROI、DNU、变现和点位分析。
如果您需要竞品情报，可能需要接入第三方数据源（如 Sensor Tower / data.ai）。"
```

### 3.5 兜底行为

当 `search_catalog` 也无命中时：

1. **诚实告知**：不编造，说明当前知识库不覆盖该问题域
2. **给边界提示**：说明 Agent 当前能覆盖的域（投放 ROI、DNU、变现、点位、素材、实验）
3. **记录监控**：写入 `agent_route_hits` 表，标 `fallback_outcome=none_match`，供周期性治理回收

---

## 四、Route 命中率监控

### 4.1 数据模型

```python
# runtime/backend/app/services/monitoring.py（新增/扩展）

@dataclass
class RouteHitRecord:
    timestamp: str           # ISO 时间戳
    question_hash: str       # 问题脱敏 hash（不存原文）
    question_tokens: str     # 问题关键词（用于聚类，不含 PII）
    matched_route: str       # KnowledgeRouter 原始命中的 route_id
    confidence: float        # 路由器评分 (0-1)
    fallback_used: bool      # 是否进入 fallback 通道
    fallback_step: str       # "none" | "llm_selection" | "search_catalog" | "none_match"
    llm_rerouted_to: str     # LLM 选路结果（若进入 fallback）
    final_route: str         # 最终使用的 route_id
    search_catalog_hits: int # search_catalog 返回的候选数（若调用）
    user_feedback: str       # "satisfied" | "unsatisfied" | "none"（若有反馈机制）
    response_latency_ms: int # 总响应延迟
```

### 4.2 存储

MySQL 表 `agent_route_hits`（公司实例，与现有 trace 表同库）：

```sql
CREATE TABLE agent_route_hits (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    question_hash VARCHAR(64) NOT NULL,
    question_tokens VARCHAR(500),
    matched_route VARCHAR(100),
    confidence FLOAT,
    fallback_used BOOLEAN DEFAULT FALSE,
    fallback_step VARCHAR(50) DEFAULT 'none',
    llm_rerouted_to VARCHAR(100),
    final_route VARCHAR(100),
    search_catalog_hits INT DEFAULT 0,
    user_feedback VARCHAR(20) DEFAULT 'none',
    response_latency_ms INT,
    INDEX idx_confidence (confidence),
    INDEX idx_timestamp (timestamp),
    INDEX idx_fallback (fallback_used, fallback_step)
);
```

### 4.3 周聚合报表

每周一自动生成（cron 或手动触发）：

```python
# tools/scripts/route_hit_weekly_report.py（新增）

def generate_weekly_report():
    """
    聚合过去 7 天的 route_hits，输出：
    1. confidence 分布直方图
    2. fallback 占比与 fallback_step 分布
    3. 低分 case 聚类（相似问题模式识别）
    4. route 候选建议
    """
    # 1. 总览
    total = count_all(last_7_days)
    low_confidence = count(confidence < 0.6)
    fallback_rate = low_confidence / total

    # 2. 低分 case 聚类
    low_conf_cases = query(confidence < 0.6, last_7_days)
    clusters = cluster_by_token_similarity(low_conf_cases.question_tokens)
    # 简单 token overlap 聚类：Jaccard > 0.3 归为同簇

    # 3. 输出候选
    for cluster in clusters:
        if cluster.size >= 3:  # 出现 3 次以上的模式
            print(f"[候选] 出现 {cluster.size} 次的相似问题模式：")
            print(f"  代表问题 tokens: {cluster.representative_tokens}")
            print(f"  建议: {suggest_action(cluster)}")
            # suggest_action:
            #   - 如果某 route 的 trigger 能覆盖 → "加 trigger_example 到 {route_id}"
            #   - 如果没有 route 覆盖 → "考虑新建 route"
            #   - 如果属于域外 → "标记 out-of-scope"
```

### 4.4 健康指标

| 指标 | 目标 | 告警阈值 |
|---|---|---|
| fallback 占比 | < 15% | > 25% |
| fallback 后 none_match 占比 | < 5% | > 10% |
| fallback 后回答准确率 | > 80% | < 70% |
| 同一低分模式出现次数 | < 3 次/周 | >= 5 次/周（需加 route） |

### 4.5 治理流程

```
每周回收流程：
  1. 生成周报（route_hit_weekly_report.py）
  2. 人工 review 低分 cluster：
     a. cluster 能被现有 route 覆盖
        → 加 trigger_example 到该 route 的 INDEX.yaml 条目
        → 跑 check_agent_retrieval_map.py 验证
     b. cluster 属于新问题模式
        → 新建 task_routes/<id>.yaml
        → 更新 INDEX.yaml
        → 跑 check_agent_retrieval_map.py + agent regression
     c. cluster 属于域外
        → 标记 out-of-scope（记入 report，不做 route）
  3. 更新 confidence 阈值（如有必要）
```

---

## 五、实现优先级与工作量

| 序号 | 事项 | 工作量 | 价值 | 依赖 | 建议时间 |
|---|---|---|---|---|---|
| 1 | `knowledge.py` 加 confidence 阈值判断 + RouteHitRecord 日志 | 0.5 天 | 有数据才能治理 | 无 | 第 1 周 |
| 2 | MySQL `agent_route_hits` 建表 + 写入逻辑 | 0.5 天 | 监控基础 | #1 | 第 1 周 |
| 3 | 实现 `search_catalog()` 工具（`catalog_search.py`） | 1 天 | fallback 核心能力 | 无 | 第 1 周 |
| 4 | Fallback 通道串联（LLM route selection + search_catalog 注入 Runtime） | 1-2 天 | 补长尾 | #1 #3 | 第 2 周 |
| 5 | `route_hit_weekly_report.py` 周报脚本 | 1 天 | 持续迭代基础 | #2 | 第 2 周 |
| 6 | 线上灰度 + 监控数据收集 | 持续 | 校准阈值 | #1-5 | 第 3-4 周 |
| 7 | 跨 route composition（第六节） | 视监控数据 | 可能不需要 | #6 有数据 | 2-4 周后评估 |

---

## 六、跨 Route 组合问题（deferred）

类型 B 长尾（一个问题需要多个 route 的知识）暂不实现。思路记录如下，等监控数据积累 2-4 周后评估是否频繁出现：

```yaml
# task_routes/INDEX.yaml 未来可能新增：
composition_rules:
  - pattern: "DNU 下滑 + 素材/预算/操作原因"
    primary_route: roi_or_campaign_analysis
    secondary_read_from:
      - material_analysis.first_read[0:3]
      - google_ads_config_change_analysis.first_read[0:2]
    budget_split: [60%, 20%, 20%]
```

**判断标准**：如果监控数据显示 >10% 的问题命中了 primary route 但 LLM 在回答中需要搜索其他 route 的表卡，则实现 composition_rules。否则不做。

---

## 七、前置依赖与验收标准

### 7.1 前置依赖

- ✅ `KnowledgeRouter.route()` 已返回 `confidence_score`
- ✅ Runtime Tool Registry 已有受控工具注入机制
- ✅ 3 个 catalog.yaml 和 semantic_contract YAML 已结构化，可直接被 Python 读取
- ⬜ MySQL `agent_route_hits` 表（实施时建）

### 7.2 验收标准

| 验收项 | 标准 |
|---|---|
| 主干不变 | confidence >= 0.6 的问题走原流程，agent regression 17/17 保持全绿 |
| Fallback 正确性 | 低置信度问题进入 fallback 后，LLM route selection 准确率 > 80%（人工抽检 20 case） |
| search_catalog 有效性 | 返回的 top-5 候选中，人工判断相关表卡出现在 top-3 的比例 > 70% |
| 监控完整性 | `agent_route_hits` 表每条问答有记录，字段无缺失 |
| 安全边界 | fallback 通道不可访问 `never_default_recall` 目录；不可选 `internal_codex_task_ids` route |
| 性能 | fallback 通道增加延迟 < 3s（LLM route selection + search_catalog） |

### 7.3 执行约束

- 改 `task_routes/INDEX.yaml` → 跑 `check_agent_retrieval_map.py`
- 改 `knowledge.py` → 跑 backend 测试 + agent regression
- 改 Runtime extension → 端到端问答验证 + token 分段报告
- 新增 route → 跑 `check_agent_retrieval_map.py` + agent regression
