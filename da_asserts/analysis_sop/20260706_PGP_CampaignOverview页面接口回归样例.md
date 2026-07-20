# PGP Campaign Overview 页面接口回归样例

## 元信息

| 项 | 内容 |
|---|---|
| ID | `sop_20260706_pgp_campaign_overview_page_api_regression_sample` |
| 状态 | live_validated_partial |
| 生成日期 | 2026-07-06 |
| 目标环境 | `https://placement-test.example.com` |
| 适用问题 | Campaign Overview 页面接口级验证、登录态只读 smoke、页面数据链路监控样例 |
| 来源 | `da_assets/analysis_sop/20260706_投放看板live验证记录.md`、PGP `campaign-overview` 前后端代码 |

本样例用于把“底层 MI / CK 已验”推进为“PGP 页面业务接口已验”。它只覆盖只读接口，不触发 admin prewarm、forecast-probe、下载任务、同步任务或任何广告平台写操作。

## 认证与安全边界

PGP 页面业务接口支持两条合法认证路径：

| 路径 | 说明 |
|---|---|
| `pgp_session` cookie | PGP 自己的 SSO 登录态，浏览器页面请求默认 `credentials: include` |
| MI iframe token | 可信 MI 父域 + `X-MI-Parent-Origin` + `X-MI-Token` |

验证要求：

- 不打印、不归档、不提交 `pgp_session`、MI token、SSO ticket、cookie、localStorage token、用户身份字段。
- 每个请求必须带 `X-Trace-ID`，只记录 trace、HTTP 状态、业务 code、聚合摘要。
- 临时 cookie 若必须落地，只能进入 `.scratch/` 或本机 env；本样例推荐使用已登录 Chrome 页面同源请求。
- `/v1/agent/smoke` 和 `/v1/agent/manifest` 是 agent-friendly 元信息入口；当前 test 已通过 public probe 验证，不能再把 404 视为可接受状态。

## 样本 A：Juggle Applovin 全链路页面接口

### 页面参数

```text
campaign_name=Juggle-WW-ROAS-D28-RC-CPMM
bundle_id=com.kcolb.juggle
media_source=applovin_int
forecast_version=v6_sdk
active_date=2026-06-22~2026-07-05
```

Trace base：`codex-pgp-live-20260706102239`。

### 期望接口矩阵

| 页面接口 | 触发方式 | 期望 HTTP | 期望 body code | 关键断言 |
|---|---|---:|---:|---|
| `GET /api/me` | 页面认证态检查 | 200 | 0 | 浏览器登录态有效；不保存用户身份值 |
| `GET /v1/campaign-overview/filter-options?field=bundle_id` | 页面初始化 | 200 | 0 | 返回包体选项 |
| `GET /v1/campaign-overview/filter-options?field=campaign_name...` | 页面初始化 | 200 | 0 | 能命中当前 campaign |
| `GET /v1/campaign-overview/filter-options?field=media_source...` | 页面初始化 | 200 | 0 | 能返回当前渠道选项 |
| `POST /v1/campaign-overview/query` | `sections=["core"]` | 200 | 0 | `access_issues=[]`，返回 core 页面结构 |
| `POST /v1/campaign-overview/history` | 首屏并发 | 200 | 0 | 返回 history events，来源可为 MI campaign history |
| `POST /v1/campaign-overview/query/red-line-check` | 首屏并发 | 200 | 0 | `ready=true`，返回红线 / 目标线 / daily judgments |
| `POST /v1/campaign-overview/query/core-forecast` | core 后 forecast | 200 | 0 | 返回 forecast 相关页面结构 |
| `POST /v1/campaign-overview/query` | `sections=["curves","governance","materials","plan_config"]` | 200 | 0 | extended 分块可返回；`access_issues=[]` |
| `POST /v1/campaign-overview/ai-summary` | 页面缓存探测 | 200 | 404 | `ai_summary_cache_miss` 不算页面数据失败 |
| `POST /v1/campaign-overview/query/top15country` | 国家贡献 lazy | 200 | 0 | 返回国家贡献 rows |
| `POST /v1/campaign-overview/query/top15country/forecast` | 国家贡献 forecast lazy | 200 | 0 | 返回 forecast rows |

