# AB3.0 实验 ID 提取规则

> 状态：active  
> 创建日期：2026-06-19  
> 适用范围：AB Orthogonal 3.0 广告实验 ID，尤其是白名单事件表 `properties.s_ad_public_adwaynum_array` 中的插屏、激励、banner 分层实验号。

## 使用边界

本文用于识别和提取 AB3.0 实验 ID，不直接提供 verified SQL。

可以作为当前默认规则使用：

- 判断 `fs` / `rv` / `ba` 开头的实验 ID 属于 AB3.0。
- 从事件 `properties` 的 `s_ad_public_adwaynum_array` 中提取对应广告层的 `waynum`。
- 规范 WHERE、SELECT、GROUP BY 中应该使用哪个提取字段。

不能直接作为 verified 事实使用：

- 未经过表卡、schema probe 或小窗口验证的表字段。
- 未确认 JSON 格式是否稳定的历史数据。
- 示例正则对应的 SQL 执行结果。

## 实验 ID 层级

| 前缀 | layer | 广告层 | 输出字段建议 |
|---|---|---|---|
| `fs` | `insert` | 插屏 | `insert_waynum` |
| `rv` | `reward` | 激励 | `reward_waynum` |
| `ba` | `banner` | banner | `banner_waynum` |

AB3.0 实验 ID 存在于 `properties.s_ad_public_adwaynum_array`，常见结构：

```json
[
  {"layer": "banner", "waynum": "ba10606"},
  {"layer": "insert", "waynum": "fs10606"},
  {"layer": "reward", "waynum": "rv10606"}
]
```

## 提取方式

推荐在 CTE 中先提取三层方案号，再在外层过滤和聚合：

```sql
regexp_extract(
  GET_JSON_OBJECT(properties, '$.s_ad_public_adwaynum_array'),
  '"layer":"banner","waynum":"([^"]+)"',
  1
) AS banner_waynum,
regexp_extract(
  GET_JSON_OBJECT(properties, '$.s_ad_public_adwaynum_array'),
  '"layer":"insert","waynum":"([^"]+)"',
  1
) AS insert_waynum,
regexp_extract(
  GET_JSON_OBJECT(properties, '$.s_ad_public_adwaynum_array'),
  '"layer":"reward","waynum":"([^"]+)"',
  1
) AS reward_waynum
```

如果源数据 JSON 可能包含空格，先做 schema / 小窗口验证；必要时把正则改成允许空白字符的版本。

## SQL 规则

当用户查询的实验 ID 以 `fs`、`rv`、`ba` 开头时：

- 必须从 `s_ad_public_adwaynum_array` 提取对应层的 `waynum`。
- WHERE 条件使用提取后的字段，例如 `insert_waynum IN (...)`。
- SELECT / GROUP BY 使用提取后的 `insert_waynum`、`reward_waynum` 或 `banner_waynum`。
- 不用旧字段 `s_ad_public_adwaynum` 直接匹配 AB3.0 实验。
- 输出中说明使用了 AB3.0 分层提取规则。

旧格式实验，例如 `8865xxxx` 仍使用旧字段 `s_ad_public_adwaynum`，但必须在输出中说明这是旧格式实验。

如果同一个需求同时包含 AB3.0 和旧格式实验：

- 优先分两个 CTE 处理。
- 或在各自提取后用 `COALESCE` 合并为统一实验维度。
- 不要把旧字段和 AB3.0 array 字段混在同一个 WHERE 条件里猜。

## 与商业化 SQL 的关系

AB3.0 经常出现在商业化链路和广告实验查询中。涉及 `ad_load_end`、`s_ad_show_action`、插屏 / 激励 / banner 分层分析时，同时遵守：

- `商业化SQL协议.md`
- `白名单事件表查询协议.md`

具体表字段、分区、PII、freshness 和 example query 仍以 `ai_hive/agent_knowledge/tables/` 为准。
