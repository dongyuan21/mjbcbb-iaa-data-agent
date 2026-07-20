# Data Agent Runtime 架构规划

> 状态：historical_plan_with_20260715_implementation_overlay
> 创建：2026-06-20
> 更新：2026-06-20
> 上下文：基于数仓知识库工程现状 + 公司基建（山海 K8s / SSO / MySQL / OSS / LiteLLM 网关）的综合规划

## 2026-07-15 实现态覆盖说明

中心化 Web、MySQL 持久化、Redis 任务队列/唤醒、PI Worker、durable SSE `after_seq` 续传和 test live N=3 已完成。行为提交 `54df4d8f` 的最终 14 条 live case × N=3 为 39 PASS、3 个预期黄色 WARN、0 fail、0 blocked、0 flaky，114 条 query records 全部成功。2026-07-15 已补齐浏览器刷新/断线后续接同一 job 的实现和离线自动化门禁；真实浏览器手工刷新报告仍与实现证据分开记录。原“工程现状”和 Phase 表保留为历史规划，不能继续当作当前完成度；OSS、钉钉通知、Langfuse与真实多人内测仍按各自证据单列。

当前事件历史以 MySQL durable job events 为唯一权威，Redis 只负责排队和唤醒；客户端按最后连续序号续接同一 job，不重复创建任务，永久缺口仍 fail-closed。

## 已确认决策

| 决策项 | 结论 | 确认时间 |
|---|---|---|
| 部署形态 | 中心化 Web 服务（山海 K8s） | 2026-06-20 |
| Agent 框架 | **PI Framework + 自定义数据工具/护栏层** | 2026-06-21 |
| 后端语言 | Python（FastAPI） | 2026-06-20 |
| 持久化 | MySQL（公司实例），**不用 SQLite** | 2026-06-20 |
| 可观测 | Langfuse **独立部署**（非 sidecar） | 2026-06-20 |

---

## 一、工程现状评估

### 已完成

| 维度 | 状态 | 数据 |
|---|---|---|
| 表卡规模 | 成熟 | ai_hive 119 张 + ai_ck 20 张，硬错误 0 |
| 语义模型 | 可用 | 11 实体 / 38 维度 / 50 指标 / 3 join 规则 |
| verified SQL | 可用 | 27 条 |
| 回归体系 | 成熟 | 10/10 通过，7 层门禁串联 |
| 控制面 | 就绪 | AGENT_RETRIEVAL_MAP + 9 类 task_routes |
| 工具链 | 成熟 | 33 脚本 + 8 runbook |
| 分析沉淀 | 活跃 | 15 SOP + 8 decision case |

### 未完成

- Runtime 本体：Phase 0 脚手架已完成（FastAPI + React + PI RPC + MySQL + MC/CK executor）
- E2E 评测：现有回归只验证资产齐备性
- 北极星场景：46%（16/35）
- 业务阈值：ROI 红线等 P0 决策待 owner 拍板

### 成熟度雷达

```
知识基座：   ████████░░  80%
控制面/路由：█████████░  90%
工具/门禁：  ████████░░  80%
部署/分发：  ███░░░░░░░  30%
Runtime：   ████░░░░░░  40%
业务闭环：  ███░░░░░░░  30%
```

---

## 二、部署方向：中心化 Web 服务

### 为什么选 Web 服务而非 Mac 客户端

- 团队共享，无需每人配 MC/CK 凭据
- 更新即时生效
- 可做权限控制和审计
- 复用公司 K8s + SSO + MySQL + OSS 基建

### 公司基建对齐

| 基建 | Data Agent 用法 | 参考 |
|---|---|---|
| 山海 DeployerV2 | 构建 Docker → ACR → K8s 部署 | sibling-platform |
| SSO | 用户认证，ticket 换 session | sibling-platform `sso.go` |
| MySQL | session / 报告元数据 / 查询记录 | sibling-platform GORM |
| OSS (PVS) | markdown 报告 / 查询结果文件 | sibling-platform HtmlReport |
| LiteLLM 网关 | LLM 推理（OpenAI 兼容 SDK） | sibling-video-agent `gateway.py` |
| 钉钉通知 | 长查询完成 / 异常通知 | sibling-video-agent `dingtalk.py` |

---

## 三、Agent 框架选型

### 候选对比（已完成评估）