## 样本 B：Google US Campaign core + Top 国家轻量探针

### 页面参数

```text
campaign_name=US-LH015-3.0--ARO-XH-260319-通用词
bundle_id=com.kcolb.juggle
media_source=googleadwords_int
forecast_version=v6_sdk
url_start=2026-06-18
url_end=2026-07-01
```

验证方式：已登录 Chrome 页面同源 `fetch`，不读取或打印 cookie/token。

| 接口 | Trace ID | HTTP / code | 关键结果 |
|---|---|---|---|
| `GET /api/me` | `codex-pgp-me-20260706103059` | 200 / 0 | 登录态有效；用户字段未归档 |
| `GET /v1/campaign-overview/filter-options?field=forecast_version&bundle_id=com.kcolb.juggle` | `codex-pgp-options-20260706103059` | 200 / 0 | 返回 5 个 forecast option：`origin`、`v6`、`xy_v6`、`v6_sdk`、`v6_纠偏` |
| `POST /v1/campaign-overview/query`，`sections=["core"]` | `codex-pgp-query-core-20260706103059` | 200 / 0 | `ready=true`，`access_issues=[]`；后端归一窗口为 `2026-06-22~2026-07-05`，Campaign 状态 `ENABLED`，预算 `30500` |
| `POST /v1/campaign-overview/query/top15country` | `codex-pgp-top15country-20260706103126` | 200 / 0 | `ready=true`，`access_issues=[]`；返回国家 `US`，`cost=297524.1989999974`、`registers=109383`、`roi360=0` |

样本 B 用于快速确认页面认证、forecast options、core query 和 CK 国家贡献路径；它不替代样本 A 的完整页面链路覆盖。

## 样本 C：Agent public probe

验证方式：

```bash
python3 tools/scripts/probe_pgp_agent_endpoints.py --base-url https://placement-test.example.com
```

本样本不使用 cookie、token 或登录态，只验证 agent-friendly 公开元信息入口。

| 接口 | Trace ID | HTTP / code | 关键断言 |
|---|---|---|---|
| `GET /v1/agent/smoke` | `codex-pgp-agent-smoke-20260706200004` | 200 / 0 | `status=ok`、`does_not_call_upstream=true`、`secrets_redacted=true`、response `x-trace-id` 回写 |
| `GET /v1/agent/manifest` | `codex-pgp-agent-manifest-20260706200006` | 200 / 0 | route catalog 含 `public_safe` / `auth_required_readonly` / `mutating_or_expensive`；request shapes 含 `campaign_query`、`roi360_query` |

## 样本 D：Campaign Overview 页面业务接口脚本

脚本入口：`probe_pgp_campaign_overview_api.py`。

验证方式：

```bash
# 无凭证边界检查：必须 401 / unauthenticated
python3 tools/scripts/probe_pgp_campaign_overview_api.py \
  --auth none \
  --profile auth-boundary \
  --base-url https://placement-test.example.com

# 认证态轻量链路：需要本机 cookie jar
PGP_COOKIE_FILE=.scratch/pgp.cookies \
python3 tools/scripts/probe_pgp_campaign_overview_api.py \
  --auth cookie \
  --profile light \
  --base-url https://placement-test.example.com

# MI iframe 认证态：需要本机 MI_TOKEN 环境变量
MI_TOKEN=<local-only> \
python3 tools/scripts/probe_pgp_campaign_overview_api.py \
  --auth mi-token \
  --profile light \
  --base-url https://placement-test.example.com
```

脚本约束：

- 不打印、不归档、不提交 `pgp_session`、MI token、SSO ticket、cookie、localStorage token、用户身份字段。
- 无凭证时只检查 `/api/me` 与低成本 `forecast_version` 选项是否被认证中间件拦截。
- 有凭证时按页面真实调用顺序检查 `/api/me`、`filter-options`、`query core`、`top15country`；`--profile full` 才追加 history、red-line、core-forecast、extended 和 top15country forecast。
- 输出只包含 trace、HTTP、body code、`ready`、row count、`access_issues` 数量和结构摘要。

