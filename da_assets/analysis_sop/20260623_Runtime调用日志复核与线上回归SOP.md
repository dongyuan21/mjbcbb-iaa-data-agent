# SOP: Runtime 调用日志复核与线上回归

## 元信息

| 项 | 内容 |
|---|---|
| ID | `sop_20260623_runtime_call_log_review_and_online_rerun` |
| 状态 | maintained |
| 来源 | `tools/scripts/runtime_review_tool.py`、`runtime/backend/app/services/persistence.py`、本工作区 `AGENTS.md` 的实时读取与证据边界 |
| 适用问题 | Data Agent Runtime 调用日志复核、失败样本诊断、线上回归验证 |
| 适用范围 | MySQL trace / message / query_records，MaxCompute / ClickHouse live probe，Runtime test 环境线上复跑 |
| 最后对齐 | 2026-08-03（按当前 Runtime 主链与工作区规则复核） |

## 分析目标

把“看日志判断问题”升级为可复用复核流程：先查 MySQL 真实 trace，再用 MC / CK live probe 复核失败样本；如果涉及 runtime 修复，再做线上复跑并核验新 trace 与 `query_records` 是否完整落库。

## 触发条件

满足任一条件时必须使用本 SOP：

- 用户要求“复核 Runtime / Data Agent 日志”“看今天的 trace / 调用日志”“复跑线上问题”。
- 问题涉及 Runtime 回答与工具执行不一致、答非所问、空结果、错表、错 join key。
- 需要把复核做成 Goal 长任务、reviewer SOP 或 skill。

## 核心规则

| 项 | 规则 |
|---|---|
| 日志来源 | 先看 MySQL `data_agent_sessions`、`data_agent_messages`、`data_agent_traces`、`data_agent_query_records`，不只看前端回答。 |
| 问题去重 | 先按问题指纹或标准化问题文本去重；同一 session 多 trace 不能直接当多条业务问题。 |
| MC 必跑 | 必须跑 `SELECT 1`，再跑至少一张目标表的 `max(示例产品)` / `max(active_date)` probe。 |
| CK 必跑 | 必须跑 `SELECT 1`，再跑至少一张代表表或目标表分区 probe。 |
| 0 行保护 | 核心 SQL `row_count=0` 或 `rows=[]` 时，必须继续 smoke；不能把分区 probe 包装成业务答案。 |
| 代码边界 | 复核默认先出报告，不直接改代码；只有确认是 Runtime 缺陷，才进入修复与回归。 |
| 线上验证 | 只要修了 runtime，必须在 test 环境复跑同题，核验新 trace 和 `query_records`。 |
| 推荐入口 | 优先使用 `python3 tools/scripts/runtime_review_tool.py review-day` 和 `python3 tools/scripts/runtime_review_tool.py replay`，避免手工拼 SSO / MySQL / HTTP。 |

## 复核分级

| 级别 | 适用场景 | 最低动作 |
|---|---|---|
| L0 快速抽查 | 只是确认有没有真实执行 | MySQL trace + MC/CK 连通性 + 目标表轻量 probe |
| L1 失败样本复核 | 0 行、答非所问、错表、错 join、结果异常 | L0 + 目标表 smoke / join 前后诊断 |
| L2 回归与晋升 | 需要修 runtime、产出 SOP / skill、验证线上修复 | L1 + 本地 E2E + test 环境线上复跑 + 落库核验 |

## 标准步骤

1. 读取 MySQL 日志：
   - 按日期过滤当天 trace。
   - 读取 session、message、trace、query_records。
   - 问题级去重，识别同一 session 多 trace。
   - 可直接运行：`python3 tools/scripts/runtime_review_tool.py review-day --date 2026-06-24`
2. 建立 live 读取能力：
   - MC：`SELECT 1` + 目标表 `max(示例产品)`。
   - CK：`SELECT 1` + 代表表或目标表最新分区 probe。
3. 判定样本类型：
   - 正常回答
   - 答非所问
   - 核心 SQL 0 行
   - 查询记录缺失
   - 路由误判 / 表路由污染 / join key 漂移
4. 对失败样本执行最小必要 smoke：
   - 日期窗口是否成熟
   - 激活表 / 行为表是否各自有数据
   - `bundle_id` / `app_name` / `media_source` / 国家过滤是否掉空
   - join 前后用户数与行数
5. 需要改 runtime 时：
   - 先本地 E2E 跑通同题。
   - 再发布到 test 环境线上复跑。
   - 推荐使用：`python3 tools/scripts/runtime_review_tool.py replay --question "<原问题>" --expect-route text2sql_or_sql_planning`
6. 线上复跑后必须检查：
   - 路由是否正确
   - Runtime 是否真实调用 MC / CK
   - 核心 SQL 是否不再 0 行或至少被护栏拦截
   - `data_agent_query_records` 是否写入每条 SQL
   - `tool_calls` / metadata 是否保留足够审计字段
   - 若 rollout 窗口仍有新旧 pod 混流，优先用 MySQL 证据核验，不依赖 ingress 上的调试接口返回。
7. 最终产物：
   - 当日总报告
   - 失败样本逐条记录
   - MC / CK 补充复核
   - 如有修复，追加线上复跑与落库核验报告

## 线上回归通过标准

通过标准至少满足以下各项：

- `/health` 与 `/api/preflight` 正常。
- 目标问题在线上 test 环境可成功发起。
- 新 trace 路由进入正确 task。
- 新 trace 中存在真实工具执行记录。
- `data_agent_query_records` 中能看到本次请求的结构化 SQL 记录。
- 如果 rollout 尚未清走旧 pod，最终结论以新 session 的 MySQL trace / query_records 为准。
- 若核心 SQL 再次 0 行，最终答案必须明确标记“未形成业务答案”，不能伪装成功。

## Goal 模式建议

如果用户要求 Goal 长执行模式，建议目标：

```text
复核指定日期的 Data Agent Runtime 调用日志，完成 MC/CK live 验证、失败样本诊断、必要的 Runtime 修复、test 环境线上复跑与报告沉淀
```

完成时必须能回答：

- 复核了哪些问题，去重口径是什么。
- MC / CK live probe 是否成功，目标表最新分区是什么。
- 哪些样本是产品口径问题，哪些是 Runtime 问题。
- 是否已经完成本地 E2E 与线上 test 复跑。
- 新 trace / `query_records` 是否形成完整审计证据。
- 是否已经把 replay / 去重入口固化成脚本，而不是继续手工操作。

## 输出格式

最终报告至少写明：

```text
复核日期：
日志范围：
问题去重口径：
MC live probe：
CK live probe：
失败样本与根因：
是否改代码：
本地 E2E 结果：
线上 test 复跑结果：
query_records 落库结果：
仍未修复项：
```
