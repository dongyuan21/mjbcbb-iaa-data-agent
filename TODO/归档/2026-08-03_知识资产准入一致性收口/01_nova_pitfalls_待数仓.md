# 01 · nova/realtime 5 表缺 known_pitfalls（待数仓）

> 对象：**数仓团队**（非 DA）。状态：待回话。
> 2026-08-02 复核：`check_table_card_quality.py` 仍精确报告以下 5 张，未新增、未减少；本轮只补闭环协议，不凭推测写入表卡。

## 与知识资产准入一致性收口的关系

这 5 张卡纳入“知识资产准入一致性”统一治理，但**不是**已确认的 catalog/card 授权级漂移：当前逐张核对结果为 4 张 `card=complete` 且 `catalog=complete`，1 张 realtime 卡 `card=partial` 且 `catalog=partial`。它们的问题是表卡质量缺少 `known_pitfalls`，不是两个入口给出了不同状态。

统一收口后应有两个独立结果，不能互相替代：

1. **状态与授权门禁**：表卡为 `documentation_status` 的权威来源，catalog 只作投影；catalog/card 冲突必须 hard fail，Runtime 不得把 `complete` 重命名为 `verified`。
2. **质量与证据门禁**：`known_pitfalls` 缺失继续以 `known_pitfalls_pending_human_confirmation` 报告，并进入表卡补全队列；它不得被脚本悄悄改写成 `partial`、`verified` 或任何新的授权/可信度等级。

因此，本 TODO 的完成并不等于状态漂移修复完成；反过来，状态一致也不等于这 5 张卡已经具备数仓确认的隐性口径知识。需要分别验收。

## 缺口

下列 5 张表的卡片 `known_pitfalls` 为空，缺"口径陷阱/反直觉点"。门禁报为 `known_pitfalls_pending_human_confirmation`（质量缺口，非硬错误），闭环后该分类的数量应从 5 降为 0。

| # | 表 | 备注 |
|---|---|---|
| 1 | `dim_nova_collection_all_user_ha` | |
| 2 | `dim_nova_collection_all_user_label_ha` | |
| 3 | `dwd_nova_collection_gp_white_event_unique_data_hi` | |
| 4 | `dwd_nova_collection_ios_white_event_unique_data_hi` | |
| 5 | `dwd_block_blast_ios_white_event_realtime_hi` | realtime，schema 借 offline_di，`dwd` project 不可达 |

## 证据与验证矩阵

以下问题是**待验证问题**，不是已确认 pitfall。只有取得对应证据后才能写入表卡。

| 表 | 优先确认问题 | 最低证据 |
|---|---|---|
| `dim_nova_collection_all_user_ha` | 小时快照是否全量覆盖；同一 `distinct_id` 是否可能多行；字段单位、默认值、空值和回补规则 | 生产加工 SQL / owner 说明 + 小窗口重复度、空值率、关键字段分布 |
| `dim_nova_collection_all_user_label_ha` | 标签生成窗口、覆盖率、未知值、回溯更新；标签名称与实际业务分组是否一致 | 标签生成逻辑 / owner 说明 + 小窗口基数与空值分布 |
| `dwd_nova_collection_gp_white_event_unique_data_hi` | `unique` 的去重键和去重窗口；GP 与 iOS 的事件名、时间和字段映射是否对齐 | 生产加工 SQL / DDL + 同窗口去重前后或唯一键验证 + 跨端字段对照 |
| `dwd_nova_collection_ios_white_event_unique_data_hi` | `unique` 的去重键和去重窗口；iOS 特有字段、隐私和事件时间语义 | 生产加工 SQL / DDL + 小窗口重复度、晚到数据和关键字段验证 |
| `dwd_block_blast_ios_white_event_realtime_hi` | realtime 与 offline 的覆盖、延迟、回补和字段差异；借用 schema 是否可能漂移 | realtime/offline 生产 SQL 或 owner 说明 + 同窗口字段、行数、延迟对照 |

通用验证边界：

