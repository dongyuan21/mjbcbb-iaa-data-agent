# 架构图 · Excalidraw

本目录是 [`../当前系统架构图.md`](../当前系统架构图.md) 的正文插图。

> 更新：2026-08-02。图1 已改为展示视图；图5、图6 已同步 Python Runtime、DataContractView 与 SQL guard；图8 为白盒主链。图2 / 图3 / 图4 / 图7 的知识与评测语义未变。归属话题：[`../README.md`](../README.md)。

| 文件 | 对应章节 |
|---|---|
| 图1-系统全景四层栈 | §1 |
| 图2-知识基座三层模型 | §2 |
| 图3-知识晋升通道 | §3 |
| 图4-控制面按需加载 | §4 |
| 图5-运行层问答主路径 | §5 |
| 图6-默认off主路径 | §5.2 |
| 图7-评测闭环三线评测 | §6 |
| 图8-一次请求的白盒主链 | [`../从一个问题看懂Data Agent.md`](../从一个问题看懂Data%20Agent.md) |

约定：

- `.png` 嵌入主文档；`.excalidraw` 为可编辑源（导入 [excalidraw.com](https://excalidraw.com)）。
- 修改 `.excalidraw` 后，用 `bash 导出架构图.sh` 重建本目录全部 PNG。脚本依赖 Excalidraw 技能的 renderer；其他环境通过 `EXCALIDRAW_RENDERER_DIR` 指向该目录。
- 原 mermaid 源备份在 [`../当前系统架构图-mermaid备份.md`](../当前系统架构图-mermaid备份.md)。
- 架构语义以 `当前系统架构图.md` 为准；改图后应同步核对 MD 中对应节的说明文字。
- 不在图中固化会自然过期的资产数量、用例数、上下文体积等运行快照。
- 运行层物理执行路径以仓内 `runtime/README.md` 为准：单一 Python Runtime。
