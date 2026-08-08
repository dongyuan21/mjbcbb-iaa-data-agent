# UA 决策行为沉淀 — 接手 Prompt

你将接手"UA 决策行为沉淀"项目。以下是完整的接手指令，从 git pull 开始。

## 第一步：拉代码

```bash
cd /Users/lidongyuan/hungrystudio/点位/数仓
git pull origin main
```

当前最新 commit：`4c0d2746`（含交接文档 + 全部代码 + 工具注册）。

## 第二步：读交接文档

```bash
cat data_agent_plan/UA决策行为沉淀/UA决策行为沉淀交接文档.md
```

这是项目的完整状态，包含：
- 当前能力（3 个工具 + 预测模型 + DiD 效应）
- 代码结构（57 脚本 + 40 文档）
- 数据来源（MC + CK + MI）
- 环境依赖路径
- 验证指南
- 尚未完成项

## 第三步：验证环境

```bash
# 1. MaxCompute 连通性
python3 /Users/lidongyuan/.maxcompute-dataworks/bin/maxcompute_sql.py --sql "SELECT 1"

# 2. ClickHouse 连通性（先 source 环境变量）
source /Users/lidongyuan/hungrystudio/cursor_friend_pack_system_env/fill_clickhouse_env_here.zsh
python3 /Users/lidongyuan/.clickhouse-shucang/bin/clickhouse_sql.py --sql "SELECT 1" --format json

# 3. MI API 连通性
/Users/lidongyuan/.codex/skills/mi-curl/scripts/mi_curl.sh "https://boards.youxi123.com/api/boards/reports/roi360/configuration" | head -20

# 4. Python 依赖
python3 -c "import sklearn, numpy; print('sklearn', sklearn.__version__, 'numpy', numpy.__version__)"
```

## 第四步：跑测试

```bash
cd /Users/lidongyuan/hungrystudio/点位/数仓

# 操作分类解析器（20 case）
PYTHONPATH=. python3 tools/scripts/test_ua_operation_taxonomy.py

# 备注意图分类器（15 case）
PYTHONPATH=. python3 tools/scripts/test_ua_remark_intent_v2.py
```

两个测试文件应该全部通过（35/35 ✅）。

## 第五步：验证工具能用

```bash
# 1. 预测工具 — 模式1（campaign 名称 → 自动拉 CK 特征）
PYTHONPATH=. python3 tools/scripts/ua_predict.py --campaign "EU-036-PUR-RC-250911-HK"

# 2. 预测工具 — 模式2（手动输入数据，不依赖 CK）
PYTHONPATH=. python3 tools/scripts/ua_predict.py --manual '{"cost_7d": 50000, "revenue_7d": 2500, "cost_change_pct": 0.35}'

# 3. 国家排除效应查询
PYTHONPATH=. python3 tools/scripts/ua_country_effect.py --country Germany

# 4. 全局摘要
PYTHONPATH=. python3 tools/scripts/ua_country_effect.py
```

如果模式 1 报 "campaign not found in CK"，说明 `/tmp/ua_phase3_v2_did/all_rows.jsonl` 不存在（重启会丢），需要重建（见第七步）。

## 第六步：看训练数据

训练数据被 `.gitignore` 排除，不在 git 里。需要从本地读取或重新生成。

```bash
# 如果 data_agent_plan/ua_phase3_v2_data/ 存在（前一个会话 copy 过来）：
ls -lh data_agent_plan/ua_phase3_v2_data/

# CSV 可以直接用 Excel 打开
open data_agent_plan/ua_phase3_v2_data/all_rows.csv

# 或用 Python 看
python3 -c "
import json
rows = [json.loads(l) for l in open('data_agent_plan/ua_phase3_v2_data/all_rows.jsonl')]
print(f'共 {len(rows)} 条训练数据')
print(f'操作类型分布:')
from collections import Counter
for t, c in Counter(r.get('op_type','') for r in rows).most_common():
    print(f'  {t:15s} {c}')
"
```

## 第七步：重建缓存数据（如果 /tmp 数据丢了）

```bash
# 1. 重建完整 v2 pipeline（拉 MC + CK + 训练 + DiD，约 5 分钟）
PYTHONPATH=. python3 tools/scripts/ua_phase3_v2.py --output-dir /tmp/ua_phase3_v2_did

# 2. 重建国家效应表（拉 CK + 跑 DiD，约 2 分钟）
PYTHONPATH=. python3 tools/scripts/ua_country_effect.py --rebuild

# 3. 重新拉取 MI 备注（1000 campaign × 8.5 个月，约 4 分钟）
python3 tools/scripts/ua_fetch_mi_remarks_full.py --output /tmp/ua_v2_mi_remarks.jsonl

# 4. 重新分类 MI 备注意图
python3 tools/scripts/ua_remark_intent_v2.py /tmp/ua_v2_mi_remarks.jsonl /tmp/ua_v2_remark_intents.jsonl
```

## 第八步：了解当前模型

- **算法**：RandomForest (n=300, depth=12)
- **训练数据**：2,618 条 Google 操作事件，5 类操作
- **测试集 macro_f1**：0.64
- **输出 7 个标签**：budget_increase / budget_decrease / bid_increase / bid_decrease / status_pause / geo_exclude_exclude / creative_change
- **方向判断**：规则型（方案 A），budget/bid 看 ROI + 消耗趋势

详见：`data_agent_plan/UA决策行为沉淀/UA决策沉淀v2评估报告.md`

## 第九步：了解 DiD 因果效应

安慰剂 10/10 通过，7 组显著：

| 操作 | D14 DiD | 解读 |
|------|---------|------|
| status（关停） | +28,623 | 关停亏损 campaign 后利润提升 |
| geo_exclude（排除国家） | +5,175 (D7) | 排除低价值国家后利润提升 |
| creative（换素材） | -44,829 | 换素材后利润短期下降（学习期） |
| budget（调预算） | -17,654 | 调预算后利润下降 |

Agent 默认召回：`knowledge/agent_knowledge/report_knowledge/UA操作效应DiD基准表.yaml`

## 第十步：尚未完成的工作

| # | 任务 | 说明 |
|---|------|------|
| 1 | 扩展到 Meta + AppLovin | 快照 diff，样本量到 5000+ |
| 2 | Agent 预警规则配置 | 让 Agent 自动引用 DiD 效应 |
| 3 | 素材+国家特征加入模型 | 等 5000+ 样本后启动（见 TODO） |
| 4 | Phase 6 实验预注册 | 需业务+数据+算法共同参与 |

详见：
- `TODO/UA决策沉淀Agent接入方案.md`
- `TODO/UA模型特征扩展待办_素材与国家级ROI.md`
- `data_agent_plan/UA决策行为沉淀/UA决策行为沉淀实施台账.md` §9

## 关键约束

1. **只预警不执行** — 不输出"建议立即加/降预算"
2. **DiD 非因果证明** — 标 observational_causal
3. **国家级数据必须在 bundle_id 前提下**
4. **不保存 PII** — MI token / cookie / 邮箱不入 git
5. **训练数据在 /tmp/ 会丢** — 重新运行 pipeline 可恢复
6. **正文不许出现"蒸馏"** — 已统一改为"沉淀"

## 线上状态

- 3 个山海服务已部署 `fd9dc3e8`（API + Worker + Freshness）
- `GET /api/tools` 返回 3 个工具
- `GET /api/ua/predict?campaign=X` 可用
- `POST /api/ua/predict/manual` 可用
- `GET /api/ua/country-effect?country=Germany` 可用
