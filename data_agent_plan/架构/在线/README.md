# 在线 Runtime

> 状态：`active_architecture`
> 更新：2026-08-08
> 现行实现：Python `DataAgentRuntime + MinimalToolLoop` 单一主链；已退役的 Node 执行器、provider registry 和 PlanProvider 不属于目标架构。

本目录是 **在线 Runtime 控制面** 的逻辑分层、控制权和治理边界入口。

- 整仓总图：[`../README.md`](../README.md)
- 离线对偶：[`../离线/`](../离线/README.md)（入库、晋升、定时刷新；本目录不替代）

## 当前入口

| 文件 | 用途 |
|---|---|
| [`架构分层与冻结边界.md`](架构分层与冻结边界.md) | 六层主链、两类横切面、四种控制权及冻结边界 |
| [`图/README.md`](图/README.md) | 架构图阅读指南；**架构 L / 评测 E** 命名硬规则 |
| [`L2/用户问题控制与澄清设计.md`](L2/用户问题控制与澄清设计.md) | L2 控制流、澄清图、受控 PE、结构化 JSON 协议 |
| [`L2/架构评估与重构建议.md`](L2/架构评估与重构建议.md) | L2 独立评估：`question_control.v2`、五道校验、E1 门槛 |
| [`L2/路由与预处理/`](L2/路由与预处理/README.md) | 输入形态、低置信度 fallback、多问题拆分、监控方案 |
| [`L3/重构决策口径.md`](L3/重构决策口径.md) | L3 知识控制面：D1–D22 已锁定；开放项见 [`TODO/L3架构线后续待办.md`](../../../TODO/L3架构线后续待办.md) |
| [`横切面/`](横切面/) | 多轮压缩、探索型 Agent、Resolver 等跨层能力规划 |

## 评测衔接（不在本目录）

| 文件 | 位置 |
|---|---|
| E1 技术方案 | [`eval/question_control_e1/评测E1技术方案、输入输出与优化路径.md`](../../../eval/question_control_e1/评测E1技术方案、输入输出与优化路径.md) |
| E1 Agent 解读 Prompt | [`eval/question_control_e1/给Agent的E1评测解读Prompt.md`](../../../eval/question_control_e1/给Agent的E1评测解读Prompt.md) |
| L3/E2 审计 Prompt | [`eval/给Agent的L3架构与E2评测讨论Prompt.md`](../../../eval/给Agent的L3架构与E2评测讨论Prompt.md) |
| E↔L 映射说明 | [`图/评测六层与Runtime六层映射说明.md`](图/评测六层与Runtime六层映射说明.md) |

## 状态边界

- 架构边界已冻结，不等于所有能力已在 Prod 启用。
- 历史实施流水已移除；本目录只保留可用于当前设计、实现与验收的架构资料。
- 当前仍开的语义质量、发布溯源、默认证据和多轮状态事项，以 `TODO/README.md` 的活跃清单为准。
- 运行事实以当前源码、测试、部署和 canary 证据为准；本目录不替代上线证明。
