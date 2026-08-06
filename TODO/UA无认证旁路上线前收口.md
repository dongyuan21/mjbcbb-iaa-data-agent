# UA 无认证旁路上线前收口

- 状态：`open`
- 优先级：`P0`
- 门禁：`formal_release`
- 适用范围：Data Agent / UA 能力进入正式生产环境或暴露到正式 Ingress 之前
- 当前决策：开发期为联调便利可暂时保留；不得将当前形态视为生产安全设计，正式上线前必须完成收口。

## 当前待收口范围

- `/api/ua/country-effect`
- `/api/ua/country-effect/rebuild`
- `/api/ua/predict`、`/api/ua/predict/manual`
- `/api/ua/rule-tree`、`/api/ua/rule-tree/manual`、`/api/ua/rule-tree/rules`

当前源码将这些接口标为“不走 SSO”。`country-effect` 查询读缓存，`rebuild` 读 MC / CK 并写效应缓存，`predict/rule-tree` 的自动链读 CK，manual/rules 为本地规则输入。该实现适合作为开发期便捷入口，不应直接沿用到正式生产。

## 上线前验收条件

1. 生产环境默认关闭开发旁路；未认证请求返回 `401/403`，或接口在正式 Ingress 中不可达。
2. 明确认证模型：人机访问复用 SSO；如需服务身份，另行设计正式环境 service-to-service auth，不得把当前仅 test/local 的 machine auth 直接扩到 prod，也不得依赖“调用方知道 URL 但不会滥用”。
3. 收紧 CORS 与来源边界，不再以全域跨站访问作为 UA 接口的默认生产配置。
4. `rebuild` 改为受控异步任务或运维任务，具备并发互斥、频率限制、超时、审计和失败终态，不在 FastAPI event loop 内同步执行长查询。
5. MC / CK 读取必须经过 `runtime/tools/data_query.py`，或经过等价的服务端只读、表级授权、PII、scan window、审计与结果上限控制；正式链路不得由公网参数直接驱动本地 helper/subprocess SQL。
6. 缓存写入路径、镜像权限和多副本一致性经过明确设计；不得把单 Pod 本地文件写入当作生产权威状态。
7. 保持产品边界：UA 输出只提供预测、预警和证据，不执行停投、放量、预算或广告平台写操作。
8. 增加生产配置测试和发布 smoke：至少覆盖匿名拒绝、授权成功、限流/互斥、审计记录、错误降级，以及 API / Worker / Freshness 的实际部署边界。

## 关闭条件

以上条件全部具备当前代码、自动化测试和正式环境证据后，删除本 TODO；安全设计和运行约定沉淀到 Runtime 权威文档，不在 TODO 中保留历史验收报告。
