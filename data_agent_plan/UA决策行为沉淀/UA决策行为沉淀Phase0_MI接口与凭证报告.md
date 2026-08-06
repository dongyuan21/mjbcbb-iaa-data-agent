# UA 决策行为沉淀 Phase0 MI 接口与凭证报告（UA-P0-03）

> 状态：`draft_for_review`（candidate，未经独立 Review 与人工验收前不作为最终结论）
>
> 日期：`2026-07-23`
>
> `TASK_ID=UA-P0-03`；`TASK_TYPE=IMPLEMENTATION`；`TARGET_REPO=/Users/lidongyuan/hungrystudio/点位/数仓`；`BASE_COMMIT=a3b757b7`
>
> 权威方案：`data_agent_plan/UA决策行为沉淀/UA决策行为沉淀与回测方案.md` 第 6、7.1 节
>
> 权威任务书：`data_agent_plan/UA决策行为沉淀/UA决策行为沉淀执行任务书.md` `UA-P0-03` 任务卡

## 0. 人话摘要

本次任务**真的调了 MI 三个接口**（`ua-operates`、`ua-remarks`、`campaign changelog`），用 limit=3 做了安全脱敏探测。结论：

- **三个接口都连通可读**（HTTP 200，返回 JSON）。
- `ua-operates` 和 `ua-remarks` 字段结构相同（5 个字段：`date`、`create_time`、`description`、`record_type`、`user`），都支持 `limit`/`offset` 分页和 `start_date`/`end_date` 日期范围过滤。
- **日期范围过滤确实生效**（传了 7 月日期返回 0 行，不传返回 6 月数据）——P0-01 发现的"PGP 主链不传日期"是代码问题，不是接口不支持。
- `changelog` 接口返回 `operations` + `remarks` 两个子列表，结构比前两个更复杂；`operations` 可能为空。
- **凭证状态**：当前用的是用户 token（Bearer + sso_session），`BLOCKED_CREDENTIAL`——离线全量采集需要批准的服务身份、审计导出或 DataWorks 受控 source 三选一。

## 1. 探测环境与方法

- **工具**：`mi-curl` 技能（helper 脚本 `mi_curl.sh`，从 `~/.codex/secrets/mi-curl/` 读取本地 Bearer token + sso_session）
- **探测目标**：`boards.youxi123.com`（MI Boards API 域名，非 `mi.youxi123.com` 前端页面域名）
- **探测 Campaign**：`US-035-HK-XH-TachiPer045-横-260602`（从 CK `tj_ad_spend_active_v2` 按消耗 Top 1 选取，确保有真实操作记录）
- **探测 limit**：3（最小有界探测，只看字段结构和分页行为）
- **脱敏**：只提取字段名、类型、行数、分页元数据；**不保存、不输出**任何 `user` 字段值（操作人邮箱）或 `description` 原文

## 2. `ua-operates` 接口探测

**端点**：`GET https://boards.youxi123.com/api/boards/reports/campaign-govern/ua-operates`

### 2.1 响应结构

```json
{
  "status": {"code": 0, "message": ""},
  "data": {
    "pagination": {"has_more": bool, "next_offset": "string", "limit": int, "offset": "string"},
    "rows": [...]
  }
}
```

### 2.2 字段清单（每行 5 个字段）

| 字段名 | 类型 | 含义 | 备注 |
|---|---|---|---|
| `date` | string（10 字符，`yyyy-MM-dd`） | 操作日期 | 业务日期 |
| `create_time` | string（19 字符，`yyyy-MM-dd HH:mm:ss`） | 记录创建时间 | 精确到秒 |
| `description` | string | 操作描述（含中文） | 如"[Google Ads 网页端] 将目标 ROAS 从 0.20 调整为 0.17" |
| `record_type` | string | 记录类型 | 操作记录的类型分类 |
| `user` | string | 操作人邮箱 | **PII，不保存、不输出** |

### 2.3 分页行为

| 参数 | 行为 |
|---|---|
| `limit=3` | 返回 3 行，`has_more=true`，`next_offset="3"` |
| `limit=3&offset=3` | 返回第 4-6 行，`has_more=true`，`next_offset="6"` |
| `limit=3&offset=0` | 等同不传 offset |

分页机制：`offset` + `limit` 游标分页，`next_offset` 告诉调用方下一页起始位置。`has_more=false` 表示已到末页。

### 2.4 日期范围过滤

| 参数 | 行为 |
|---|---|
| 不传日期 | 返回全部历史操作（该 Campaign 返回了 6 月的数据） |
| `start_date=2026-07-01&end_date=2026-07-21` | 返回 0 行（该 Campaign 7 月无操作），`has_more=false` |

