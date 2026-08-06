# TODO · 素材与变现 verified_sql 待补

> 状态：pending
> 创建：2026-07-24
> 触发来源：知识加载健康度审计，发现 material_analysis 和 monetization_performance_analysis 两个外部路由 verified_sql 覆盖偏薄。
> 优先级：P1（不阻塞当前生产，但补充后可提升回答质量）

## 当前状态

| Route | 当前 verified_sql 数量 | 目标 |
|-------|----------------------|------|
| `material_analysis` | 1-2 条（素材 IPM/CPI 快照） | 补到 4-5 条 |
| `monetization_performance_analysis` | 3 条（Day0 ARPU、广告展示、设备资产） | 补到 5-6 条 |

## 建议补充方向

### material_analysis 待补

- [ ] 素材冷启动通过率 & 周期统计
- [ ] 素材生命周期衰减（老素材 IPM/spend 趋势）
- [ ] 设计师维度素材效果汇总
- [ ] 素材 ROI/LTV 后续追踪（如果有数据源）

### monetization_performance_analysis 待补

- [ ] ARPDAU 按 ad_format 拆解（激励视频/插屏/Banner）
- [ ] 展示渗透率 × 人均展示次数趋势
- [ ] eCPM 按 ad_source 变化
- [ ] fill rate 下降诊断（按 ad_source × ad_format）

## 执行约束

- 新 SQL 必须先进入 `da_assets/candidate_sql/`，通过 `SQL晋升治理.md` 门禁后才能进 `verified_sql/`
- 补充后更新 `da_assets/index.yaml`
- 跑 `check_knowledge_consistency.py` 验证