| 框架 | 适配度 | 理由 |
|---|---|---|
| **PI Framework** | 高 | earendil-works/pi；TypeScript/Node Agent loop、RPC/SDK、事件流、工具执行过程输出；适合作为 Runtime 的主 Agent 框架 |
| LangGraph | 中偏高 | 成熟状态机编排；当前先用 PI 的 agent loop 与 RPC 事件流 |
| OpenCode | 不适合 | 编码 Agent（172K stars），用于写代码/调试，不是构建业务 Agent 产品的框架 |
| 完全自研 | 中 | 贴合但造轮子成本高 |

### 已确认：PI Framework + FastAPI RPC Bridge

```
用户问题
 → FastAPI Web 层（SSE + Session + MySQL）
   → 自定义路由层（KnowledgeRouter → task_routes + AGENT_RETRIEVAL_MAP）
   → 知识内容注入（verified SQL 内容 + 表卡摘要 + 策略协议 → PI prompt）
   → PI RPC Agent（agent loop + tool execution events）
     → bash 工具 → runtime/tools/data_query.py（独立脚本，不回调 FastAPI）
       ├── MC 执行器（helper subprocess）
       └── CK 执行器（helper subprocess / clickhouse-driver 直连）
   → read-only 门禁（工具脚本层 + executor 层双重校验）
 → SSE 流式输出（含 heartbeat + event ID + 断线重连）
```

路由层自己写：已有完整的 AGENT_RETRIEVAL_MAP.yaml 和 9 类 task_routes/，比任何框架的 Router 都贴合业务。

Agent 核心用 PI：agent loop、RPC/SDK、TUI/事件流、工具执行过程输出。FastAPI 负责 Web API、MySQL、SSE、知识注入和公司基建 bridge。PI 通过 bash 调用独立工具脚本（`runtime/tools/data_query.py`）查询数据，不回调 FastAPI，避免循环 HTTP。

### LLM 接入

复用公司 LiteLLM 网关（同 sibling-video-agent）：

```python
from openai import OpenAI
client = OpenAI(
    base_url="https://stargate.example.com/v1",
    api_key=os.environ["LLM_GATEWAY_API_KEY"],
)
```

PI 通过 `models.json` / provider 配置接入 OpenAI 兼容网关；本地 Runtime 通过 `pi --mode rpc --no-session` 的 JSONL RPC 调用 PI。

### 未来迁移路径

```
现在：FastAPI Bridge + PI RPC subprocess（每请求 spawn）
  ↓ Phase 1：PI 长驻进程（复用同一进程处理多请求，消除冷启动）
  ↓ 需要更深定制工具/模型/上下文时
未来：PI SDK 嵌入 Node service 或 PI extensions/skills/MCP 包
```

---

## 四、Web 架构

### 技术栈

| 层级 | 选型 | 理由 |
|---|---|---|
| 前端 | React + Vite | 轻量启动，Phase 0 单文件 SPA |
| 前后端通信 | SSE（Server-Sent Events） | HTTP 兼容，单向推送够用 |
| 后端框架 | FastAPI（Python） | 原生 async + SSE + Pydantic 数据模型；通过 RPC 调用 PI |
| ORM | SQLAlchemy 2.0 + Alembic | Python 生态标准（参考 sibling-video-agent） |
| 异步任务 | asyncio task（POC）/ Celery（生产） | MC 长查询异步执行 |
| 部署 | Docker 一镜两用（API + Worker） | 同 sibling-video-agent 模式 |

### 关于后端语言选择

sibling-platform 用 Go，sibling-video-agent 用 Python。Data Agent Web/API 层推荐 **Python**，Agent 框架使用 **PI(TypeScript/Node)**：
- 知识库工具链全是 Python（33 个脚本）
- MC/CK helper 当前是 Python（PyODPS / clickhouse-driver）
- PI 是 TypeScript/Node Agent 框架，通过 RPC 与 Python Web 层集成
- sibling-video-agent 已验证 Python + FastAPI + 山海 K8s 可行

### 连接稳定性方案