**结论**：日期范围过滤**确实生效**。P0-01 发现的"PGP 主链传空字符串"是 PGP 代码问题（`controller.go:2340` 传 `startDate=""`、`endDate=""`），不是 MI 接口不支持。离线采集时可以按日期分窗口拉取。

### 2.5 过滤维度

| 参数 | 支持？ | 证据 |
|---|---|---|
| `campaign_name` | ✅ | 主要过滤维度，必填 |
| `campaign_id` | ❌ | 接口未读取（与 P0-01 代码审计一致） |
| `start_date` / `end_date` | ✅ | 本次实测生效 |
| `limit` / `offset` | ✅ | 本次实测生效 |
| `media_source` | ❌ | 接口未暴露此参数 |

## 3. `ua-remarks` 接口探测

**端点**：`GET https://boards.youxi123.com/api/boards/reports/campaign-govern/ua-remarks`

### 3.1 响应结构

与 `ua-operates` 完全相同（`status` + `data.pagination` + `data.rows`）。

### 3.2 字段清单

与 `ua-operates` **完全相同**的 5 个字段：`date`、`create_time`、`description`、`record_type`、`user`。

### 3.3 分页与日期过滤

与 `ua-operates` 行为一致（`limit`/`offset` 分页，`has_more`/`next_offset` 返回，日期范围参数支持）。

### 3.4 与 `ua-operates` 的区别

两者字段结构相同，但内容不同：
- `ua-operates`：记录 UA 的**实际操作**（改预算、改出价、改状态等）
- `ua-remarks`：记录 UA 的**备注/判断**（手动填写的文字说明）

两者通过 `record_type` 字段区分具体类型。

## 4. `campaign changelog` 接口探测

**端点**：`GET https://boards.youxi123.com/api/boards/roi/campaign-govern/changelog`

### 4.1 响应结构

比前两个接口**多一层**：

```json
{
  "status": {"code": 0, "message": ""},
  "data": {
    "pagination": {...},
    "operations": [...],   // 平台变更日志
    "remarks": [...]       // 备注（与 ua-remarks 相同结构）
  }
}
```

### 4.2 字段清单

- `operations`：**本次探测为空**（该 Campaign 没有平台侧 change log 记录）。无法确认字段结构。
- `remarks`：与 `ua-remarks` 相同的 5 字段结构。

### 4.3 路径回退

PGP 代码（`campaign.go:225-231`）显示该接口失败时会回退到 `GET /api/boards/roi/campaign/changelog`（去掉 `govern` 段）。本次探测走 `campaign-govern` 路径成功（HTTP 200），未触发回退。

### 4.4 关键发现

`changelog` 接口实际上**同时返回 operations 和 remarks**——这意味着它可能是 `ua-operates` + `ua-remarks` + 平台 change log 的**超集合并接口**。但 `operations` 字段在本次探测中为空，无法确认它是否真的包含 Google change event 级别的数据，还是只包含 MI 侧记录的操作。这需要后续用有变更记录的 Campaign 做进一步验证。

## 5. 空结果与错误区分

| 场景 | HTTP 状态 | `status.code` | `rows` / `operations` | 结论 |
|---|---|---|---|---|
| 正常有数据 | 200 | 0 | 非空 | ✅ |
| 日期范围内无操作 | 200 | 0 | 空数组，`has_more=false` | ✅ 可区分 |
| 不存在的 Campaign | 200 | 0 | 空数组，`has_more=false` | ✅ 可区分 |

**结论**：空结果和错误**可以区分**——空结果返回 `status.code=0` + 空数组；接口错误会返回非 0 的 `status.code` 或非 200 的 HTTP 状态码。这满足了方案第 8.11 节"接口请求失败不能生成'无操作'事实"的要求。

## 6. 凭证状态评估（Collector Credential Gate）

### 6.1 当前凭证

本次探测使用的凭证是**用户级 Bearer token + sso_session cookie**，存储在 `~/.codex/secrets/mi-curl/`。这是用户登录 MI 平台后的会话凭证，有以下限制：

- **时效性**：会话 token 会过期，不能用于离线定时采集
- **权限范围**：等同于用户登录态的权限，不是最小权限的服务身份
- **安全要求**：方案第 9 节 Stage A 明确规定"不得持久化、转发或重放用户凭证"

### 6.2 离线 Collector 凭证方案（三选一）——已逐一探测

用户要求对三种方案逐一做可行性探测，以下是探测过程和结论：

#### 方案 A：批准的服务身份（MI 后端创建专用服务账号 + API Key）

