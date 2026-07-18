# Verified SQL: AF 激活 vs MI 注册设备 时区对齐对账 (UTC0/UTC8)

## 元信息

| 项 | 内容 |
|---|---|
| ID | `vsql_20260616_af_mi_register_timezone_recon` |
| 状态 | verified |
| 来源 | 用户证据 2026-06-16：MI ROI360 截图「注册设备(af)=255,977」(BB GP / googleadwords_int / 2026-06-15) + 用户两条对比 SQL |
| 适用场景 | 用 AF 侧激活明细核对 MI ROI360「注册设备(af)」时排除 UTC0/UTC8 切日错位；回应「AF 归因注册 < MI 注册」类质疑 |
| 最后验证 | 2026-06-16 |

## 原始问题

> BB 这个游戏，AF 每天归因到 Google 的注册设备数，比 MI ROI360 上 Google 的「新注册设备数」要少。

## 口径说明

| 类型 | 内容 |
|---|---|
| 产品 | BB GP，`bundle_id = com.kcolb.juggle` |
| 渠道 | Google，`media_source = googleadwords_int`（MI 的 Google 即此单一源，无聚合） |
| 对比日 | 2026-06-15（单日；论断本质是单日错位，多日聚合会自洽） |
| MI 侧 | 页面「注册设备(af)」= `shucang_market.tj_ad_spend_active_v2.registers`；MC 同构表 `h-s.ads_market_tj_ad_spend_active_v2.registers`；`active_date` 为 **UTC8** |
| AF 侧 | `h-s.dwd_market_appsflyer_activation_push_hi` 激活明细，按设备 `appsflyer_id` 去重 |
| 关键时区 | hi 表 `dt` 为 **UTC0** 分区：`dt='D'` 实测覆盖 `active_time_utc8` 的 `[D 08:00, 次日 08:00)`；`active_time_utc8` 才是 UTC8 自然日 |
| 去重键 | `appsflyer_id`(设备) ≈ `distinct_id`(业务ID)，本场景 `null` 占比 0，二者等价；用户原 SQL 的 `count(distinct distinct_id)` 与设备去重一致 |

## SQL

```sql
-- A. AF 侧：同一数据用两种切日口径对比（UTC0 dt vs UTC8 active_time）
--    af_dev_dt_utc0  复现用户口径(dt=UTC0)        -> 241,434
--    af_dev_utc8     对齐 MI(active_time_utc8)    -> 255,977
SELECT
  count(distinct if(dt = '2026-06-15', appsflyer_id, NULL))                              AS af_dev_dt_utc0,
  count(distinct if(substr(active_time_utc8,1,10) = '2026-06-15', appsflyer_id, NULL))   AS af_dev_utc8
FROM h-s.dwd_market_appsflyer_activation_push_hi
WHERE dt IN ('2026-06-14','2026-06-15','2026-06-16')   -- UTC8 的 06-15 跨 UTC0 两个分区，多带一天兜底
  AND media_source = 'googleadwords_int'
  AND bundle_id = 'com.kcolb.juggle';
```

```sql
-- B. MI 侧「注册设备(af)」(active_date 为 UTC8) -> 255,977
--    注意字段是 registers(复数)，写成 register 会报 column cannot be resolved
SELECT sum(registers) AS registers
FROM h-s.ads_market_tj_ad_spend_active_v2
WHERE dt = '2026-06-15' AND active_date = '2026-06-15'
  AND media_source = 'googleadwords_int'
  AND bundle_id = 'com.kcolb.juggle';
-- CK 等价：shucang_market.tj_ad_spend_active_v2，同口径同值 255,977
```

## 验证记录

| 日期 | 验证人 | 结果 | 备注 |
|---|---|---|---|
| 2026-06-16 | AI | verified | bit 级一致：AF `active_time_utc8`=06-15 设备去重 255,977 == MI `registers` 255,977；同口径对齐后无差异 |

实测数值（BB GP / googleadwords_int / 2026-06-15，设备去重）：

| 口径 | 数值 | 时区 |
|---|---:|---|
| MI registers（active_date UTC8） | 255,977 | UTC8 |
| AF `active_time_utc8` = 06-15 | 255,977 | UTC8（= MI，bit 级相等） |
| AF `dt='2026-06-15'`（用户口径） | 241,434 | UTC0 |
| AF `active_time_utc0` = 06-15 | 241,434 | UTC0 |
| AF `count(distinct distinct_id)`，dt=06-15 | 241,432 | UTC0 |

## 关键结论

- MI「注册设备(af)」与 AF 激活去重设备是**同一口径**，同时区下 bit 级相等；MI 未多报、AF 未少报。
- 「AF 比 MI 少约 6%」的唯一根因是**时区切日**：`dt`(UTC0) 与 `active_date`(UTC8) 错开 8 小时，覆盖的不是同一批用户。
- 多日聚合时时区误差互相抵消（前期实测 7 天合计 AF ≈ MI），差异只在单日显现且有正有负（如 06-12/06-13 反而 AF 多）。

## 风险与陷阱

- 拿激活明细对 MI 时**必须**用 `substr(active_time_utc8,1,10)` 切日，不能用 `dt`(UTC0) 直接对 `active_date`(UTC8)。
- UTC8 单日跨 UTC0 两个 `dt` 分区，须 `dt IN ('D-1','D')`（或多带一天）才能覆盖完整。
- `dwd_market_appsflyer_activation_push_hi` 暂无独立表卡，结构同 `dwd_market_appsflyer_activation_push_data_di`；`appsflyer_id`/`distinct_id` 为 PII，仅聚合 `count(distinct ...)`，不落明细。
- 媒体侧 `media_installs`（页面「注册设备(media)」）约为 af 口径的 4 倍，是 Google 自报安装，勿与「注册设备(af)」混比。
- 该数对账，不含 organic 拆分；如需区分 organic，按 `media_source`/`campaign_type` 另出 `all` 与 `paid_only` 两版。
