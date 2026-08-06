# TODO — 当前待办入口

> 更新：2026-08-02
>
> 本目录只保留尚未闭环、需要取证、需要外部确认或需要发布验证的事项。它不是事实库，也不进入 Runtime 默认事实召回。

## 2026-08-02 全量复核结论

- 已逐份复核原目录的 100 个文件（其中 97 个 Markdown）。
- 61 个原文件因整份完成、被替代或架构失效进入本次归档批次；没有物理删除。
- 4 个仍有效的 Runtime 架构原文件从 TODO 提升到 `data_agent_plan/Runtime控制面架构/`，并新增当前架构索引。
- Runtime 时代的探索方案保留为 snapshot，现行方案已按 Python `MinimalToolLoop` 重写。
- 其余文档按当前源码和治理边界做了局部修订；当前活跃区共 38 个 Markdown，以下分类是唯一入口。

## P0 与正式发布门

| 文件 | 当前缺口 |
|---|---|
| [`工程评审后续收口总表.md`](工程评审后续收口总表.md) | 本次客观工程评审提出的 5 项未来事项总入口 |
| [`UA无认证旁路上线前收口.md`](UA无认证旁路上线前收口.md) | UA 匿名接口在正式 Ingress 前完成认证、限流、审计和 rebuild 隔离 |
| [`知识状态与Runtime授权一致性收口.md`](知识状态与Runtime授权一致性收口.md) | 表卡、catalog 和 Runtime eligibility 状态语义统一 |
| [`证据覆盖与终态裁决生产启用收口.md`](证据覆盖与终态裁决生产启用收口.md) | required claim 的默认终态裁决/证据策略、Prod 放量和回滚 |
| [`Runtime发布溯源与生产验收待办.md`](Runtime发布溯源与生产验收待办.md) | 不可变构建来源、三服务版本一致性和 Prod canary |
| [`凭据轮换与生产密钥治理.md`](凭据轮换与生产密钥治理.md) | 核验历史 gateway key 状态；必要时无回显轮换和三服务验证 |
| [`多轮对话建设.md`](多轮对话建设.md) | 结构化状态真实提交链、CAS/恢复和长会话压缩 |

## Runtime、检索与运营质量

| 文件 | 当前缺口 |
|---|---|
| [`Runtime语义质量晋级待办.md`](Runtime语义质量晋级待办.md) | B1 protected fact 漏失仍未过门；B2/B3 Semantic 阻塞 |
| [`Runtime SLA证据通道建设.md`](<Runtime SLA证据通道建设.md>) | 本地端点已有，live evidence、heartbeat 和连续观测仍开 |
| [`探索型异步Agent实施.md`](探索型异步Agent实施.md) | 实现已齐，真实 off/on A/B、盲评和灰度尚未完成 |
| [`上下文工程与Runtime下一步规划.md`](上下文工程与Runtime下一步规划.md) | 当前只保留 bootstrap、检索切片和 Runtime 压缩接线 |
| [`KV缓存命中与压缩关系观测计划.md`](KV缓存命中与压缩关系观测计划.md) | 模板已齐，等待真实采集和 A/B 结论 |
| [`低置信度反问协议TODO.md`](低置信度反问协议TODO.md) | shadow 有实现，自然样本和 enforce 准入不足 |
| [`路由质量监控与迭代闭环.md`](路由质量监控与迭代闭环.md) | 周报/脚本已有，人工 review 与迭代节奏未运行 |

## 数据、语义与表卡

| 文件 | 当前缺口 |
|---|---|
| [`语义层待补清单.md`](语义层待补清单.md) | 只记录未拍板口径和未闭环语义缺口 |
| [`SQL写作链候选表准入积压清单.md`](SQL写作链候选表准入积压清单.md) | 44 张有效候选表仍未入 catalog；占位 `table_name` 不计 |
| [`素材与变现verified_sql待补.md`](素材与变现verified_sql待补.md) | 两条分析 route 的 verified SQL 覆盖偏薄 |
| [`ASA表卡补columns段待办.md`](ASA表卡补columns段待办.md) | ASA columns 和 spend 字段漂移治理 |
| [`DA-22_media_country_roi_v2_v3_停用决策.md`](DA-22_media_country_roi_v2_v3_停用决策.md) | v2/v3 canonical 与 v2 停用待 DA 决策 |
| [`ads_market_roi_cohort_sdk_multidim_ETL血缘待补.md`](ads_market_roi_cohort_sdk_multidim_ETL血缘待补.md) | 宽表生产 ETL SQL 和 owner 证据缺失 |
| [`ai_hive待回填/`](ai_hive待回填/README.md) | 必须等数仓/业务/DA 回答的其余表卡缺口；Nova/realtime 5 张 pitfalls 已归档 |
| [`ai_ck待回填/`](ai_ck待回填/README.md) | 两组素材 CK 表的人确认项；旧 schema 漂移单已归档 |
| [`投放看板知识沉淀待补问题.md`](投放看板知识沉淀待补问题.md) | 素材效能与 Campaign Overview 的未决口径/链路 |
| [`数据底座维护Harness.md`](数据底座维护Harness.md) | 深卡/join/PII 高风险案例和迁正式 runbook |
| [`freshness刷新自动化计划.md`](freshness刷新自动化计划.md) | 共享环境定时、告警、MC 定时和连续留证 |

## 只读产品能力

| 文件 | 当前缺口 |
|---|---|
| [`工具建设待办.md`](工具建设待办.md) | 跨工具总索引；只保留仍开项 |
| [`平台操作记录与素材能力待办.md`](平台操作记录与素材能力待办.md) | Meta/AppLovin change log 表、频率和三平台生产指标 |
| [`ROI360月度人员环比工具.md`](ROI360月度人员环比工具.md) | CK 对账、钉钉和对话内调用 |
| [`红黄线定时推送与Trace落库计划.md`](红黄线定时推送与Trace落库计划.md) | 调度拍板、真实钉钉、DB/live 和连续 3 天验收 |
| [`UA决策沉淀Agent接入方案.md`](UA决策沉淀Agent接入方案.md) | 将现有 UA 工具按当前 Runtime 治理接入，并收口 5 个未索引 UA DDL/执行证据资产 |
| [`UA模型特征扩展待办_素材与国家级ROI.md`](UA模型特征扩展待办_素材与国家级ROI.md) | 样本量达到门槛后再扩 27 维特征 |

## 归档

已完成、整份被替代或不再适合作为活跃待办的文件移到 [`归档/`](归档/README.md)。归档只用于追溯，不是当前事实或默认召回来源。

## 维护规则

- 需要 DA/UA、业务 owner 或用户拍板的问题标 `needs_decision`，不要替人决定。
- 已确认口径迁入正式知识、表卡或语义合同；SQL、SOP、case 分别迁入 `verified_sql`、`analysis_sop`、`decision_cases`。
- 整份完成或被替代且仍有审计价值时归档；纯重复、无审计价值的临时记录才删除。
- 任一“已完成”必须说明是代码存在、单测通过、主链接入、Test 验证还是 Prod 验证，不能混写。
- 不把缺少自动停投、放量、改预算或广告平台写操作列为缺陷；本产品只读分析与预警。