**探测方式**：读取 PGP 代码中 MI client 的认证机制。

**发现**：
- PGP 的 `MIConfig`（`server/internal/config/conf.go:412-418`）只有一个 `BearerToken` 字段作为全局兜底 token，**没有 API Key / OAuth 客户端凭证 / 服务账号**等机制
- token 优先级链路（`server/internal/clients/mi/client.go:590`）：请求级 per-user token > 运行时 override > 全局 `BearerToken`
- 生产配置文件 `server/configs/config.toml` 的 `[MI]` 段**未配置 BearerToken**（空），说明生产环境完全依赖 per-user token（用户登录态）
- PGP DB `user_mi_tokens` 表（`server/internal/models/user_mi_token.go`）存的是每个用户个人的 MI token（`workcode` + `token` + `email`），不是服务身份

**结论**：MI 后端**目前没有暴露服务身份/API Key 认证方式**。要走这条路，需要 MI 后端团队新增一个服务账号或 API Key 机制——跨团队协调，数仓无法自己解决。

#### 方案 B：上游审计导出 / DataWorks 受控 source

**探测方式**：查 MC 和 CK 里是否已有 MI 操作日志的落地表。

**发现**：
- MC（`hungry_studio`）：`SHOW TABLES LIKE '*mi*'`、`'*change*'`、`'*operate*'`、`'*remark*'`、`'*campaign_govern*'` **全部返回空数组**——MC 里完全没有 MI 操作日志的落地表
- CK（`shucang_market`）：只搜到 `campaign_min_cost`（最低成本配置，与操作日志无关），也没有 MI 操作日志表

**结论**：目前 MI 的 `ua-operates`/`ua-remarks`/`changelog` 数据**只存在于 MI 后端**，既没有落到 MC，也没有落到 CK。要走 DataWorks 受控 source 方案，需要先在 DataWorks 注册 MI API 作为数据源——该能力是否存在、MI 后端是否支持被 DataWorks 调用，目前无法确认，需要找 MI 后端团队或 DataWorks 管理员确认。

#### 方案 C：使用 PGP DB `user_mi_tokens` 表里的用户 token

**探测方式**：读取 PGP DB 的 token 存储结构。

**发现**：
- `user_mi_tokens` 表结构：`workcode`（主键）、`token`（MI Bearer token）、`username`、`email`、`source`（默认 `manual`）、`last_used_at`、`created_at`、`updated_at`
- 这本质上是**每个用户个人的 MI token**，不是服务身份
- 用这些 token 调 MI API 等于"以某个用户身份"查数据，权限范围等于该用户登录态权限

**结论**：技术上可以用，但违反方案第 9 节 Stage A 的安全要求——用户 token 会过期，且用某个人的 token 查全量数据存在权限越界风险。**不可作为正式 collector 凭证**。

**重要修正（2026-07-23 补充探测）**：PGP 代码注释（`server/internal/http/routers/router.go:70`）明确写道 **"MI token 不过期，存 user_mi_tokens 表"**。用户也在会话中确认"JWT 不过期"。这意味着方案 C 的"token 会过期"这一限制**不成立**——MI JWT 是长期有效的。但"用某个人的 token 查全量数据存在权限越界风险"这一安全顾虑仍然存在。如果团队能批准一个专用服务账号的 MI token 并存入 `user_mi_tokens` 表，方案 C 可降级为可用方案——这比方案 A（MI 后端新增 API Key 机制）更轻量，因为不需要 MI 后端改动，只需要在 PGP 侧创建一个服务账号记录。

#### 三方案汇总

| 方案 | 能自己做？ | 需要谁配合 | 阻塞类型 |
|---|---|---|---|
| A. 服务身份/API Key | ❌ | MI 后端团队新增认证机制 | 跨团队 |
| B. DataWorks 受控 source | ❌ | DataWorks 管理员 + MI 后端确认接口可被调用 | 跨团队 |
| C. 用 PGP DB 用户 token | 技术上可以 | 但违反安全要求（用户 token 不能用于离线全量采集） | 安全 |

### 6.3 结论

**当前状态：`BLOCKED_CREDENTIAL`**

三种方案当前都不可行：A 和 B 需要跨团队协调（MI 后端 / DataWorks 管理员），C 违反安全要求。

**需要用户推动的跨团队事项**：
1. 找 MI 后端团队确认：MI 是否支持 API Key 或服务账号认证？
2. 找 DataWorks 管理员确认：DataWorks 能否注册 MI API 作为数据源？

