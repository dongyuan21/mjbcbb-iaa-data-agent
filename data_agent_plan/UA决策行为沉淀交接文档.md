# UA 决策沉淀项目交接文档

> 创建日期：2026-07-27
> 当前 main 分支 commit：`fd9dc3e8`
> 线上版本：3 个山海服务已部署 `fd9dc3e8`（API + Worker + Freshness）

## 一、项目是什么

从 UA（用户获取）的历史操作记录中，沉淀出 UA 的决策行为模式，构建：
1. **行为预测模型**——输入 campaign 表现数据，预测 UA 可能选哪种操作
2. **因果效应估计**——用 DiD 估计每种操作对利润的因果效应
3. **独立工具能力**——CLI + FastAPI 接口，Agent 和人都能用

## 二、当前能力

### 工具市场（3 个工具，已上线）

| 工具 | 接口 | 输入 | 输出 |
|------|------|------|------|
| ROI 月度人员环比 | `POST /api/tools/roi360_monthly_person_recon/jobs` | 两个月导出文件 | Excel 工作簿 |
| **UA 操作预测** | `GET /api/ua/predict?campaign=X` | campaign 名称 | 5 类操作概率 + 方向 + 置信度 |
| **UA 操作预测（手动）** | `POST /api/ua/predict/manual` | 表现数据 JSON | 同上 |
| **国家排除效应** | `GET /api/ua/country-effect?country=Germany` | campaign / country | DiD 效应 + CI + 标签 |

### 预测模型

- **算法**：RandomForest (n=300, depth=12, class_weight=balanced)
- **训练数据**：2,618 条 Google 操作事件（5 类操作）
- **测试集 macro_f1**：0.64
- **输出 7 个标签**：`budget_increase` / `budget_decrease` / `bid_increase` / `bid_decrease` / `status_pause` / `geo_exclude_exclude` / `creative_change`
- **方向判断**：方案 A（规则判断），budget/bid 看 ROI + 消耗趋势，status/geo_exclude/creative 方向固定

### DiD 因果效应（已验证，安慰剂 10/10 通过）

| 操作 | D14 DiD | CI | 解读 |
|------|---------|-----|------|
| status（关停） | +28,623 | [+10,638, +51,884] | 关停亏损 campaign 后利润显著提升 |
| geo_exclude（排除国家） | +5,175 (D7) | [+1,030, +8,549] | 排除低价值国家后利润提升 |
| creative（换素材） | -44,829 | [-67,445, -25,214] | 换素材后利润短期下降（学习期） |
| budget（调预算） | -17,654 | [-31,577, -2,513] | 调预算后利润下降 |

### app 分层 DiD

| App | D7 DiD | 结论 |
|-----|--------|------|
| BlockBlast | -1,077 ✅ | 排除有效 |
| Mahjong | Germany/France/Japan 等主要国家 effective | 排除有效 |
| BlockCrush | 多国 harmful | 排除策略需调整 |

## 三、代码结构

### 已入 git 的文件（57 个脚本 + 40 个文档）

**核心脚本**（`tools/scripts/`）：

| 脚本 | 说明 | 测试 |
|------|------|------|
| `ua_operation_taxonomy.py` | 5 类 change_event JSON 解析器 | `test_ua_operation_taxonomy.py` (20 case) |
| `ua_remark_intent_v2.py` | 6 类意图分类器 | `test_ua_remark_intent_v2.py` (15 case) |
| `ua_fetch_mi_remarks_full.py` | MI 备注批量拉取（1000 campaign × 8.5 个月） | — |
| `ua_phase3_v2.py` | 完整 v2 pipeline（AIPW + DiD） | — |
| `ua_country_effect.py` | 国家级操作效应查询工具（CLI + 查表） | — |
| `ua_predict.py` | UA 操作预测工具（CLI + 两种输入模式） | — |
| `ua_enrich_features.py` | 素材 + 国家特征增强（实验用，暂未启用） | — |

**其他 UA 脚本**（v1 遗留 + Phase 0-5 框架）：
`ua_build_*.py`, `ua_behavior_*.py`, `ua_uplift_*.py`, `ua_pgp_*.py`, `ua_mi_collector.py`, `ua_batch_collect.py`, `ua_phase3_*.py` 等

**关键文档**（`data_agent_plan/`）：

| 文档 | 说明 |
|------|------|
| `data_agent_plan/UA决策行为沉淀/UA决策操作分类体系设计.md` | 6 类 + L0-L3 分层定义 |
| `data_agent_plan/UA决策行为沉淀/UA决策沉淀v2评估报告.md` | v1→v2→DiD 完整对比（8 章节） |
| `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀实施台账.md` §9 | 版本演进 + 当前状态 + 尚未完成 |
| `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀与回测方案.md` | 原始方案 v0.3 |
| `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀执行任务书.md` | Phase 0-6 原子任务 |

**Agent 召回的知识文件**：

