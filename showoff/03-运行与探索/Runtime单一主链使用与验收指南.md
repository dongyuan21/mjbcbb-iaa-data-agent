# Runtime 单一主链使用与验收指南

> 面向：产品、分析师、值班工程师和评审者。
> 当前形态：固定 slim prior、business prompt、受治理知识工具与查询工具；不存在 off/shadow/on 模式切换。
> 核心边界：只读分析与预警，不自动修改投放、预算或广告平台状态。

## 日常使用

用户不需要选择运行模式。提问时尽量明确产品/包体、国家、媒体、指标和时间窗口；
Runtime 负责路由、受控知识读取、DataContract binding、SQL 授权、失败恢复和终态裁决。

- `missing_source`、`incomplete` 或 `needs_decision` 表示证据不足或需要人工判断；
- route/prior 只帮助检索，不授权资产、SQL 或完成状态；
- `SELECT 1`、分区 probe 和 freshness 只能证明连通/覆盖，不能替代业务结果；
- 禁止要求系统执行停投、放量、改预算等写操作。

## Test 验收顺序

1. Worker、API、Freshness 使用同一完整 source revision，依次核对 task commit、clone commit、image tag、Pod 状态和重启数。
2. `/health`、`/readyz`、machine-auth 白名单边界和 `/api/models` 使用安全投影核验；不输出凭据或环境变量正文。
3. 需要业务链路证据时，只运行一次有明确目的的 durable smoke，记录 job/trace/event 的 ID、enum、count、hash 和有限 reason code。
4. Registry、policy manifest、prompt template 和 tool manifest 必须由 Worker 首次 claim 固定；retry 只能复用同一 snapshot，漂移必须 fail-closed。
5. 模型可见工具由 route policy 和 Runtime Registry 共同收窄；DataContractView、PII 与 SQL guard 不因测试或失败而放宽。

## 固定题集边界

`eval/exploration_ab/cases.yaml` 保留为历史冻结的业务风险题集，并继续供静态 Registry
校验和 layered human eval 引用。旧 paired off/on runner、mode validator 和双 prompt
结论已经退役；不得用历史 mode hash 或评分冒充当前 Runtime 证据。

## 故障处理

| 现象 | 处理方式 |
|---|---|
| 正文、token、SQL rows 出现在 trace | 停止扩大验证范围，保留安全 run ID，修复持久化投影 |
| Registry、policy 或 asset hash 漂移 | 当前 run fail-closed；不得重试后静默换资产 |
| 预算耗尽或工具拒绝 | 检查 sequence、phase、error code、asset ID；不通过加预算或放宽白名单掩盖 |
| 回答缺源或不完整 | 保留受控终态，补数据源/数据资产目录/owner 证据后再验 |
| 三服务版本不一致 | 标记 deployment drift，按 Worker → API → Freshness 整体重发 |

## 发布原则

- 发布目标 commit 必须已推送；共享脏工作树中的无关文件不得混入提交。
- 默认全服务部署，除非用户明确限定单个服务。
- Test 通过不等于 Prod 通过；Prod 需要独立配置、canary、SLA、回滚和 owner 证据。
- 任何环境都不允许通过模型提示绕过 Runtime 的授权与安全策略。

权威架构与待办见：[`data_agent_plan/架构/在线/横切面/探索型异步Agent架构方案.md`](../../data_agent_plan/架构/在线/横切面/探索型异步Agent架构方案.md)、[`TODO/L3架构线后续待办.md`](../../TODO/L3架构线后续待办.md)。
