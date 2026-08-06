# 2026-08-03 知识资产准入一致性收口

> 状态：`archived / not_current_fact / denied_for_default_retrieval`

本批次归档已完成的 Nova/realtime 5 张表卡 `known_pitfalls` 回填任务。可复用的单表风险说明已写入对应 `ai_hive/agent_knowledge/tables/*.yaml`；归档文件只保留原始待办、证据矩阵和完成过程，不作为运行时授权或业务事实来源。

| 归档项 | 完成事实 | 当前权威位置 |
|---|---|---|
| `01_nova_pitfalls_待数仓.md` | 5 张卡均已写入可追溯 pitfalls；质量门禁不再报告该分类 | 对应 `ai_hive/agent_knowledge/tables/*.yaml` |

## 完成边界

- `dim_nova_collection_all_user_ha` 与 `dim_nova_collection_all_user_label_ha`：确认其小时快照边界，禁止跨小时累计用户。
- Nova GP/iOS unique 视图：确认其多离线分期 `UNION ALL` 与分期覆盖边界；具体去重键仍未取得生产定义，已作为运行时限制写入表卡，不伪装为已确认语义。
- BB iOS realtime：确认当前 schema 仅由离线分支等价推断，实时项目访问、覆盖率、延迟与回补仍不能由本归档证明；表卡继续保持 `partial`。

运行时状态授权的代码收口另见 `TODO/知识状态与Runtime授权一致性收口.md`，其 Test/Prod 入口验收仍是活跃发布事项。
