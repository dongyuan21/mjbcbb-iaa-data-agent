# bugfix_doc

工程级"问题 → 修复 → 验证"的 bugfix 记录区(区别于 `TODO/` 的近期待办、`da_assets/decision_cases/` 的投放决策复盘)。

## 命名约定

```text
YYYYMMDD<主题>.md      # 例:20260615_ai_ck_结构治理问题.md
```

## 每篇应包含

- 问题概览(编号 / 级别 / 证据 / 状态)
- 真理源与影响范围说明
- 整改方案与执行结果
- 验收(回归 / 校验)
- 遗留观察项与待 DA/业务拍板项

## 当前记录

| 文件 | 主题 |
|---|---|
| `20260620_知识层收敛与语义契约归并记录.md` | 知识层收敛:从 ai_hive / ai_ck 三层划分到 semantic_contract 归并 knowledge,明确表卡、政策、跨表语义和审计材料归属 |
| `20260629_长SQL追问流式传输失败重大问题.md` | 长 SQL 追问导致 GET EventSource URL 超长，触发流式链路 chunk/分隔符限制；改为 POST JSON 建流并手动解析 SSE |
| `20260630_PI同题不同用户回答不一致重大问题.md` | 同题 fingerprint 下 002452/002494 回答不一致：非用户歧视，系 PI 非确定性+熔断；已落地 verified SQL 与回归用例 |
| `20260630_PI同题稳定性_D30渠道国家Top20集中度.md` | 同上问题的工程改进项、口径确认与 MC 验证记录 |
| `20260615_ai_ck_结构治理问题.md` | ai_ck 结构治理:分层、深卡补全、ad_revenue 纳入、版本 canonical 自动探测、agent 友好性 P0/P1 |
| `20260615_ai_hive_PII护栏问题.md` | ai_hive PII 护栏:标注覆盖不足/真理源打架/语义二元化过粗,canonical 字典+自动盖章方案(待拍板) |
| `20260712_latest报告与生成产物本地依赖问题.md` | latest 回归与评估产物被本地忽略、下游流程隐式依赖的问题，以及后续可复现性治理方向 |
| `20260712_配置层与运行层割裂问题.md` | 路由配置已声明资产边界但运行时未完全强制执行的架构与安全边界问题 |
| `20260715_PI_RPC桥接MC查询timeout错位与query_id缺失.md` | PI RPC 四层查询链超时阶梯错位、ODPS instance_id 丢失、logview token 脱敏与可观测性修复 |
