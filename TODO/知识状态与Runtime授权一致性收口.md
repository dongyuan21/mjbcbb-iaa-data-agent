# 知识状态与 Runtime 授权一致性收口

- 状态：`open`
- 优先级：`P0`
- 门禁：`knowledge-control-plane`
- 当前结论：问题可解决；不能只修两张表的 YAML，必须同时收敛状态语义、唯一权威和 Runtime 读取规则。

## 当前问题

同一张表可能因读取入口不同得到不同授权结果：

```text
普通表卡读取：card.documentation_status = partial → 非 verified
探索注册表：catalog.documentation_status = complete → 映射为 verified
```

当前确认存在漂移的两张 CK 表：

- `shucang_market.tj_ad_revenue_v2`
- `shucang_market.af_cohort_user_acquisition_v2`

Git 历史显示：两张表卡在 2026-06-14 创建时为 `partial`；2026-06-15 的批量 CK 结构治理提交 `d1d6cdc2` 将 catalog 项提升为 `complete`，但表卡头部未同步。现有表卡门禁只校验 FQN，不校验状态，因而没有阻止漂移。

## 根因

1. catalog 与表卡重复保存 `documentation_status`，没有唯一权威。
2. `documentation_status` 同时承担“文档完整度”“可生成 SQL”“verified 可信度”等不同语义。
3. exploration registry 只读 catalog，并执行 `complete → verified` 的有损归一化。
4. 普通检索和探索检索没有共享同一套状态解析与 fail-closed 门禁。
5. 质量脚本未校验 catalog/card 状态相等或合法映射。

## 收口决策

### 最小兼容方案

1. 表卡成为状态权威；catalog 只做索引投影，不再独立决定授权状态。
2. 在当前 vocabulary 下显式区分：
   - `partial`：schema/线索可读，不得作为默认执行授权；
   - `complete`：L2 `agent_queryable`，允许受 DataContract 和只读 guard 约束的查询；
   - `partial_verified` / `verified`：经过小窗口、join/对账或 owner 确认，可承担更高置信证据角色；
   - `deprecated_stale` / `stub` / `design_candidate`：按既有边界拒绝或仅作候选。
3. Runtime 内部不得再把 `complete` 无条件重命名成 `verified`；如需兼容，输出独立的 `queryability_level`，保留原始 `documentation_status`。
4. exploration registry 加载 catalog 项后必须读取对应表卡，状态缺失、冲突、路径越界或未知枚举一律 fail closed。

若后续确认“文档完整度”和“证据可信度”必须独立演进，再新增显式 `trust_status`；在 schema 和迁移完成前，不允许靠隐式约定区分两个同名字段。

## 实施步骤

- [ ] 为 documentation / queryability / evidence trust 建立唯一状态映射和类型测试。
- [ ] 让 `exploration_asset_registry.py` 从表卡取得权威状态，并保留 catalog/card 原始状态供审计。
- [ ] 修改 `check_table_card_quality.py`：catalog/card 状态冲突升级为 hard error；若允许映射，映射必须在单一配置中显式声明。
- [ ] 修改 catalog rebuild：状态从表卡生成，禁止手工双写后静默漂移。
- [ ] 对上述两张 CK 表重新核对证据后决定保持 `partial` 还是晋升；不得为了门禁一致直接改成 `complete`。
- [ ] 增加普通检索、探索检索、DataContractView 和模型 SQL 授权的交叉测试。
- [ ] 检查所有 179 张表卡，确认同一资产在所有入口得到相同的 queryability / trust 判断。

## 必测场景

1. catalog=`complete`、card=`partial`：构建 registry 必须拒绝或报硬错误，不能升级为 verified。
2. catalog/card 均 `complete`：允许生成受限 DataContractView，但审计状态不得伪装成 L3 verified。
3. card=`verified`：普通与探索入口得到同一 trust 状态和同一 content hash / registry revision。
4. 未知状态、缺表卡、catalog 路径指错、状态漂移：全部 fail closed。
5. catalog rebuild 前后逐字节稳定；无关表不得发生状态变化。

## 验证命令

```bash
python3 tools/scripts/check_table_card_quality.py
python3 tools/scripts/check_agent_retrieval_map.py
runtime/backend/.venv/bin/python -m pytest -q \
  runtime/backend/tests/test_retrieval_policy.py \
  runtime/backend/tests/test_exploration_mode.py \
  runtime/backend/tests/test_data_contract_view.py \
  runtime/backend/tests/test_data_contract_evidence.py
```

影响语义模型或默认召回时，再运行 semantic build / composer 和 Agent regression；实时数据可信度仍需 MC/CK probe 单独证明。

## 完成定义

- catalog 不再是独立授权权威，同一表在普通检索、探索检索和 SQL binding 中的状态一致。
- 两张已知漂移表完成基于证据的裁决，且全库状态一致性门禁为 0 error。
- `complete`、`agent_queryable`、`verified` 的含义在代码、表卡标准、测试和审计投影中一致。
- 任一状态漂移都会在 CI 中硬失败，不能等到线上探索时才暴露。
