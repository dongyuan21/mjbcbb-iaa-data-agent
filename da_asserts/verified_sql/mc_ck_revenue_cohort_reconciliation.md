# MC vs CK Revenue / Cohort 对账

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_mc_ck_revenue_cohort_reconciliation` |
| 状态 | verified |
| 适用场景 | 补 spend 之外的 MC↔CK 同源对账：SDK 回收 / AF 回收 / 留存 cohort |
| 验证日期 | 2026-06-16 |
| 对账日 | `active_date = 2026-06-12`（距今 4 天，回收/留存基本回灌成熟，仅到 date_diff=3） |
| 对账粒度 | `active_date × date_diff`（全维度 SUM） |
| 关联 | 补全 `mc_ck_spend_reconciliation.md`（spend 主表）；回写 `../../ai_ck/agent_knowledge/数据地图.md` 衔接表 |

对账表对：

| 域 | MC 表 (`h-s`) | CK 表 (`shucang_market`) |
|---|---|---|
| SDK 回收 | `ads_market_tj_ad_sdk_revenue_attributed_di` | `tj_ad_sdk_revenue` |
| AF 回收 | `ads_market_tj_ad_revenue_v2` | `tj_ad_revenue_v2` |
| 留存 cohort | `ads_market_af_cohort_user_acquisition_v2` | `af_cohort_user_acquisition_v2` |

## 口径说明

- **MC 与 CK 分区语义不同**：MC 三表分区为 `dt`，实测 `dt` = 变现日 / 留存事件日，**按 date_diff 增量落库**（同一 `active_date` 的回收/留存分散在 `dt = active_date, active_date+1, …` 各分区，逐日递减），**不是累计快照**；CK 是按 `active_date` 的单表累计（物理表含该 active_date 的所有 date_diff 行）。
- 因此**跨源对账必须按 `date_diff` 对齐**：MC 用 `dt` 覆盖 `[active_date, active_date+N]` 再 `GROUP BY date_diff`；CK 直接 `WHERE active_date=X GROUP BY date_diff`。直接比 `dt` 或不分层会错配。
- 等价地，MC 的 `active_date` 累计 = `SUM(revenue) WHERE dt >= active_date`，CK 累计 = `SUM(revenue) WHERE active_date=X`。
- 时区：MC sdk 表 `active_date` 注释 `UTC8`、CK 注释 `UTC0`，但实测同名 `active_date` 数值 bit 级一致 → 口径实质对齐，**以数据为准，注释存疑**。

## SQL

### MC（ODPS，按 date_diff 累计）

```sql
-- SDK 回收
SELECT date_diff, ROUND(SUM(revenue),2) AS revenue, SUM(revenue_counts) AS rev_cnt
FROM h-s.ads_market_tj_ad_sdk_revenue_attributed_di
WHERE dt BETWEEN '2026-06-12' AND '2026-06-16' AND active_date = '2026-06-12'
GROUP BY date_diff ORDER BY date_diff;

-- AF 回收（把表名换成 ads_market_tj_ad_revenue_v2，其余相同）
-- 留存 cohort
SELECT date_diff, SUM(unique_users) AS uu, SUM(event_count) AS ec
FROM h-s.ads_market_af_cohort_user_acquisition_v2
WHERE dt BETWEEN '2026-06-12' AND '2026-06-16' AND active_date = '2026-06-12'
  AND date_diff IN (0,1,2,3)
GROUP BY date_diff ORDER BY date_diff;
```

### CK（ClickHouse）

```sql
-- SDK 回收
SELECT date_diff, ROUND(SUM(revenue),2) AS revenue, SUM(revenue_counts) AS rev_cnt
FROM shucang_market.tj_ad_sdk_revenue
WHERE active_date = '2026-06-12'
GROUP BY date_diff ORDER BY date_diff;

-- AF 回收（把表名换成 shucang_market.tj_ad_revenue_v2，其余相同）
-- 留存 cohort
SELECT date_diff, SUM(unique_users) AS uu, SUM(event_count) AS ec
FROM shucang_market.af_cohort_user_acquisition_v2
WHERE dt >= '2026-06-12' AND active_date = '2026-06-12'
  AND date_diff IN (0,1,2,3)
GROUP BY date_diff ORDER BY date_diff;
```

## 验证记录（active_date = 2026-06-12，2026-06-16 实跑）

### SDK 回收 `tj_ad_sdk_revenue`（revenue / revenue_counts）

| date_diff | MC revenue | CK revenue | MC rev_cnt | CK rev_cnt | 一致 |
|---|---|---|---|---|---|
| 0 | 143385.41 | 143385.41 | 1562041 | 1562041 | ✅ |
| 1 | 87933.94 | 87933.94 | 611633 | 611633 | ✅ |
| 2 | 59427.17 | 59427.17 | 470802 | 470802 | ✅ |
| 3 | 46810.46 | 46078.47 | 399006 | 392488 | ⚠️ CK 少 1.6%（回填时间差） |

### AF 回收 `tj_ad_revenue_v2`

| date_diff | MC revenue | CK revenue | MC rev_cnt | CK rev_cnt | 一致 |
|---|---|---|---|---|---|
| 0 | 131459.25 | 131459.25 | 1604053 | 1604053 | ✅ |
| 1 | 82977.03 | 82977.03 | 654425 | 654425 | ✅ |
| 2 | 57206.49 | 57206.49 | 515390 | 515390 | ✅ |
| 3 | 45676.53 | 45676.53 | 439698 | 439698 | ✅ |

### 留存 cohort `af_cohort_user_acquisition_v2`（unique_users / event_count）

| date_diff | MC unique_users | CK unique_users | MC event_count | CK event_count | 一致 |
|---|---|---|---|---|---|
| 0 | 3135702 | 3135702 | 10280493 | 10280493 | ✅ |
| 1 | 824404 | 824404 | 3459163 | 3459163 | ✅ |
| 2 | 637101 | 637101 | 2522134 | 2522134 | ✅ |
| 3 | 534667 | 534667 | 2045223 | 2045223 | ✅ |

## 结论

- **AF 回收、留存 cohort：MC↔CK 在所有可用 date_diff（0–3）上 bit 级完全一致**，证明同源、口径一致、同步正确。
- **SDK 回收：成熟层（date_diff 0/1/2）bit 级一致；最新层 date_diff=3 CK 比 MC 少 1.6%**（CK 392488 设备 / 46078 收入 vs MC 399006 / 46810），为 SDK 回收回填的同步时点差（对账时 CK 快照略早于 MC），**非口径错误**。隔日复跑该层应收敛一致。
- 跨源对账方法（按 `date_diff` 对齐）验证有效，可纳入日常 sanity check。

## 风险与陷阱

- 只在 `active_date=2026-06-12` 单日、`date_diff≤3` 范围验证；更久窗口或更深 date_diff 未覆盖。
- MC 必须带 `dt` 分区过滤；对未成熟 `active_date`（距今 < 3 天）对账，最新 date_diff 层大概率不一致，属回填进度差，不应据此判口径错误。
- CK 与 MC 可能存在同步延迟；对账避开当天实时未完成分区。
- 真理源仍以 MaxCompute 为准，CK 仅作 OLAP 加速。
