# UA 决策行为沉淀 Phase0 PII 与安全责任边界（UA-P0-11）

> 状态：`frozen_candidate`
>
> 日期：`2026-07-23`
>
> `TASK_ID=UA-P0-11`；`TASK_TYPE=IMPLEMENTATION`；`BASE_COMMIT=37977c8c`
>
> 权威方案：第 3.1、8.7、8.8、8.9、9 节
>
> 合并来源：P0-01（18 字段政策 SHA256）、P0-03（MI 接口 user 字段）、P0-06（脱敏规则）

## 0. 人话摘要

这个任务定义"什么数据不能碰、什么数据要脱敏、谁负责什么"。

核心规则：
- **不存**：操作人邮箱明文、MI raw JSON、用户 token、cookie
- **要脱敏**：操作人身份用 HMAC（不是普通 SHA256），备注文本脱敏后才能进 LLM
- **不写**：Data Agent 不持有 MI token、不调媒体写接口
- **分层**：受限基础表（含 PII）只在内网，Agent 只看安全 projection

## 1. PII 字段清单与等级

| 字段 | 来源 | PII 等级 | 处理方式 |
|---|---|---|---|
| `change_event_user_email` | Google change event 宽表 | 高（邮箱明文） | 入仓前 HMAC 脱敏；不进 Agent 层 |
| `user`（MI ua-operates/ua-remarks） | MI 接口返回 | 高（邮箱明文） | 同上 |
| `description`（MI 操作/备注文本） | MI 接口返回 | 中（可能含人名/金额） | 脱敏后进受控索引；原始文本只存来源系统 |
| `change_event_old_resource`/`new_resource` | Google change event 宽表 | 中（含配置 JSON） | 只在库内解析；不输出整段 JSON |
| `before_after_json` | 18 字段统一变更日志 | 中 | 安全层解析为预算字段；原始 JSON 不进 Agent serving |
| `account_id` | 三平台配置表 | 低（账户 ID） | 聚合可用；明细不输出 |
| MI Bearer token | `~/.codex/secrets/mi-curl/` | 极高 | 不入仓、不进 chat、不转发 |

## 2. 操作人脱敏方案

### 2.1 当前状态

18 字段政策（`平台操作记录统一变更日志字段规范.md:45`）：`email/user_id 替换为 operator_<sha256>`（普通 SHA256，无密钥）。

### 2.2 冻结升级路径

| 阶段 | 脱敏方式 | 能做什么 | 不能做什么 |
|---|---|---|---|
| Phase 0（当前） | 保持 SHA256 不变 | 字段格式验证 | 操作人维度分析 |
| 正式入仓前 | 升级为 HMAC | 同一人去重、操作频次统计 | 反推原始身份 |
| HMAC 升级前 | 只存 `operator_redacted` | 无 | 任何个人级分析 |

### 2.3 HMAC 规范

- 算法：HMAC-SHA256
- 密钥：由安全 Owner 管理，不入仓、不进代码
- `key_scope`：`ua_decision_operator`
- `key_version`：每次密钥轮换递增
- 输出格式：`operator_hmac_<key_version>_<hash前16位>`
- 密钥轮换时：旧 hash 保留，新 hash 追加，不覆盖

### 2.4 低熵文本禁用普通 hash

以下字段**禁止**用普通 SHA256（低熵可被彩虹表反推）：
- 操作人邮箱
- 工号
- 备注 text
- 可枚举的 payload

这些字段必须用 HMAC，或只存 `redacted`。

## 3. 分层访问设计

### 3.1 受限基础表（18 字段统一变更日志）

- 包含 `change_by`（脱敏后）、`before_after_json`（原始）、`notes`
- 按受限数据资产管理
- **不进入** Data Agent 默认 RAG 召回
- **不进入** CK 默认 serving projection

### 3.2 Agent 安全 projection

从受限基础表投影出安全字段：
- `change_by` → `operator_token`（HMAC 后）
- `before_after_json` → `budget_before`/`budget_after`/`change_pct`（解析后数值）
- `notes` → `source`（只保留来源标记）
- `description` → `intent_summary_safe`（脱敏摘要，如有）

### 3.3 默认 RAG 禁止项

以下内容**不进入** Agent 默认召回：
- 操作人邮箱（明文或 SHA256）
- 原始 before/after JSON
- MI raw payload
- 用户 token / cookie / SSO session
- `change_event_user_email` 列

## 4. 系统责任边界

| 系统 | 责任 | 禁止 |
|---|---|---|
| MI / Nexus | 只读操作审计来源 | — |
| MC / DataWorks | 追加式事实、特征、Episode；受限基础表存储 | 不存明文 PII；不 update/delete 旧 revision |
| CK | serving projection；离线评分结果 | 不作为训练真理源；不存受限基础表原始字段 |
| Data Agent | 通过 typed read-only API 检索证据；输出 `needs_decision` | **不持有 MI 用户 token**；不调媒体写接口；不存 PII |
| PGP | 页面、BFF、鉴权、证据渲染、反馈 DB | 不另建独立决策逻辑；不调媒体写接口 |
| collector | 用服务账号 MI token 做全量采集 | **不持久化用户凭证**；不转发 token；不重放 |

## 5. PGP DB outbox → MC 链路

- PGP 先写产品 DB / transactional outbox（反馈、assignment、exposure、view）
- ETL 追加同步到 MC（不覆盖旧 revision）
- **不能**由页面直接写 MC
- **不能**用覆盖更新抹掉历史 revision

## 6. `pii_leakage_count = 0` 验证方式

| 检测项 | 方法 |
|---|---|
| Agent 输出不含操作人邮箱 | 自动化扫描 Agent 所有输出字段 |
| Agent 输出不含 raw JSON | 检查 `before_after_json` 是否被解析为数值 |
| 默认 RAG 不含受限表 | 检查 RAG 召回配置 |
| 代码中不硬编码 token | grep `Bearer`/`token`/`cookie` |
| MC 表不存明文邮箱 | schema 检查 `change_by` 列格式 |

## 7. 凭证安全

- MI JWT token：存 `~/.codex/secrets/mi-curl/`（当前用户 only 600 权限）
- PGP session：存 `~/.codex/secrets/pgp/`（同上）
- **不入仓**、**不进 chat**、**不进报告**
- token 不过期（PGP 代码确认），但仍定期检查 `last_used_at`

## 8. 非目标声明

本任务未修改 18 字段政策文件；未创建 HMAC 密钥；未执行 DDL/DML；未部署。脱敏升级路径为候选版本，待正式入仓前由安全 Owner 批准。
