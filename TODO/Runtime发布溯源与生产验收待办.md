# Runtime 发布溯源与生产验收待办

- 状态：`open / test_behavior_verified / immutable_build_provenance_pending / production_not_validated`
- 优先级：`P0`
- 更新：2026-08-02
- 架构：[`Runtime 控制面架构`](../data_agent_plan/Runtime控制面架构/README.md)
- 历史证据：[`P0-C 构建版本溯源平台交接`](归档/2026-08-02_过时与已完成事项/Runtime用户问题管理与控制面收敛_历史实施材料/P0_C_构建版本溯源平台交接.md)

## 当前边界

最近一次仓内收口记录证明 P0～P3 在 Test 的业务行为、等待恢复、三服务同源码提交和 health/ready 已通过；它不证明当前 Prod 已启用，也不补足构建与镜像的不可变来源链。`git_commit == clone_commit` 只能证明源码对齐，不能单独证明 API、Worker、Freshness 使用同一不可变构建产物。

## P0 · 构建与发布来源链

- [ ] 构建器在 clone 后自动把实际 resolved 的完整 SHA 写入 OCI label 和 Runtime build metadata；拒绝 `unknown`、短 SHA、手填 SHA、分支名或 image tag 反推。
- [ ] 平台提供不含 Secret 的安全投影，能核对 task commit、clone commit、OCI revision、Runtime build commit 和 image digest。
- [ ] API、Worker、Freshness 三服务的构建/发布关系明确：若平台无法使用同一 digest，必须提供每个镜像由同一 source revision 生成的不可变 provenance，不能继续沿用不可能满足的“不同进程必须同一镜像 digest”字面条件。
- [ ] 任一服务版本、revision、policy/registry 或镜像来源不一致时标 `deployment_drift`，不得宣称整体部署完成。

## P0 · Prod 验收

- [ ] 在 Prod 真实配置下核对认证、QuestionContract/P3 mode、exploration mode、policy/registry revision、health/ready 和服务拓扑。
- [ ] 使用新 session 做单次无重试 canary，分别覆盖完整业务路径和 waiting/resume 路径；Test 证据不得包装成 Prod 证据。
- [ ] canary 只输出安全 identity、enum、count、hash、task/run ID 和 reason code，不导出问题正文、prompt、SQL、rows、构建日志或凭证。
- [ ] 记录整体回滚对象和停止线；回滚必须覆盖 API、Worker、Freshness 的一致版本与配置。

## 与其他 TODO 的关系

- 本文负责“运行的到底是哪份不可变构建”和 Prod 验收。
- [`证据覆盖与终态裁决生产启用收口`](证据覆盖与终态裁决生产启用收口.md)负责 required claim 的默认终态裁决/证据策略与放量。
- [`Runtime SLA 证据通道建设`](Runtime%20SLA证据通道建设.md)负责可持续 SLA 指标和 live 证据通道。

## 完成定义

- 三服务的 source revision、构建产物、运行版本和配置均可由安全平台证据闭环。
- Prod 有当前版本的单次 canary、waiting/resume、SLA 和整体回滚记录。
- 报告明确区分 `source_aligned`、`build_provenance_verified`、`test_verified` 和 `production_verified`。