**SSE 断线重连**（当前实现态）
- 服务端每 15s 发送 heartbeat 注释行保持连接
- durable job 的每个 SSE `id:` 等于 MySQL event `seq`；`Last-Event-ID` 在未显式传 `after_seq` 时可作为续传游标
- 服务端仍发送 `retry: 5000` 标准提示；React `fetch` reader 由自身状态机按固定退避重连，不依赖浏览器原生 `EventSource`
- `GET /api/jobs/{job_id}/events?after_seq=` 从 MySQL durable event log 断点续传；Redis 通知不直接作为历史事件转发
- 浏览器以 tab 级 `sessionStorage` 保存 `job_id`、最后连续 `seq` 和绝对 deadline；刷新只观察同一 job，不重复 POST，也不重置 deadline
- 首次 POST 结果不明时只用同一个 `external_message_id` 幂等重试；得到 `job_id` 后立即从 checkpoint 移除问题正文

**MC 长查询处理**
- 用户提交 → 后端返回 query_id → 异步执行 MC SQL
- SSE 推送进度：submitted → running → fetching → done
- 断线恢复：结果存 MySQL，重连后用 session_id 取回

**会话恢复**
- session_id 存前端 localStorage
- 刷新页面 → 从 MySQL 恢复对话历史和查询结果
- 若该 tab 仍有 active job checkpoint，则恢复历史后从最后连续 `seq` 继续观察；显式“停止接收”会清除自动续接标记，后台 job 不被误报为已取消

---

## 五、Q\&A：Markdown 分析报告怎么实现？用户需要什么权限？

### 5.1 报告生成链路

Data Agent 的核心输出之一是 markdown 分析报告。完整链路：

```
用户提问（自然语言）
  → Agent 任务路由 + 知识检索
  → SQL 匹配（verified SQL 优先）或 Text2SQL 生成
  → MC/CK 执行 SQL，拿到结构化数据
  → LLM 生成 markdown 报告：
    - 数据表格（markdown table）
    - 关键结论 + 同环比
    - 数据来源标注（表名、SQL、时间窗口）
    - 置信度和局限性说明
  → 报告正文存 OSS（PVS 挂载目录）
  → 报告元数据写 MySQL（reports 表）
  → API 返回报告内容 + 下载链接
```

### 5.2 存储方案（MySQL + OSS，不用 SQLite）

**为什么不用 SQLite**：K8s Pod 重启会丢失本地文件系统，SQLite 数据库文件无法持久化（除非挂 PVC，但这本身就不如直接用 MySQL）。公司已有 MySQL 实例，直接复用。

| 数据 | 存储位置 | 理由 |
|---|---|---|
| 报告元数据（标题、作者、时间、格式） | **MySQL** `reports` 表 | 结构化查询、列表筛选 |
| 报告正文（markdown 文件） | **OSS** `/data/reports/{user_id}/{date}/{report_id}/report.md` | 文件体积大、支持 CDN 加速 |
| 查询结果数据（CSV/JSON） | **OSS** 同目录下 `data/` 子目录 | 报告内引用，支持独立下载 |
| 图表（如有） | **OSS** 同目录下 `charts/` | 前端渲染或后端生成 |

### 5.3 渲染与导出

| 场景 | 方案 |
|---|---|
| 浏览器预览 | 前端 `markdown-it` 或 `v-md-preview` 实时渲染 |
| 导出 HTML | 后端 `markdown → html`（`markdown-it` Python 版 或 `mistune`） |
| 导出 PDF | `weasyprint`（纯 Python，Docker 友好）或 `puppeteer` |
| 复制到钉钉/飞书 | 表格数据支持纯文本格式复制 |
| 分享给同事 | 生成带 HMAC 签名的短链，有效期可配 |

### 5.4 用户权限模型

用户**不需要自己配置任何数据库凭据**。权限分三层：

| 权限层 | 要求 | 说明 |
|---|---|---|
| **登录** | 公司 SSO（钉钉扫码） | 同 sibling-platform，无额外注册 |
| **查数** | SSO 登录即可 | Agent 后端用统一的 MC/CK **只读 service account** 执行 SQL，用户不接触 AK/SK |
| **报告访问** | session owner 隔离 | 只能看到自己创建的报告；分享需生成短链 |

如果未来需要更细粒度权限（如限制某些表的访问），在门禁层的 PII gate 中扩展即可。

---

## 六、Q\&A：不同 Session 怎么隔离？是否成熟？

### 6.1 结论：成熟模式，无技术风险

Session 隔离是 Web 应用的标准能力，sibling-platform 和 sibling-video-agent 都已在生产验证。Data Agent 的 session 隔离比它们更简单——只需要对话历史 + 查询结果的隔离，不涉及复杂的资源竞争。