2026-07-06 本机未设置 `PGP_COOKIE_FILE`、`MI_TOKEN` 或 `.scratch/pgp.cookies`，已执行无凭证边界检查：

| 接口 | Trace ID | HTTP / code | 关键断言 |
|---|---|---|---|
| `GET /api/me` | `codex-pgp-page-api_me_unauth-20260706201315` | 401 / 401 | 无登录态被拦截，response `x-trace-id` 回写 |
| `GET /v1/campaign-overview/filter-options?field=forecast_version&bundle_id=com.kcolb.juggle` | `codex-pgp-page-forecast_options_unauth-20260706201317` | 401 / 401 | 业务路由无登录态被拦截，认证中间件生效 |

## 请求体模板

### core section

```json
{
  "filters": {
    "campaign_name": "<campaign_name>",
    "bundle_id": "<bundle_id>",
    "media_source": "<media_source>",
    "active_date_start": "<yyyy-mm-dd>",
    "active_date_end": "<yyyy-mm-dd>",
    "forecast_version": "<forecast_version>",
    "revenue_source": "sdk"
  },
  "sections": ["core"],
  "force_refresh": false
}
```

### extended section

```json
{
  "filters": {
    "campaign_name": "<campaign_name>",
    "bundle_id": "<bundle_id>",
    "media_source": "<media_source>",
    "active_date_start": "<yyyy-mm-dd>",
    "active_date_end": "<yyyy-mm-dd>",
    "forecast_version": "<forecast_version>",
    "revenue_source": "sdk"
  },
  "sections": ["curves", "governance", "materials", "plan_config"],
  "force_refresh": false
}
```

### Top15 country

```json
{
  "filters": {
    "campaign_name": "<campaign_name>",
    "bundle_id": "<bundle_id>",
    "media_source": "<media_source>",
    "active_date_start": "<yyyy-mm-dd>",
    "active_date_end": "<yyyy-mm-dd>",
    "forecast_version": "<forecast_version>",
    "revenue_source": "sdk"
  },
  "force_refresh": false
}
```

## 监控断言

| 等级 | 断言 | 失败含义 |
|---|---|---|
| P0 | `/api/me` 不能 200 / code=0 | 登录态或认证中间件不可用，业务接口验证无效 |
| P0 | `POST /v1/campaign-overview/query` core 不是 200 / code=0 | 页面主链路不可用 |
| P0 | `/v1/agent/smoke` 不是 200 / code=0，或 `does_not_call_upstream` / `secrets_redacted` 不是 true | agent-friendly 部署探针不可用或安全契约退化 |
| P0 | 无凭证访问 `/api/me` 或 Campaign Overview 业务路由不是 401 / unauthenticated | 认证中间件可能被绕过或网关策略漂移 |
| P1 | `/v1/agent/manifest` 不是 200 / code=0，或 route catalog / request shapes 缺关键项 | agent 无法发现认证方式、只读路由和请求模板 |
| P1 | core `ready=false` 或 `access_issues` 非空 | scope 解析、MI、CK 或 forecast 依赖存在问题 |
| P1 | `top15country` 不是 200 / code=0 | 国家贡献 CK / forecast 页面分支不可用 |
| P2 | `ai_summary_cache_miss` | AI summary 缓存未命中，不代表页面指标数据失败 |

## 输出模板

```text
目标环境：
验证方式：
认证态：
Trace IDs：
页面参数：
接口矩阵：
核心断言：
已知缺口：
是否可升级：
```

## 已知缺口

- 当前 test 环境 `/v1/agent/smoke` 与 `/v1/agent/manifest` 已通过 public probe 验证；若再次出现 404，应视为 agent-friendly 探针回归。
- 样本 A / B 是页面接口回归样例，不代表所有 campaign、包体、国家和 forecast version 都已验证。
- 页面接口通过不等于全部数值口径已 verified；数值解释仍需结合 MI / CK 对账、freshness 和业务窗口成熟度。
