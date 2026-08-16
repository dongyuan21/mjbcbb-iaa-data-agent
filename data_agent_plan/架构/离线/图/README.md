# 离线知识工程 · 直观架构图

易读入库 / 晋升流水线（非运行时控制面细图）。

**标注规范**：图中英文术语统一为「中文（英文）」；仓库路径名（如 `数据资产目录/`、`da_assets/`）保持原样。

| 文件 | 用途 |
|---|---|
| [`一张表怎么入库.excalidraw`](一张表怎么入库.excalidraw) / [`.png`](一张表怎么入库.png) | 表名 → 数据资产目录 → 目录 (catalog) → 注册表 (Registry) → 架构层 L3 可读 |
| [`一份知识怎么入库.excalidraw`](一份知识怎么入库.excalidraw) / [`.png`](一份知识怎么入库.png) | 文档 (docx) → 原始归档 (raw) → 抽取 → 校验 → 权威映射 (authority) 挂切面 |
| [`一条SQL怎么晋升.excalidraw`](一条SQL怎么晋升.excalidraw) / [`.png`](一条SQL怎么晋升.png) | 候选 SQL → 门禁 A/B/C → 已验证 (verified) → 挂切面 → 架构层 L3 |

导出 PNG（源图变更后）：

```bash
bash tools/scripts/export_offline_diagrams.sh
```

父目录：[`../README.md`](../README.md)