### 6.2 隔离机制

```
用户 A（SSO workcode: zhangsan）
  ├── Session 1: "BB 美国 DNU 分析"
  │   ├── messages: 用户问题 + Agent 回复
  │   ├── query_records: 执行的 SQL + 结果路径
  │   └── reports: 生成的报告
  └── Session 2: "ROI 周报数据"
      ├── messages: ...
      └── ...

用户 B（SSO workcode: lisi）
  └── Session 3: ...（完全独立，互不可见）
```

### 6.3 数据模型（全部用 MySQL，不用 SQLite）

```sql
CREATE TABLE sessions (
    id          VARCHAR(36) PRIMARY KEY,
    user_id     VARCHAR(64) NOT NULL,   -- SSO workcode
    title       VARCHAR(256),           -- 自动生成或用户改名
    status      ENUM('active', 'archived') DEFAULT 'active',
    created_at  DATETIME NOT NULL,
    updated_at  DATETIME NOT NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_updated_at (updated_at)
);

CREATE TABLE messages (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id  VARCHAR(36) NOT NULL,
    role        ENUM('user', 'assistant', 'system') NOT NULL,
    content     LONGTEXT NOT NULL,
    metadata    JSON,                   -- trace_id, tool_calls, sql_executed, tokens_used
    created_at  DATETIME NOT NULL,
    INDEX idx_session_id (session_id),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE query_records (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id  VARCHAR(36) NOT NULL,
    message_id  BIGINT,
    engine      ENUM('maxcompute', 'clickhouse') NOT NULL,
    sql_text    LONGTEXT NOT NULL,
    status      ENUM('submitted', 'running', 'succeeded', 'failed', 'canceled') NOT NULL,
    row_count   INT,
    duration_ms INT,
    error_msg   TEXT,                   -- 失败时的错误信息
    result_path VARCHAR(512),           -- OSS 路径
    created_at  DATETIME NOT NULL,
    updated_at  DATETIME NOT NULL,
    INDEX idx_session_id (session_id),
    INDEX idx_status (status)
);

CREATE TABLE reports (
    id           VARCHAR(36) PRIMARY KEY,
    session_id   VARCHAR(36),
    user_id      VARCHAR(64) NOT NULL,
    title        VARCHAR(256) NOT NULL,
    format       ENUM('markdown', 'html') DEFAULT 'markdown',
    storage_path VARCHAR(512) NOT NULL,  -- OSS 路径
    share_token  VARCHAR(64),            -- 分享短链 token
    share_expire DATETIME,               -- 短链过期时间
    created_at   DATETIME NOT NULL,
    INDEX idx_user_id (user_id)
);
```

### 6.4 四层隔离保证

| 层 | 机制 | 说明 |
|---|---|---|
| **身份隔离** | SSO user_id 绑定 session | 所有 API 自动注入当前用户，无法越权 |
| **数据隔离** | SQL 查询全部带 `WHERE user_id = ?` | 应用层强制，非可选 |
| **并发隔离** | 同一用户可开多个 session | 每个 session 独立的消息流和查询队列 |
| **执行隔离** | SQL 用统一只读 service account | 用户看不到也改不了底层凭据 |

### 6.5 为什么不用 SQLite

| 对比项 | SQLite | MySQL（公司实例） |
|---|---|---|
| K8s 持久化 | Pod 重启丢数据，需额外 PVC | 天然持久化 |
| 多实例 | 不支持并发写（WAL 也有限） | 天然支持 |
| 运维 | 需自己备份、监控 | 公司 DBA 统一运维 |
| 迁移 | 后期必须迁 MySQL | 一步到位 |

**结论：直接用 MySQL，不引入 SQLite。**

---

## 七、Q\&A：会话断了系统能感知吗？能钉钉通知吗？

### 7.1 结论：能感知，能通知

系统通过 SSE 连接状态 + heartbeat 检测用户是否在线。离线后有待送达结果时，通过钉钉 webhook 推送 markdown 通知。

### 7.2 两种断线场景的处理

**场景 A：短查询（CK 秒级）中断**

