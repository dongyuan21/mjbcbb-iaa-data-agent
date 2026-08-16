# 分析平台 实战分析 SOP

## 元信息

| 项 | 内容 |
|---|---|
| ID | `sop_mi_分析平台_practical_analysis` |
| 状态 | draft |
| 来源 | `knowledge/audit_archive/mi_analysis/MI_分析平台实战分析_20260613.md` |
| 适用问题 | 投放大盘、渠道/国家/campaign 归因、SDK vs AF 回收、预测版本差异 |

## 分析顺序

1. 固定筛选口径：
   - `active_date`
   - `bundle_id`
   - `country`
   - `forecast_version`
   - `revenue_source`
2. 先看 summary / 默认日期趋势。
3. 下钻 `media_source` 和 `country`。
4. 再下钻 `campaign_name` / `adset_name` / `ad_name`。
5. 对比 `revenue_source=sdk` 与 `revenue_source=af`。
6. 对比 `forecast_version=v6` 与纠偏/其它版本。
7. 将定位出的异常回到 `数据资产目录` / `数据资产目录` 做 SQL 复核。

## 标准输出

```text
问题：
口径：
关键发现：
证据：
判断：
下一步建议：
风险 / 待确认：
```

## 注意事项

- Campaign 候选只作为人审线索，不自动执行投放动作。
- summary 不等于 rows 平均。
- 长线 ROI 可能包含预测 / 纠偏，不一定是完全成熟真实回收。
- SDK 与 AF 回收源必须显式说明。
- 不保存 token / cookie / Authorization。
