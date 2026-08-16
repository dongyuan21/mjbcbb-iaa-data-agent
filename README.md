# 数据代理公开资料

本仓库是从私有工程中按白名单导出的公开材料，包含架构设计、方法论文档、可编辑架构图和问题修复复盘。

所有组织、产品、内部平台、域名、包名、地址和提交标识均已替换；生产 SQL、表卡、metadata、原始数据、历史数据文件、凭证与内部接口不在仓库中。

## 目录

- [`showoff/`](showoff/)：面向读者的架构与能力说明。
- [`data_agent_plan/架构/`](data_agent_plan/%E6%9E%B6%E6%9E%84/)：在线与离线架构设计。
- [`da_assets/`](da_assets/)：可复用的方法论与操作规范。
- [`bugfix_doc/`](bugfix_doc/)：重大问题、修复与验证复盘。

## 图的更新

图以 `.excalidraw` 为可编辑源；修改源文件后运行：

```bash
npm install
ruby scripts/重新导出架构图.rb
ruby scripts/校验公开快照.rb
```

图像只应由当前已脱敏源重新导出，不应复用私有工程中的旧 PNG。