| 文件 | 说明 |
|------|------|
| `knowledge/agent_knowledge/report_knowledge/UA操作效应DiD基准表.yaml` | DiD 效应数值（Agent 默认召回） |

**TODO 文件**：

| 文件 | 说明 |
|------|------|
| `TODO/UA决策沉淀Agent接入方案.md` | 数值知识与工具已做；当前 Runtime 主链接线、证据归因和安全发布待办 |
| `TODO/UA模型特征扩展待办_素材与国家级ROI.md` | 等 5000+ 样本后加入新特征 |

### 未入 git 的数据文件（需要线下打包）

**以下文件在 `.gitignore` 排除范围内或只在 `/tmp/`，不在 git 里。重启 `/tmp/` 会丢失。**

#### `data_agent_plan/ua_phase3_v2_data/`（被 .gitignore 排除，但已 copy 到本地）

| 文件 | 大小 | 说明 |
|------|------|------|
| `all_rows.csv` | 1.4 MB | **训练数据 CSV**（3,347 行 × 51 列，Excel 可打开） |
| `all_rows.jsonl` | 3.9 MB | 训练数据 JSONL（同上，程序用） |
| `all_rows_enriched.jsonl` | 4.8 MB | 增强版（加了素材+国家特征，实验用） |
| `operations.jsonl` | 13 MB | 16,361 条操作事件（5 类） |
| `mi_remarks.jsonl` | 1.5 MB | 5,528 条 MI 原始备注（8.5 个月） |
| `remark_intents.jsonl` | 2.6 MB | 5,528 条 MI 备注意图分类 |
| `v2_results.json` | 20 KB | 模型训练结果 + DiD 效应 |
| `country_did_results.json` | 749 KB | country 级 DiD 完整结果 |

#### `/tmp/` 下的缓存文件（重启会丢，可重新生成）

| 路径 | 说明 | 重新生成命令 |
|------|------|------------|
| `/tmp/ua_phase3_v2_did/all_rows.jsonl` | 训练数据（同上） | `python3 tools/scripts/ua_phase3_v2.py --output-dir /tmp/ua_phase3_v2_did` |
| `/tmp/ua_country_effect_cache.json` | 国家效应缓存 | `python3 tools/scripts/ua_country_effect.py --rebuild` |
| `/tmp/ua_v2_mi_remarks.jsonl` | MI 备注 | `python3 tools/scripts/ua_fetch_mi_remarks_full.py` |
| `/tmp/ua_v2_remark_intents.jsonl` | 备注意图分类 | `python3 tools/scripts/ua_remark_intent_v2.py /tmp/ua_v2_mi_remarks.jsonl /tmp/ua_v2_remark_intents.jsonl` |

### ⚠️ 线下打包提醒

**需要你手动打包线下发的文件**：

```bash
# 打包训练数据 + 结果（约 28 MB）
cd /Users/lidongyuan/hungrystudio/点位/数仓
tar -czf ua_training_data.tar.gz data_agent_plan/ua_phase3_v2_data/

# 或者单独 copy CSV（1.4 MB，最常用）
cp data_agent_plan/ua_phase3_v2_data/all_rows.csv ~/Desktop/
```

这些文件被 `.gitignore` 排除（`data_agent_plan/ua_phase3_v2_data/`），不会随 git push 到远程。如果其他机器需要，必须线下传。

## 四、数据来源

| 数据源 | 表/接口 | 时间范围 | 用途 |
|--------|--------|---------|------|
| MC `ods_market_google_ads_config_wide_hi` | Google change_event 宽表 | 2026-06-17 ~ 07-24 (38天) | 5 类操作的 before/after JSON |
| MC `ods_market_google_campaign_criterion_da` | criterion 维度表 | 最新分区 | criterion_id → 国家名映射 |
| CK `tj_ad_spend_active_v2` | 消耗表 | 按需 | cost/shows/clicks/registers（含 country + adset_name 维度） |
| CK `tj_ad_revenue_v2` | 收入表 | 按需 | revenue（含 country 维度） |
| MI API `boards.youxi123.com/api/boards/reports/campaign-govern/ua-remarks` | UA 备注 | 2025-11-11 ~ 2026-07-24 (8.5个月) | 备注文本 → 6 类意图分类 |
| `knowledge/agent_knowledge/report_knowledge/PACKAGE_BUNDLE_MAP.csv` | 包体映射 | 静态 | bundle_id → app_name |

## 五、环境依赖

| 依赖 | 路径 | 说明 |
|------|------|------|
| MaxCompute helper | `/Users/lidongyuan/.maxcompute-dataworks/bin/maxcompute_sql.py` | MC 查询 |
| ClickHouse helper | `/Users/lidongyuan/.clickhouse-shucang/bin/clickhouse_sql.py` | CK 查询 |
| CK 环境变量 | `/Users/lidongyuan/hungrystudio/cursor_friend_pack_system_env/fill_clickhouse_env_here.zsh` | CK 连接配置 |
| MI curl helper | `/Users/lidongyuan/.codex/skills/mi-curl/scripts/mi_curl.sh` | MI API 调用 |
| MI token | `~/.codex/secrets/mi-curl/token` | JWT（不过期） |
| Python 包 | sklearn, numpy, pandas | RF 模型训练 |
| LightGBM | **未安装**（arm64 Mac libomp 架构冲突） | 跳过，用 RF 替代 |

