# 新/回流设备 SDK 收入 dwd / dws 边界验证

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260616_sdk_revenue_dwd_dws_boundary_validation` |
| 状态 | verified |
| 适用场景 | 验证 `dwd_market_new_return_device_sdk_revenue_di` 与 `dws_market_new_return_device_sdk_revenue_di` 的字段、分区、血缘、聚合关系和 `device_cnt` 口径 |
| 依赖表 | `dwd_market_new_return_device_sdk_revenue_di`, `dws_market_new_return_device_sdk_revenue_di` |
| 最后验证 | 2026-06-16 |

## 口径说明

- 验证对象：`dwd_market_new_return_device_sdk_revenue_di` 与 `dws_market_new_return_device_sdk_revenue_di` 的字段、血缘、分区、聚合关系和 `device_cnt` 口径。
- 粒度边界：`dwd` 落表后是 `device_id` 粒度；`dws` 是聚合层，不保留任何 ID 字段。
- 聚合口径：`dws.device_cnt` 来自任务 SQL 的 `COUNT(device_id)`，不是 `COUNT(DISTINCT device_id)`。
- 日期口径：`dws.date_diff` 来自 `DATEDIFF(TO_DATE(dt), TO_DATE(substr(af_install_time_utc8, 1, 10)))`。
- 验证分区：字段和分区用线上表探测；聚合关系用共同分区 `dt='2026-06-02'` 对账。

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-16 | AI | verified | 结合线上字段/分区探测、DataWorks 任务 SQL、血缘截图和 `2026-06-02` 共同分区聚合对账；只记录聚合结果，不输出或落盘用户级明细。 |

## 验证结论

- 线上 `dwd_market_new_return_device_sdk_revenue_di` 字段名是 `device_id`，没有 `distinct_id` 字段。
- 线上 `dws_market_new_return_device_sdk_revenue_di` 没有任何 ID 字段，只有聚合维度和 `device_cnt`、`revenue`。
- DataWorks 任务 SQL 确认：`dwd` 源收入事实是 `distinct_id` 粒度；任务通过 `dim_market_new_return_device_attribution_da` 的 `EXPLODE(distinct_id)` 映射到 `device_id`，再输出到收入 `dwd` 表。
- DataWorks 血缘图确认：`dws_market_new_return_device_sdk_revenue_di` 由 `dwd_market_new_return_device_sdk_revenue_di` 经 SQL 节点直接产出。
- DataWorks 血缘图显示：`dwd_market_new_return_device_sdk_revenue_di` 上游包含 `dim_market_appsflyer_attribution_by_distinct_id_da`、`dim_market_new_return_device_attribution_da` 和多张 `*_user_multi_dim_hi` / `*_user_ha` 表；这解释了 DA 提到 `distinct_id` 的上游背景，但收入 `dwd` 表自身字段仍是 `device_id`。
- DA 将收入 `dwd` 称为 `distinct_id` 维度的来源已基本解释：任务输入收入层确实是 `distinct_id` 粒度；但落表后的收入 `dwd` 字段是映射后的 `device_id`。
- `2026-06-02` 共同分区中，`dws.revenue` 与 `dwd.sum(revenue)` 在 bundle 粒度仅有浮点尾差，可视为同一收入聚合口径。
- `dws.device_cnt` 任务 SQL 口径是 `COUNT(device_id)`，不是 `COUNT(DISTINCT device_id)`；`2026-06-02` 共同分区中 `dws.sum(device_cnt)=47,130,319`，与 `dwd` 非空 `device_id` 行数一致。
- `dws.date_diff` 任务 SQL 口径是 `DATEDIFF(TO_DATE(dt), TO_DATE(substr(af_install_time_utc8, 1, 10)))`；非空安装日记录的数据验证全部匹配。
- 两表分区新鲜度不同：验证时 `dwd` 最新分区到 `2026-06-15`，`dws` 最新分区只到 `2026-06-02`。
- DataWorks 产出信息截图显示两表都有日调度生产任务：`dwd_market_new_return_device_sdk_revenue_T14`（节点 ID `10000306290`）和 `dws_market_new_return_device_sdk_revenue_T14`（节点 ID `10000306291`），且截图可见 2026-06-13 / 2026-06-14 周期实例运行记录。
- `dwd` 任务 SQL 中约束 `AND substr(attr.af_install_time_utc0, 1, 10) <= raw.revenue_date` 被注释掉，这能解释为什么后续 `dws` 可能出现 `af_install_date > revenue_date` 和负 `date_diff`。

## 血缘图证据

来源图片：`raw_exports/lineage-graph-image.png`，抽取记录见 `da_assets/raw/2026-06-16_SDK回收血缘图抽取记录.md`。

血缘链路：

```text
dim_kcolb_tsalb_gp_user_ha
dim_kcolb_tsalb_ios_user_ha
dim_market_appsflyer_attribution_by_distinct_id_da
dim_market_new_return_device_attribution_da
dws_kcolb_tsalb_all_user_multi_dim_hi
dws_kcolb_tsalb_gp_user_multi_dim_hi
dws_kcolb_tsalb_ios_user_multi_dim_hi
dws_block_collection_all_user_multi_dim_hi
dws_nova_collection_all_user_multi_dim_hi
  -> SQL
  -> dwd_market_new_return_device_sdk_revenue_di
  -> SQL
  -> dws_market_new_return_device_sdk_revenue_di