```
用户发起 CK 查询 → SSE 开始推送
  → 用户关闭浏览器 / 网络断
  → FastAPI 捕获 ClientDisconnect 异常
  → 查询结果已在内存 → 写入 MySQL query_records
  → 用户重新打开页面 → 前端用 session_id 恢复 → 看到结果
  → 无需钉钉通知（结果已持久化，重连即可见）
```

**场景 B：长查询（MC 分钟级）中断** ← 重点场景

```
用户发起 MC 查询 → 后端创建异步任务，返回 query_id → SSE 推送"已提交"
  → 用户关闭浏览器 / 网络断
  → 后端 worker 继续执行 MC SQL（不受前端影响）
  → SQL 执行完成 → 结果写 MySQL + OSS
  → 检查用户在线状态：
    → 该 user_id 有活跃 SSE 连接？
      → 是：通过 SSE 推送结果
      → 否：触发钉钉通知
```

### 7.3 在线状态判断

```python
# 内存维护 user → SSE connection 映射
active_connections: dict[str, set[SSEConnection]] = {}

# 前端每 30s 发 heartbeat
# SSE 连接断开 → 从 active_connections 移除
# 查询完成时检查：len(active_connections.get(user_id, set())) > 0
```

### 7.4 钉钉通知实现

直接复用 sibling-video-agent 已有的 `dingtalk.py` 模块（webhook + HMAC-SHA256 签名）：

**触发条件**

| 事件 | 触发钉钉 | 说明 |
|---|---|---|
| 长查询完成 + 用户离线 | 是 | 主场景 |
| 查询失败 / SQL 报错 | 是 | 用户可能已离开 |
| 报告生成完成 | 是 | 生成耗时可能较长 |
| 短查询完成 + 用户在线 | 否 | SSE 直接推送，无需额外通知 |
| 用户主动取消 | 否 | 不通知 |

**通知格式（钉钉 markdown）**

```markdown
### [Data Agent] 你的查询已完成

- **问题**：BB 美国 DNU 昨天多少
- **状态**：✅ 成功
- **耗时**：45 秒
- **结果摘要**：DNU 12,345（环比 -3.2%）

[点击查看完整结果](https://data-agent.example.com/session/xxx)
```

**配置（K8s Secret 注入）**

```bash
DINGTALK_ACCESS_TOKEN=xxx  # 群机器人 token
DINGTALK_SECRET=xxx        # 加签密钥
```

未配置时 no-op，不阻断主流程。

### 7.5 未来扩展：钉钉 Bot 双向交互

Phase 3 可做钉钉 Bot 接入（不仅推送通知，还能在钉钉里直接提问）：

```
钉钉群消息 @DataAgent "BB 美国 DNU？"
  → 钉钉 webhook → Data Agent API
  → Agent 执行查询
  → 结果以 markdown 卡片回复到群里
```

---

## 八、Q\&A：Langfuse 是否单独部署？

### 8.1 结论：Langfuse 独立部署，不跟 Agent 绑在一个 Pod

Langfuse 是一个独立的 Web 应用，需要自己的 PostgreSQL 和 ClickHouse。它跟 Data Agent 是**观察者与被观察者**的关系，不应该耦合在同一个 Deployment 里。

### 8.2 部署方式（从轻到重三档）

Langfuse 需要 PostgreSQL（不支持 MySQL），所以额外 Pod 数取决于公司是否有现成 PG：

Langfuse 依赖两个存储：**PostgreSQL**（元数据）和 **ClickHouse**（trace 明细）。CK 可复用公司已有集群（建独立 database），但 PG 需确认公司是否有现成实例。

**为什么 Langfuse 不能用 MySQL？** Langfuse 底层用 Prisma ORM，schema 和 migration 写死了 PostgreSQL 语法（JSONB 类型、GIN 索引、数组字段等 PG 专有特性），不是配置能切换的硬依赖。如果公司没有 PG 且不想单独搞，**直接用 MySQL `agent_traces` 表方案（见 8.3），零额外部署，Phase 0 ~ Phase 1 完全够用**。

| 组件 | 能否复用公司基建 | 说明 |
|---|---|---|
| ClickHouse | **能** | 公司 CH 集群里建 `langfuse` database，存 trace 明细 |
| PostgreSQL | 看公司有没有 PG | Langfuse 硬依赖 PG（不支持 MySQL） |

| 场景 | 额外 Pod | 条件 |
|---|---|---|
| **公司有 PG** | **+1**（langfuse-web） | PG + CK 都复用公司基建 |
| **公司无 PG** | **+2**（langfuse-web + langfuse-pg） | CK 复用，PG 自建 |

