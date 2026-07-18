# PI 查询执行复核护栏

## 目标

把这次 PI 线上问题里暴露出的几个高频坑，沉淀成通用执行护栏，避免后续再靠 case by case 补题。

## 适用边界

- Runtime / PI 在回答业务 SQL、NL2SQL、投放分析、cohort 收入或留存类问题时适用。
- Reviewer / Goal 长任务在复核 trace、query_records、线上 replay 时同样适用。
- 这不是某一题的固定 SQL 模板，而是执行顺序和证据标准。

## 固定护栏

1. `SELECT 1`、`MAX(dt)`、freshness probe 只能作为 smoke，不是业务答案。
2. 核心业务 SQL 返回 0 行或明显异常时，必须继续 smoke：
   - 日期窗口是否成熟；
   - 关键过滤条件是否掉空；
   - join 前后行数是否异常；
   - 分表口径是否被误套。
3. 安装 / 激活 cohort 与行为 / 收入表联查时，先确认 cohort 侧真实可用的产品过滤字段。
   - 默认优先校验 `bundle_id` / 包体等激活表真实字段；
   - 行为 / 收入表的 `app_name` 过滤，不得未验证就直接套到激活表。
4. 当问题要求 cohort 人均收入、人均留存或 cohort 侧均值时，分母必须保留 cohort 全量。
   - 默认使用 `LEFT JOIN + COALESCE` 保留 0 收入 / 0 回收用户；
   - 不能只对“有收入用户”做平均，除非问题明确要求。
5. `D7累计`、`D7总收入` 和常规 `D0/D7收入均值` 默认都是累计到第 N 天的 cohort 口径。
   - D0 收入：cohort 当天收入。
   - D7 收入：D0-D7 累计收入，即 `dt >= cohort_date AND dt <= cohort_date + 7`。
   - 只有用户明确说“D7 当天”时，才允许只取 `dt = cohort_date + 7`。
   - 非负收入口径下，D7 累计均值低于 D0 均值时必须停止并自检。
6. Runtime 修复后，不能只看回答文本，必须核验：
   - trace 是否存在真实工具执行；
   - `query_records` 是否按条落库；
   - metadata / trace 是否保留足够审计字段。
7. Reviewer 长任务必须跑 MC 和 CK live probe。
   - 但普通业务回答只跑和问题真实相关的数据源；
   - 不允许为了“看起来双引擎”而伪造无关 CK 业务答案。

## 关键判断

### 什么时候算“没答出来”

- 核心 SQL 0 行后没有继续 smoke；
- 只返回 probe / freshness，没有返回业务结果；
- 路由、表、join key、日期窗仍有未消解冲突；
- 没有形成 trace / query_records 证据链。

### 什么时候算“修复完成”

- 同题本地或 test replay 能成功返回；
- 核心 SQL 不再错套过滤条件，或被护栏明确拦截；
- trace、assistant metadata、query_records 三者至少能从两处以上复核真实执行。

## 建议接入点

- `task_routes/text2sql_or_sql_planning.yaml`
- `task_routes/roi_or_campaign_analysis.yaml`
- `eval/agent_regression/regression_cases.yaml`
- `da_assets/analysis_sop/20260623_PI调用日志复核与线上回归SOP.md`