```

## SQL

### DataWorks 任务 SQL 摘录

来源：用户 2026-06-16 粘贴的 DataWorks 任务 SQL，抽取记录见 `da_assets/raw/2026-06-16_SDK回收DataWorks任务SQL摘录.md`。

关键片段：

```sql
-- dwd: SDK 收入（distinct_id 粒度）与 attribution 表 explode distinct_id 后关联
LEFT JOIN (
    SELECT
        device_id, bundle_id, did AS distinct_id,
        af_media_source, af_country,
        af_campaign_id, af_campaign_name,
        af_adset_id, af_adset_name,
        af_ad_id, af_ad_name,
        af_install_time_utc8, af_install_time_utc0,
        is_new_device, is_return_device,
        sdk_install_date, sdk_return_date
    FROM h-s.dim_market_new_return_device_attribution_da
    LATERAL VIEW EXPLODE(distinct_id) t AS did
    WHERE dt = MAX_PT('h-s.dim_market_new_return_device_attribution_da')
) attr ON raw.distinct_id = attr.distinct_id
       AND raw.bundle_id = attr.bundle_id
    --    AND substr(attr.af_install_time_utc0, 1, 10) <= raw.revenue_date
GROUP BY attr.device_id, raw.bundle_id, raw.revenue_date;
```

```sql
-- dws: 从 dwd 聚合，去掉 device_id 粒度
SELECT
    substr(af_install_time_utc8, 1, 10) AS af_install_date,
    DATEDIFF(TO_DATE(dt), TO_DATE(substr(af_install_time_utc8, 1, 10))) AS date_diff,
    COUNT(device_id) AS device_cnt,
    SUM(revenue) AS revenue,
    dt
FROM h-s.dwd_market_new_return_device_sdk_revenue_di
WHERE dt BETWEEN '${start_date}' AND '${end_date}'
GROUP BY
    bundle_id, af_media_source, af_country,
    af_campaign_id, af_campaign_name,
    af_adset_id, af_adset_name,
    af_ad_id, af_ad_name,
    substr(af_install_time_utc8, 1, 10),
    is_return_device,
    DATEDIFF(TO_DATE(dt), TO_DATE(substr(af_install_time_utc8, 1, 10))),
    dt;
```

### 字段确认

```sql
DESC h-s.dwd_market_new_return_device_sdk_revenue_di;
DESC h-s.dws_market_new_return_device_sdk_revenue_di;
```

### 分区确认

```sql
SHOW PARTITIONS h-s.dwd_market_new_return_device_sdk_revenue_di;
SHOW PARTITIONS h-s.dws_market_new_return_device_sdk_revenue_di;
```

### dwd 分区画像

```sql
SELECT
  COUNT(1) AS rows_cnt,
  COUNT(DISTINCT device_id) AS distinct_device_cnt,
  SUM(revenue) AS revenue,
  SUM(CASE WHEN device_id IS NULL OR device_id = '' THEN 1 ELSE 0 END) AS blank_device_rows
FROM h-s.dwd_market_new_return_device_sdk_revenue_di
WHERE dt = '2026-06-02';
```

验证结果：

```text
rows_cnt=47,130,324
distinct_device_cnt=47,123,964
revenue=3,081,954.109868057
blank_device_rows=5
```

### dws 分区画像

```sql
SELECT
  COUNT(1) AS rows_cnt,
  SUM(device_cnt) AS sum_device_cnt,
  SUM(revenue) AS revenue