```
K8s namespace: data-agent
  │
  ├── data-agent-api        ← FastAPI 服务（写 trace 到 Langfuse）
  ├── data-agent-worker     ← 异步 MC 查询 worker
  │
  ├── langfuse-web          ← Langfuse 应用（UI + trace API）
  └── langfuse-pg           ← Langfuse 专用 PostgreSQL（公司有 PG 则不需要此 Pod）
  
  外部依赖（复用公司基建，不新增 Pod）：
  ├── 公司 ClickHouse 集群  ← langfuse database，存 trace 明细
  └── 公司 MySQL            ← Data Agent 业务数据（session/报告/审计）
```

Data Agent 通过 K8s Service 内网地址写 trace：

```python
LANGFUSE_HOST=http://langfuse-web.data-agent.svc.cluster.local:3000
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
```

### 8.3 更轻量的替代方案：自建 MySQL trace 表

如果连 Langfuse 的 1-2 个额外 Pod 都不想要，可以直接用现有 MySQL 记录 trace，零额外部署：

```sql
CREATE TABLE agent_traces (
    id          VARCHAR(36) PRIMARY KEY,
    session_id  VARCHAR(36) NOT NULL,
    user_id     VARCHAR(64) NOT NULL,
    question    TEXT NOT NULL,            -- 用户原始问题
    task_route  VARCHAR(64),              -- 命中的任务路由
    retrieved   JSON,                     -- 检索到的知识（表卡/SQL/policy 名称列表）
    llm_model   VARCHAR(64),              -- 使用的模型
    llm_prompt  LONGTEXT,                 -- 完整 prompt（调试用）
    llm_output  LONGTEXT,                 -- LLM 原始输出
    tokens_in   INT,                      -- 输入 token 数
    tokens_out  INT,                      -- 输出 token 数
    tool_calls  JSON,                     -- 工具调用记录（SQL 执行、知识检索等）
    duration_ms INT,                      -- 总耗时
    status      ENUM('success', 'error', 'timeout') NOT NULL,
    error_msg   TEXT,
    created_at  DATETIME NOT NULL,
    INDEX idx_session (session_id),
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
);
```

查 trace 直接写 SQL 或在管理页面加一个 trace 列表。功能不如 Langfuse 丰富（没有图形化思维链、没有 token 趋势图），但满足基本的调试和审计需求。

### 8.4 分阶段方案

| 阶段 | 可观测方案 | 额外部署 |
|---|---|---|
| **Phase 0**（技术验证） | **structlog** JSON → stdout → SLS | 0 Pod |
| **Phase 1**（核心能力） | structlog + **MySQL agent_traces 表** | 0 Pod |
| **Phase 1.5**（可选） | 加 **Langfuse** 自部署（需要图形化 trace 调试时） | +1~2 Pod |
| **Phase 2+**（生产化） | Langfuse + SLS 告警 + Prometheus metrics | +1~2 Pod |

Phase 0 ~ Phase 1 完全零额外部署，用 structlog + MySQL trace 表就能覆盖调试和审计。Langfuse 等团队实际用起来、trace 量上来后再按需加。

### 8.5 日志分层

| 层级 | 内容 | 存储 |
|---|---|---|
| L1 请求日志 | HTTP 请求/响应、异常 | structlog → stdout → SLS |
| L2 Agent Trace | 思维链、工具调用、知识检索、SQL、LLM 输入输出 | Langfuse（Phase 0 降级到 structlog） |
| L3 业务审计 | 查询历史、执行的 SQL、数据访问记录 | MySQL `query_records` 表 |

---

## 九、外仓演进

### 结论：Runtime 上线后外仓不废弃，角色转变

| 阶段 | 外仓（dist）定位 | 内仓定位 |
|---|---|---|
| 现在 | DA 同事查数入口 | 开发工作区 |
| Web POC 上线后 | 降级为 power user 工具 + 知识贡献入口 | 开发工作区 + Web 部署源 |
| Web 稳定运行后 | 可选保留（Cursor 辅助）或归档 | 唯一源码仓 |

短期不动外仓，等 Web 服务稳定运行 2-4 周后再决定。

---

## 十、K8s 部署拓扑

