# UA 决策行为沉淀批量采集报告

> 日期：2026-07-24

## 采集结果

| 项 | 值 |
|---|---|
| Campaign 数 | 30（Google，6月消耗 Top 30） |
| 时间窗口 | 2026-06-01 ~ 2026-06-30 |
| 成功率 | 30/30 = 100% |
| 操作记录（ua-operates） | 87 条 |
| 备注记录（ua-remarks） | 493 条 |
| Coverage 状态 | 全部 complete，terminal_cursor=True |

## MC 写入结果

| 表 | 行数（dt=2026-06-30） |
|---|---|
| ods_mi_campaign_operation_observation_hi | 94（87新 + 7旧） |
| ods_mi_campaign_remark_observation_hi | 556（493新 + 63旧） |
| 不同 Campaign 数 | 29 |

## 用途

这批数据可供 Phase 3（行为模仿训练）和 Phase 4（Uplift 可行性）使用：
- 87 条操作记录可用于动作分桶统计和训练样本
- 493 条备注记录可用于意图沉淀
- 30 个 Campaign 提供了足够多样的样本

## 非目标

未执行 DDL/DML（只 INSERT INTO 追加）；未部署；未保存 PII。
