# ai_hive 待回填（等外部确认后由 agent 回填）

本文件夹专门挂 **ai_hive 知识库里"机器补不了、必须等人确认"的缺口**。区别于：

- `bugfix_doc/`：已完成的治理记录
- 原 `TODO/下周给DA的问题.md`（已于 2026-07-14 归档）：曾用于挂 DA 的完整问题清单（DA-25 等），已处理结论见 `knowledge/agent_knowledge/policies/DA问题已处理结论_20260628.md`
- 本文件夹：**等回话 → agent 回填 → 验证**的闭环跟踪

## 闭环规则

每项：① 缺口是什么 ② 为什么机器补不了（必须人）③ 问题已发给谁 ④ 拿到答复后 agent 回填到哪、怎么验证。
**拿到答复前不自行编造**（pitfalls 不硬编、口径不替业务拍板）。

## 当前待办

| 文件 | 缺口 | 对象 | 状态 |
|---|---|---|---|
| `02_口径签字_待业务与DA.md` | organic KPI / campaign TCPA / activation_di 去重（口径决策记录仍 `needs_decision`；activation example 仍 `confidence: medium`） | 业务 + DA | 待回话 |
| `03_素材生产总表_待确认.md` | MC 素材生产总表 7 项 | owner / DA | 待确认 |
| `04_素材三表_待确认.md` | MC 素材三表 6 项（表卡仍回链） | owner / DA | 待确认 |

## 已自动闭环（不在此跟踪，仅备注）

- Nova/realtime 5 张表的 `known_pitfalls`：已基于生产血缘、表卡和可访问源表的分区探测回填；realtime 无访问权的边界仍明确保留为 `partial`，质量缺口 `5 → 0`，历史任务见 `../归档/2026-08-03_知识资产准入一致性收口/`。
- 5 张 P0 表 example_queries：已从 口径决策记录 派生 + 在线实跑验证回填（commit b285701），DA 仅需 review 边界（见 DA-25）。
- PII 护栏 JSON 内嵌盲区：属"执行层拦截"后续工程话题，记在 `bugfix_doc/20260615_ai_hive_PII护栏问题.md` §四，不在本文件夹。
