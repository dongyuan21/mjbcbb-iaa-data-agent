# 2026-08-02 TODO 清理归档

> 状态：`archived / not_current_fact / denied_for_default_retrieval`
>
> 本批次移动归档 61 个原文件，另增加 2 个架构跳转页以保持历史相对链接可达；移动而非删除，可通过 Git 历史和本目录追溯。

## 整份归档判断

| 归档项 | 原因 | 当前入口 |
|---|---|---|
| `Agent-OS.md` | 概念稿不是可执行 TODO，且“Runtime/Codex/Claude 可替换 Provider”与单一 Runtime 主链裁决冲突 | `data_agent_plan/Runtime控制面架构/` |
| `后续待办.md` | 旧部署 SHA、历史 replay、已完成 POC 和多个现行专项混在一份总表，不能再代表当前状态 | `TODO/README.md`；唯一凭据事项已迁 `TODO/凭据轮换与生产密钥治理.md` |
| `UA决策沉淀DataAgent预警能力建设待办.md` | DiD YAML、app 分层、工具接口和 route 登记已实现；剩余 Runtime 接线另有活跃 TODO | `TODO/UA决策沉淀Agent接入方案.md`、`TODO/UA无认证旁路上线前收口.md` |
| `02_CK_schema漂移待确认.md` | 文件自身已标 `superseded`；当前漂移由 schema 报告和 ASA 专项跟踪 | `TODO/ASA表卡补columns段待办.md` |
| `Runtime用户问题管理与控制面收敛_历史实施材料/` | P0～P3 已完成 Test 收口；目录主要是实施任务书、被替代方案和验收流水，不应继续占活跃 TODO | 架构见 `data_agent_plan/Runtime控制面架构/`；未完成线见 `TODO/Runtime语义质量晋级待办.md`、`TODO/Runtime发布溯源与生产验收待办.md`、`TODO/默认证据闭环与P3生产启用收口.md` |

## 使用边界

- 归档中的 SHA、Test task、session、评测数字只代表文档记录的时间点。
- 任何当前架构、发布状态或业务事实必须回到现行源码、正式知识、当前测试和部署证据验证。
- 不把归档路径加入 task route `first_read`、默认知识 catalog 或 Runtime eligible asset registry。