## 六、验证指南

### 人类验证步骤

1. **抽 5-10 个你熟悉的 campaign**，用模式 1 预测：
```bash
PYTHONPATH=. python3 tools/scripts/ua_predict.py --campaign "你熟悉的campaign名"
```
看预测的操作类型 + 方向是否符合 UA 实际决策逻辑。

2. **用模式 2 测试假设场景**：
```bash
PYTHONPATH=. python3 tools/scripts/ua_predict.py --manual '{"cost_7d": 50000, "revenue_7d": 2500, "cost_change_pct": 0.35}'
```
看不同 ROI / 消耗趋势下模型的预测变化是否合理。

3. **查国家排除效应**：
```bash
PYTHONPATH=. python3 tools/scripts/ua_country_effect.py --country Germany
```
看排除 Germany 的 DiD 效应是否跟 UA 体感一致。

4. **查训练数据**：
```bash
# Excel 打开
open data_agent_plan/ua_phase3_v2_data/all_rows.csv

# 或 Python 查看
python3 -c "
import json
rows = [json.loads(l) for l in open('data_agent_plan/ua_phase3_v2_data/all_rows.jsonl')]
print(f'共 {len(rows)} 条')
for r in rows[:5]:
    print(f'{r[\"change_date\"]} {r[\"campaign_name\"][:30]} {r[\"op_type\"]:15s} roi={r[\"roi_7d\"]}')"
```

### 运行测试

```bash
PYTHONPATH=. python3 tools/scripts/test_ua_operation_taxonomy.py
PYTHONPATH=. python3 tools/scripts/test_ua_remark_intent_v2.py
```

### 重建效应表（数据更新后）

```bash
# 重建国家效应表（拉 CK + 跑 DiD）
PYTHONPATH=. python3 tools/scripts/ua_country_effect.py --rebuild

# 重建完整 v2 pipeline（拉 MC + CK + 训练 + DiD）
PYTHONPATH=. python3 tools/scripts/ua_phase3_v2.py --output-dir /tmp/ua_phase3_v2_did
```

## 七、尚未完成

| # | 任务 | 状态 | 说明 |
|---|------|------|------|
| 1 | 扩展到 Meta + AppLovin | 未开始 | 快照 diff 推断预算变更，样本量到 5000+ |
| 2 | 补 country 级数据 | ✅ 已完成 | country DiD + app 分层已跑通 |
| 3 | 接入 Data Agent 预警能力 | 部分完成 | CLI + API + YAML 已做，Agent 预警规则待配置 |
| 4 | Phase 6 实验预注册 | 未开始 | 需业务+数据+算法共同参与 |
| 5 | 素材+国家特征加入模型 | TODO | 等 5000+ 样本后启动（见 `TODO/UA模型特征扩展待办_素材与国家级ROI.md`） |
| 6 | LightGBM | 跳过 | arm64 Mac 架构冲突，用 RF 替代 |

## 八、关键约束（不能违反）

1. **只预警不执行**——不输出"建议立即加/降预算"，只提供效应证据和预测
2. **DiD 非因果证明**——DiD 有平行趋势假设，标 `observational_causal`
3. **国家级数据必须在 bundle_id 前提下**——不能跨 app 看国家
4. **不保存 PII**——MI token / cookie / 操作人邮箱不入 git
5. **训练数据在 /tmp/ 会丢**——重新运行 pipeline 可恢复

## 九、版本历史

| 版本 | 日期 | macro_f1 | Commit | 说明 |
|------|------|---------|--------|------|
| v1 (Phase3) | 2026-07-24 | 0.79 (3类) | `74006e49` | MI 备注 → 3 分类 |
| v1 retry | 2026-07-24 | 0.52 (2类) | `7020ed01` | Google 原生 → budget increase/decrease |
| v2 首版 | 2026-07-24 | 0.15 (5类) | `7020ed01` | 5 类操作 × 双数据源 × app 分层 |
| v2.1 修复 | 2026-07-24 | 0.63 (5类) | `7020ed01` | 加历史特征 + 分层随机 + control 修复 |
| v2.1+DiD | 2026-07-24 | 0.64 (5类) | `f3dfaa9a` | AIPW → DiD，安慰剂 10/10 |
| v2.1+方向 | 2026-07-27 | 0.64 (5类) | `b931fea1` | 加方向预测（7 标签） |
| v2.1+手动 | 2026-07-27 | 0.64 (5类) | `fd9dc3e8` | 加模式 2 手动输入 |