- DDL / PyODPS schema 只能证明结构，不能单独证明语义型 pitfall。
- 数据能自证的异常必须使用小窗口聚合，不输出 `distinct_id`、设备 ID 或用户级明细。
- 语义、去重、回补和跨端差异若证据不足，继续保留 `needs_owner_confirmation`，不得为了清门禁编写结论。
- 当前 freshness 只能由实时 MaxCompute probe 证明；旧 snapshot 不作为回填依据。

## 为什么机器补不了

pitfalls 装的是"DDL 注释说不清甚至说错"的坑（样板：BB 的 `best_combo_hi` 是标记非总次数、`game_time` 汇总要 ÷60、`casino_revenue` BB 常年为 0、`wide_ha` 覆盖率 73–82%）。这类是维护过表的人才知道的隐性知识，schema 推不出。**为凑字段硬编 = 污染**，故留空等人。

> 注：少数"数据能自证"的坑（某列常年 0/null、基数异常）agent 可探测补充；但语义型坑必须数仓给。

## 沟通话术

请数仓同学就下列表给"反直觉/易错点"，有就写、没有就明确"无已知坑"：

1. `dim_nova_collection_all_user_ha` — Nova 用户属性小时快照，114 个字段，grain 是 `distinct_id × dt × hour`。有没有字段含义和名字不一致、单位需要转换、或者常年为空/为零的坑？
2. `dim_nova_collection_all_user_label_ha` — Nova 用户标签小时快照，25 个字段。标签字段（如 `media_source_group`、`country_group`、`layertype0626`）有没有"看名字以为是 X 但实际是 Y"的情况？
3. `dwd_nova_collection_gp_white_event_unique_data_hi` — Nova GP 白名单事件。与 `_ios_` 表的字段映射是否完全对齐？`event_name` 是否跨端一致？
4. `dwd_nova_collection_ios_white_event_unique_data_hi` — Nova iOS 白名单事件。同上。
5. `dwd_block_blast_ios_white_event_realtime_hi` — BB iOS 实时事件，schema 借 offline_di，project `dwd` 不可达。realtime 与 offline 的行覆盖、延迟、字段是否有不一致的坑？

参照已有 BB 系卡 `known_pitfalls` 的写法（`id` / `field` / `issue`），每张给几条；确认无坑的标"无已知坑"即可。

## 期望输出

每张表：单位/口径陷阱、与同源表的差异、字段注释错误项；或确认"无已知坑"。

推荐参照资产：对应 5 张 `ai_hive/agent_knowledge/tables/*.yaml`。

## 拿到答复后 agent 做什么

1. 先按 `skills/table-intake/SKILL.md` 验证 MaxCompute 连通性，并对目标表做 PyODPS schema、最新分区和必要的小窗口聚合 probe。
2. 把已取得证据的坑写进对应 `ai_hive/agent_knowledge/tables/*.yaml` 的 `known_pitfalls`，沿用 `id` / `field` / `issue`，并附 evidence / confirmation 来源。
3. 若数仓明确确认“无已知坑”，记录确认人、日期和范围；不要仅写一个无法追溯的空数组。
4. 运行 `python3 tools/scripts/rebuild_ai_hive_catalog.py`，确认 catalog 未产生无关漂移。
5. 运行 `python3 tools/scripts/check_table_card_quality.py` 和 `python3 tools/scripts/check_agent_retrieval_map.py`：硬错误为 0、没有新增 warning，且 `known_pitfalls_pending_human_confirmation` 从 5 降为 0。
6. 影响高频问答、join 或指标语义时，再运行 semantic build / composer 和 `python3 eval/agent_regression/run_regression.py`；若只因 freshness 退出 2，保留 blocker，不伪造 PASS。
7. 检查 5 张卡片的 `last_verified`、source_docs/source_notes 和实际证据日期同步更新；完成后删除本 TODO，不保留历史验收报告。

## 完成定义

- 五张表均有可追溯的 `known_pitfalls`，或有数仓明确确认的“无已知坑”记录。
- 所有结论能追溯到生产 SQL、owner/数仓确认或脱敏小窗口验证；没有由字段名猜出的语义。
- 表卡质量门禁不再报告这 5 个待确认缺口，且没有引入新的 hard error / warning。
- 回归结果和实时 freshness 结果分开报告；未验证的线上事实仍标未验证。
