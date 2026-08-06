# UA 决策沉淀 Runtime 接入待办

- 状态：`partial_implemented / runtime_mainline_not_integrated`
- 优先级：`P1`
- 更新：2026-08-02
- 已完成来源：DiD 基准、app/country 分层、`ua_country_effect`、`ua_predict`、`ua_rule_tree` 服务与工具市场登记
- 架构：[`Runtime 控制面架构`](../data_agent_plan/Runtime控制面架构/README.md)
- 安全前置：[`UA 无认证旁路上线前收口`](UA无认证旁路上线前收口.md)

## 当前事实

UA 数值知识和三个只读能力已经存在：

- `knowledge/agent_knowledge/report_knowledge/UA操作效应DiD基准表.yaml`；
- `runtime/backend/app/services/tool_registry.py` 的工具市场描述；
- `/api/ua/country-effect`、`/api/ua/predict`、`/api/ua/rule-tree` 及其内部 service/script。

但当前 Python `MinimalToolLoop` 使用的是 `runtime_tool_registry.py` 的进程内受治理工具集合，里面没有上述 UA 工具。`task_routes` 中存在 `external_tool_refs` 只代表能力登记，不会自动让真实回答调用这些工具。因此不能宣称“UA 工具已接入 Data Agent 主链”。

历史方案中的 Runtime prefetch、Runtime 自调用 HTTP、从 CK 拉全量 campaign 列表后把三份结果预注入 prompt，不再符合当前单一 Runtime、按需工具调用和 evidence binding 架构，予以取消。

## 当前实施方案

### P1-A · 受治理工具接线

- [ ] 在 `runtime_tool_registry.py` 增加进程内 UA handler，直接调用受控 service，不经匿名 HTTP 自调用。
- [ ] 为三种工具定义严格参数 schema、超时、错误码、model-visible payload 上限和 safe audit projection。
- [ ] 增加 Runtime-owned capability resolver：仅对命中的只读投放/UA route 开放对应工具；不得把 UA 工具加入所有问题的全局可见集合。
- [ ] `campaign/country/app_group` 从 QuestionContract/澄清结果取得；模糊多匹配必须进入 clarification，不静默猜 campaign。

### P1-B · 证据与终态

- [ ] UA 输出绑定 tool execution id、模型/规则/数据 revision、freshness 和 `observational_causal` 边界。
- [ ] Claim attribution 只能把 UA 工具结果支持到对应 claim；预测概率、DiD 和规则树不得覆盖 ROI/消耗等未查询事实。
- [ ] P3 `complete/partial/incomplete` 与工具失败、无匹配、多匹配、stale 和低置信状态一致。
- [ ] 回答只输出预警、历史效应和 `needs_decision`，禁止最终停投、放量、预算或国家排除指令。

### P1-C · 验证

- [ ] 单测覆盖唯一 campaign、多匹配反问、无数据、低置信、工具超时、安全投影和 route 不可见负例。
- [ ] Test 用新 session、单次无重试覆盖 country-effect、predict、rule-tree 各一条；对账 QuestionContract、tool execution、QueryRecord/trace、claim coverage 和用户文本。
- [ ] 正式发布前先完成 UA 接口认证收口；开发期匿名 API 可存在，但不能成为 Runtime 主链的认证设计。

### P1-D · 资产完整性

- [x] `ua_decision_ddl.sql` 已在 `da_assets/index.yaml` 登记为 `archived_excluded` 的 raw DDL 审计资产；它含写入性 DDL，不能进入只读 Agent 召回或晋升链。
- [x] 同目录 4 个 DDL/load JSON 已作为 raw DDL 的受治理执行证据登记，并以 `source_assets` 回链；它们不再被误解为可执行候选 SQL。
- [x] 已重跑 `check_asset_eval_integrity.py`；5 个 `candidate 未索引` 硬错误必须保持为零，不能靠删除验证证据或放宽门禁取得 PASS。

## 完成定义

- 真实 API/SSE/Worker 主链可按 route 和合同调用 UA 工具，未命中 route 的问题看不到这些能力。
- 工具结果、claim attribution、P3 terminal 和用户输出可审计且一致。
- 匿名 HTTP 不是内部调用依赖；Prod 入口已完成认证、限流和审计。
- UA DDL 及执行结果的资产类型、索引和历史证据回链一致，资产完整性门禁通过。
- 产品仍是只读分析与预警，不获得广告平台写权限或最终投放决策权。