```
山海 DeployerV2
  → Docker Build（Python 3.12 + FastAPI + 依赖）
  → ACR 镜像推送
  → K8s namespace: data-agent

Deployments:
  data-agent-api:       FastAPI 服务, port 8000
  data-agent-worker:    异步 MC 查询 worker
  langfuse-*:           可观测性（Phase 1）

ConfigMap:
  data-agent-config:    应用配置（MC/CK endpoint, 网关地址等）

Secrets:
  data-agent-secrets:   MC AK/SK, CK 密码, LLM API key, SSO secret, 钉钉 token

Service + ALB Ingress:
  https://data-agent.example.com

PVS (OSS 后端):
  /data/reports/         报告文件
```

### Dockerfile 参考（同 sibling-video-agent 模式）

```dockerfile
FROM python:3.12-slim
# 系统依赖
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 应用代码
COPY app/ /app/app/
WORKDIR /app

# 一镜两用
# API: uvicorn app.main:app --host 0.0.0.0 --port 8000
# Worker: python -m app.worker
```

---

## 十一、分阶段落地节奏

### Phase 0（1 周）：技术验证 ✅ 已完成

- ✅ PI RPC Agent：通用 MC/CK 查询 tool（独立脚本 `runtime/tools/data_query.py`）+ verified SQL 匹配 + 知识内容注入
- ✅ FastAPI + SSE 最小服务（含 heartbeat、event ID、断线重连）
- ✅ LiteLLM 网关接通验证（preflight 预检）
- ✅ MySQL 持久化（session/message/trace/query_record/report，Alembic migration）
- ✅ React 前端对话式 UI
- **验收**：浏览器输入「BB 美国 DNU 昨天多少」→ 流式返回 SQL + 结果

### Phase 1（2-3 周）：核心能力

- 接入完整任务路由（9 类 task_routes）
- MC 执行器 + 异步长查询
- verified SQL 匹配（27 条）+ Text2SQL 兜底
- 门禁层：freshness + PII + read-only
- Session 管理（MySQL）
- 前端对话式 UI
- SSO 认证
- **验收**：2-3 个 DA 同事内测

### Phase 2（3-4 周）：生产化

- Markdown 报告生成 + OSS 存储
- 钉钉通知（长查询完成 / 断线恢复）
- Langfuse trace 接入
- Docker 镜像 + 山海部署
- 断线重连 + 会话恢复
- E2E 回归测试
- **验收**：DA/UA 组 5+ 人日常使用

### Phase 3（远期）

- MCP Server 化
- 钉钉 Bot 接入
- 闭环经验回写
- 外仓评估是否归档

---

## 十二、关键技术栈总结

| 组件 | 选型 | 参考来源 |
|---|---|---|
| Agent 框架 | PI Framework (`@earendil-works/pi-coding-agent`) | earendil-works/pi |
| Web 后端 | FastAPI | sibling-video-agent |
| 前后端通信 | SSE | - |
| 前端 | React + Vite | Phase 0 轻量选型 |
| ORM | SQLAlchemy 2.0 + Alembic | sibling-video-agent |
| LLM | 公司 LiteLLM 网关（OpenAI 兼容） | sibling-video-agent `gateway.py` |
| MC 执行 | PyODPS | 现有 skill |
| CK 执行 | clickhouse-driver | 现有 skill |
| 认证 | 公司 SSO ticket | sibling-platform `sso.go` |
| 文件存储 | OSS via PVS | sibling-platform HtmlReport |
| 通知 | 钉钉 webhook | sibling-video-agent `dingtalk.py` |
| 日志 | structlog → SLS | sibling-video-agent |
| Trace | Langfuse 自部署（Phase 1） | - |
| 部署 | 山海 DeployerV2 → K8s | sibling-platform / sibling-video-agent |

---

## 待决策项

以下事项需要在开始实现前确认：

1. ~~**前端技术栈确认**~~：已确认 React + Vite（2026-06-21）
2. ~~**LLM 模型选择**~~：已确认 qwen3-max，通过公司 LiteLLM 网关（2026-06-21）
3. **K8s namespace / 域名**：SRE 申请
4. **SSO AppID 申请**：走公司 SSO 注册流程
5. **MySQL 实例**：复用现有还是申请新实例
6. **OSS Bucket**：申请 `data-agent` bucket + PVS 挂载
7. **钉钉机器人**：申请 webhook token
