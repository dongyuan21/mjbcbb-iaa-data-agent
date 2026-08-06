# ads_market_roi_cohort_sdk_multidim ETL 生产 SQL 血缘待补

## 状态

`needs_evidence` — 非阻塞,等用户从阿里云 DataWorks 找到产出任务 SQL 后补齐。

## 背景

2026-07-23 已通过 CK live probe + 宽表建设需求文档交叉确认这张宽表的上游四链路(消耗 / SDK 真实回收 / ROI 预估补全 / 游戏行为维表),并已写入表卡 `upstream` 字段、catalog、CK/Hive 数据地图,三个质量门禁全绿。

但具体把四条上游链路拼合并 INSERT 到 CK 的 **ETL 写入 SQL** 不在需求文档内,当前在表卡 `upstream.non_verified_note` 标为待 owner 确认。

## 待办

1. 用户在阿里云 DataWorks 数据开发中搜索产出 `ads_market_roi_cohort_sdk_multidim`(或 `_local`)的节点:
   - 搜节点名或节点 SQL 含 `ads_market_roi_cohort_sdk_multidim`
   - 或搜 `INSERT INTO shucang_market.ads_market_roi_cohort_sdk_multidim`
   - 写 CK 的节点一般是「数据集成节点」(MC → CK 离线同步)或「ODPS SQL 节点 + 数据集成」两段式。
2. 拿到生产 SQL 后,重点核对:
   - FROM 了哪些源表(验证四链路是否对得上)
   - 预估模型 v6-SDK / xy_v5 的接入方式
   - `dim_level` 各层级(date/bundle/bundle_media/...)的 rollup 逻辑
   - Campaign 筛选(近30天累计折后消耗>500 且 当日折后消耗>50)是否在 SQL 里实现
3. 核对完成后:
   - 补进表卡 `upstream` 的 `etl_sql_source` / `etl_node` 字段
   - 去掉 `upstream.non_verified_note`
   - 更新 `last_verified`
   - 跑 `check_table_card_quality.py` + `check_knowledge_consistency.py`

## 关联文件

- 表卡:`ai_ck/agent_knowledge/tables/ads_market_roi_cohort_sdk_multidim.yaml`
- 需求文档(本地归档):`raw_exports/宽表建设&ROI 预估落表范围需求.docx`
