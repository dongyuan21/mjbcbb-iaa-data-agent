# 横切面能力规划

> 状态：`active_architecture`（方案级；落地进度以 `TODO/` 为准）
> 归属：[`../README.md`](../README.md) · 架构总夹：[`../../README.md`](../../README.md)

本目录放 Runtime 横切面能力的当前工程设计，以及仍被其他文档引用的退役决策记录。

| 文件 | 用途 | 活待办 |
|---|---|---|
| [`探索型异步Agent架构方案.md`](探索型异步Agent架构方案.md) | Runtime 单一主链；旧 exploration 控制面退役记录 | — |
| [`多轮对话与上下文压缩工程设计.md`](多轮对话与上下文压缩工程设计.md) | 多轮状态、压缩 L0–L4、提交语义；P0 as-built、本地 P1 replay 与 Test 边界 | `TODO/多轮对话建设.md` |
| [`P1-3模型Resolver工程计划.md`](P1-3模型Resolver工程计划.md) | 模型 Resolver 工程计划 | — |
| [`Runtime资源治理与工具编排设计.md`](Runtime资源治理与工具编排设计.md) | provider 调用前的预算准入、阶段化工具面与安全终态设计 | `bugfix_doc/20260809_Runtime主链预算与工具编排质量问题.md` |

不在此放部署 SOP / SLA 证据通道实现说明；以 `runtime/` 权威文档为准。
