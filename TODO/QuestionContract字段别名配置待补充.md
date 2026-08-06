# QuestionContract 字段别名配置待补充

状态：已完成首批本地 Test-shadow 种子；后续新增仍须业务 owner 审核。

配置文件：`runtime/backend/app/config/question_contract_filter_value_aliases.yaml`

补充后先执行：

```bash
runtime/backend/.venv/bin/python tools/scripts/check_question_contract_filter_value_aliases.py
```

该命令只输出每个字段的标准值/别名数量和配置摘要，不输出具体别名内容。

当前已写入字段专属种子：`country`、`media_source`、`bundle_id`。种子来自本地 CK 事实表 `shucang_market.tj_ad_spend_active_v2` 在 2026-07-05 至 2026-08-04 的受控枚举；`raw_exports/` 只用于发现显示名候选，未作为标准值来源。配置外的中文过滤值不会进入 QuestionContract，也不会传给路由、资产授权或 SQL。

补充规则：

- 每个字段分别维护，禁止跨字段复用别名。
- `aliases` 的每个目标必须先出现在同字段的 `canonical_values`。
- 标准值只能使用安全 ID；别名不得承载 SQL、凭证、用户明细或题干全文。
- 每次新增别名须补一条 observer 回归：别名与标准值产生相同的安全过滤摘要；未知值仍被拒绝。
- 在未完成字段口径、授权范围和测试前，不把该字段别名启用到 Test 或 Prod 证据。
- `Share-*`、`None`、邀请、分享、活动等未分类 `media_source` 不得映射为广告媒体；当前配置不为它们提供显示名别名。既有 ASCII 原值处理保持原样，不能据此宣称其属于某个广告媒体。

待补充项：

- [x] country：已种入当前 CK 观察到的两位代码；已批准 `美国 -> US`。
- [x] media_source：已种入当前 CK 观察到的 provider-style 标准值与 `organic`；尚无显示名别名。
- [x] bundle_id：已种入当前 CK 观察到的包体 ID；尚无产品显示名别名。
- [ ] country：补充其余经审核的中文国家显示名映射。
- [ ] media_source：逐条审核中文/展示名别名；需要时另建未分类来源的业务分类规则，不能猜测归属。
- [ ] bundle_id：补充经业务 owner 确认的产品名、简称到包体 ID 的映射。