FROM h-s.dws_market_new_return_device_sdk_revenue_di
WHERE dt = '2026-06-02';
```

验证结果：

```text
rows_cnt=13,482,994
sum_device_cnt=47,130,319
revenue=3,081,954.1098680203
```

### bundle 粒度对账

```sql
WITH dwd AS (
  SELECT
    bundle_id,
    SUM(revenue) AS revenue,
    COUNT(1) AS rows_cnt,
    COUNT(DISTINCT device_id) AS distinct_device_cnt
  FROM h-s.dwd_market_new_return_device_sdk_revenue_di
  WHERE dt = '2026-06-02'
  GROUP BY bundle_id
),
dws AS (
  SELECT
    bundle_id,
    SUM(revenue) AS revenue,
    SUM(device_cnt) AS device_cnt
  FROM h-s.dws_market_new_return_device_sdk_revenue_di
  WHERE dt = '2026-06-02'
  GROUP BY bundle_id
)
SELECT
  COALESCE(dwd.bundle_id, dws.bundle_id) AS bundle_id,
  dwd.rows_cnt AS dwd_rows,
  dwd.distinct_device_cnt AS dwd_distinct_devices,
  dws.device_cnt AS dws_device_cnt,
  dwd.revenue AS dwd_revenue,
  dws.revenue AS dws_revenue,
  dws.revenue - dwd.revenue AS revenue_diff,
  dws.device_cnt - dwd.rows_cnt AS devicecnt_minus_rows
FROM dwd
FULL OUTER JOIN dws
ON dwd.bundle_id = dws.bundle_id
ORDER BY ABS(dws.revenue - dwd.revenue) DESC
LIMIT 20;
```

### date_diff 公式验证

```sql
SELECT
  COUNT(1) AS valid_rows,
  SUM(device_cnt) AS valid_device_cnt,
  SUM(
    CASE
      WHEN date_diff = DATEDIFF(
        CAST(CONCAT(revenue_date, ' 00:00:00') AS TIMESTAMP),
        CAST(CONCAT(af_install_date, ' 00:00:00') AS TIMESTAMP),
        'dd'
      )
      THEN device_cnt ELSE 0
    END
  ) AS formula_match_device_cnt
FROM h-s.dws_market_new_return_device_sdk_revenue_di
WHERE dt = '2026-06-02'
  AND af_install_date IS NOT NULL
  AND af_install_date <> ''
  AND revenue_date IS NOT NULL
  AND revenue_date <> '';
```

验证结果：

```text
valid_rows=13,482,989
valid_device_cnt=47,130,319
formula_match_device_cnt=47,130,319
```

## DataWorks 产出任务证据

来源截图抽取记录：`da_assets/raw/2026-06-16_SDK回收DataWorks生产任务截图.md`。

| 表 | 产出任务 | 调度 | 节点 ID | 截图可见信息 |
|---|---|---|---|---|
| `dwd_market_new_return_device_sdk_revenue_di` | `dwd_market_new_return_device_sdk_revenue_T14` | 日调度 / 周期实例 | `10000306290` | 业务日期 `2026-06-15`，近期实例在 `18:30` 附近运行，2026-06-14 实例耗时约 `6秒` |
| `dws_market_new_return_device_sdk_revenue_di` | `dws_market_new_return_device_sdk_revenue_T14` | 日调度 / 周期实例 | `10000306291` | 业务日期 `2026-06-15`，近期实例在 `18:30` 附近运行，2026-06-14 实例耗时约 `1秒` |

解释边界：截图证明生产任务和周期实例存在；任务 SQL 已由用户粘贴补充。但实际运行参数 `${start_date}` / `${end_date}`、是否空跑或写入失败仍需结合运行日志判断。分区可用性仍以 MaxCompute `SHOW PARTITIONS` 和查询结果为准。

## 风险与陷阱

- 查询收入 `dwd` 表时不能写 `distinct_id` 字段；如需 `distinct_id`，应回到上游用户宽表或 `dim_market_new_return_device_attribution_da` 展开。
- `dws` 在验证时明显滞后于 `dwd`，但产出信息截图显示 `dws` 日调度任务近期有运行记录；正式分析前必须先查共同分区，滞后原因需看运行参数 `${start_date}` / `${end_date}`、运行日志或写分区结果。
- `2026-06-02` 存在 `af_install_date > revenue_date` 的记录，主要是 `af_install_date=2026-06-03` 对应 `date_diff=-1`，约 `300,909` 设备数；任务 SQL 中安装日期不晚于收入日期的过滤条件被注释，负 `date_diff` 不是查询错误，而是当前任务逻辑允许的结果。