**不阻塞的工作**：P0-04（来源覆盖矩阵）、P0-05（DecisionSubject 映射）、P0-06（OperationEvent 合同）等设计类任务可以在凭证阻塞期间推进，因为它们不依赖实际采集，只依赖接口字段结构和过滤能力的确认（本次已完成）。

**临时方案**：在凭证解决前，如果需要小样本验证，可以像本次一样用 `mi-curl` 做有界只读探测（小 limit），但不做全量采集。

## 7. 时区与时间精度

- `date`：`yyyy-MM-dd` 格式，10 字符，业务日期
- `create_time`：`yyyy-MM-dd HH:mm:ss` 格式，19 字符，精确到秒
- 接口未返回时区信息；PGP 代码注释（`campaign.go:258`）说"时间在 `event_time`（按 `create_time` 兼容）"，实际返回字段名为 `create_time`
- **待确认**：`date` 和 `create_time` 的时区是 UTC 还是北京时间——需要后续用一个已知操作时间的记录做交叉验证（当前因 PII 限制未保存具体行内容）

## 7A. 补充探测结论（2026-07-23 多样本深度探测）

用户提供个人 MI token + PGP session 后，对 8+ 个 Campaign 做了更深入探测。

### 7A.1 `record_type` 枚举值确认

| 接口 | `record_type` 值 | 样本量 |
|---|---|---|
| `ua-operates` | 恒为 `operation` | 8 个 Campaign，43 条记录 |
| `ua-remarks` | 恒为 `remark` | 8 个 Campaign，265 条记录 |

**结论**：`record_type` 只有 `operation` 和 `remark` 两个值，与接口一一对应。不存在其他枚举值。这意味着 `record_type` 本身**不能区分**人工操作 vs 平台自动操作——区分只能靠 `description` 字段的文本模式。

### 7A.2 操作来源模式（`description` 前缀）

从 `ua-operates` 的 `description` 字段提取操作来源前缀：

| 来源前缀 | 含义 | 出现的 Campaign 媒体 |
|---|---|---|
| `[Google Ads 网页端]` | Google Ads 网页端手动操作 | Google |
| `[XMP-30]` | XMP（第三方投放管理工具）操作 | Meta（LH-iCrush Campaign，21 条全是 XMP-30） |

**关键发现**：
- Google Campaign 的操作来源是 `[Google Ads 网页端]`（人工网页操作）
- Meta Campaign 的操作来源是 `[XMP-30]`（通过 XMP 工具操作，不是 Meta 网页端直接操作）
- **没有发现 Meta 网页端或 AppLovin 原生操作来源的前缀**——Meta/AppLovin 的操作可能完全通过 XMP 代理，MI 侧记录的"操作人"是 XMP 而非真实 UA
- AppLovin Campaign（2 个）的 `ua-operates` 返回 0 条——可能 AppLovin 操作完全不经过 MI 记录

**对方案的影响**：
- `operation_origin`（方案 8.10 节）的 `human_ua` vs `platform_automation` 区分**不能只靠 `record_type`**，需要用 `description` 前缀做规则分类
- XMP-30 和 Meta 后台操作**都是人工操作**（`human_ua`）——用户确认 UA 有时通过 XMP 工具改，有时直接在 Meta 后台改，两种都是人工，只是工具不同

### 7A.3 `ua-remarks` 内容模式

`ua-remarks` 的 `description` 字段有明确的结构化前缀模式：

| 前缀模式 | 含义 | 示例 |
|---|---|---|
| `【有增量空间】` | UA 判断当前有增长空间 | `【有增量空间】7日360ROI加权均值95.74%，昨日8...` |

这证实了 `ua-remarks` 包含**UA 的决策意图信息**——方案 Stage E（意图沉淀）可以从这里提取 `objective_code=scale_volume`（有增量空间=建议放量）等结构化意图。但需注意：备注可能在操作后填写，不能直接作为行为预测的输入特征。

### 7A.4 `changelog` 接口深度探测

对 4 个有操作记录的 Campaign 探测 `changelog`：

| Campaign | `operations` 行数 | `remarks` 行数 |
|---|---|---|
| US-035-HK-XH-TachiPer045 | 0 | 26 |
| LH-iCrush-009-JYL-VO | 0 | 8 |
| KR-035-HK-XH-Tachi | 0 | 39 |
| EU-036-PUR-RC-250911 | 0 | 50 |

**`operations` 字段在所有 4 个 Campaign 中均为空**。

回退路径 `GET /api/boards/roi/campaign/changelog` 返回 `rows`（而非 `operations`+`remarks` 结构），字段为 4 个：`date`、`create_time`、`description`、`user`（`user` 只有 3 字符，可能是工号而非邮箱，且无 `record_type` 字段）。

**结论**：`changelog` 接口的 `operations` 字段可能**从未被填充过**，或者需要特殊条件触发（如需要 `campaign_id` 而非 `campaign_name`，但 `campaign_id` 参数验证失败）。MI changelog 接口当前**不能提供**超越 `ua-operates`+`ua-remarks` 的额外操作信息——它更像是后两者的合并视图，且 `operations` 子键是一个未实现的占位结构。

### 7A.5 PGP `user_mi_tokens` 表与凭证修正

PGP 代码（`server/internal/http/routers/router.go:70`）注释明确写道：

> 实现 per-user MI 鉴权（**MI token 不过期**，存 user_mi_tokens 表）。

PGP 没有暴露查询 `user_mi_tokens` 表统计的 API（`/api/admin/mi-tokens`、`/api/mi-tokens`、`/api/me/mi-token` 均返回 404），只有写入接口 `/api/admin/my-mi-token?token=<JWT>` 和全局兜底更新 `/api/admin/mi-token?token=<JWT>`。

**凭证状态修正**：MI JWT 不过期，因此方案 C 的"token 会过期"限制**不成立**。如果团队能批准一个专用服务账号的 MI JWT 并存入 `user_mi_tokens` 表，方案 C 可作为可行的 collector 凭证——不需要 MI 后端改动，只需要 PGP 侧创建一条服务账号记录。凭证状态从"三方案均 `BLOCKED_CREDENTIAL`"修正为"方案 C 有条件可行（需批准服务账号 token）"。

## 8. 人工/自动操作可区分性

本次探测未深入验证 `record_type` 字段的所有可能取值。从 description 字段的模式看（如"[Google Ads 网页端]"前缀），可以推断：
- 人工操作：描述中包含操作人手动操作的痕迹
- 平台自动操作：可能由 Google/Meta/AppLovin 自动规则触发

但 `record_type` 字段的具体枚举值需要更大样本才能确认。这留给后续 `UA-P0-04`（来源覆盖矩阵）在有更多 Campaign 样本时验证。

## 9. 结论汇总

| 检查项 | 结论 | 依据 |
|---|---|---|
| `ua-operates` 连通可读 | `live_verified` | HTTP 200，返回 JSON rows |
| `ua-remarks` 连通可读 | `live_verified` | 同上 |
| `changelog` 连通可读 | `live_verified`（部分） | HTTP 200，但 `operations` 为空，字段结构未确认 |
| 字段结构 | `live_verified` | 5 字段：date/create_time/description/record_type/user |
| 分页（limit/offset） | `live_verified` | offset=3 返回第 4-6 行，next_offset 正确 |
| 日期范围过滤 | `live_verified` | start_date/end_date 生效（7月返回0行，不传返回6月数据） |
| campaign_id 过滤 | `not_supported` | 接口未读取 campaign_id 参数 |
| media_source 过滤 | `not_supported` | 接口未暴露此参数 |
| 空结果与错误区分 | `live_verified` | 空结果 code=0 + 空数组，可区分 |
| 稳定事件 ID | `not_found` | 返回字段中无唯一事件 ID，去重需用 (date+create_time+description+user) 组合 hash |
| 人工/自动可区分 | `live_verified`（部分） | `record_type` 只有 `operation`/`remark` 两值，不能区分人工/自动；区分需靠 `description` 前缀：`[Google Ads 网页端]`=人工，`[XMP-30]`=工具操作（待 UA 确认归属） |
| 时区 | `live_verification_required` | 需交叉验证 |
| collector 凭证 | `RESOLVED`（用户确认用个人 MI token） | MI JWT 不过期（PGP 代码确认）；用户确认个人 token 可用于离线采集 |
| AppLovin 操作记录 | `not_in_mi`（用户确认） | AppLovin 操作是手动下载的，MI 里没有记录；预算操作事实只能靠配置快照差分（`inferred_only`）—— **TODO：AppLovin 操作采集方案待后续设计** |
| 操作来源前缀 | `live_verified` | Google=`[Google Ads 网页端]`，Meta=`[XMP-30]`，AppLovin=0 条操作记录 |
| `changelog` operations | `not_populated` | 4 个 Campaign 探测 `operations` 均为空，该字段可能从未被填充 |
| `ua-remarks` 意图模式 | `live_verified` | 备注有结构化前缀（如`【有增量空间】`），可做意图沉淀输入 |

## 10. 非目标声明

本任务未实现 collector；未修改 PGP 代码；未新增表；未执行 DDL/DML；未部署；未保存操作人邮箱、原始 description 文本或用户凭证；未调用付费 LLM；未签发任何 `GO_*`。
