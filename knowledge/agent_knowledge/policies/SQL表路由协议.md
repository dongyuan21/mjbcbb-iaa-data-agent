# SQL 表路由协议

> 状态：active  
> 创建日期：2026-06-19  
> 适用范围：MaxCompute / ODPS 业务 SQL 的产品、端、主题表和粒度选择。

## 使用边界

本文规定“需求应该先路由到哪类表”，不是表卡、DDL 或 verified SQL。

可以作为当前默认规则使用：

- 根据产品、端、主题和指标选择候选表类型。
- 判断用户需求应先走用户属性、用户行为、留存、实验、投放、商业化、局 / 轮 / 块、埋点元数据还是 ROI 预测主题。
- 生成 SQL 前列出还需要表卡、schema 或小窗口验证的字段证据。

不能直接作为 verified 事实使用：

- 不在 `ai_hive/agent_knowledge/catalog.yaml` 或 `ai_hive/agent_knowledge/tables/` 中的具体表名。
- 没有 live schema / dry-run / 小窗口验证的字段。
- 未经 `da_assets/SQL晋升治理.md` 晋升的 SQL。

如果路由到的表不在当前 `ai_hive/agent_knowledge/catalog.yaml`：

```text
candidate_table_requires_intake
```

Agent 可以把它作为补表线索，但不能默认用它生成“已验证 SQL”。若用户要求继续写 SQL，必须先通过 `maxcompute-dataworks` 做 schema probe 或小窗口验证，并在输出中标明验证状态。

## 产品和端过滤

| 产品 | GP bundle_id | GP app_name | iOS bundle_id | iOS app_name | 说明 |
|---|---|---|---|---|---|
| block blast | `com.block.juggle` | `block_blast_gp` | `com.blockpuzzle.us.ios` | `block_blast_ios` | BB 双端通常有独立 GP / iOS 表，也有 all 聚合表。 |
| mahjong blast | `com.nebula.mahjongtile` | `nova_mahjong_gp` | `com.nebula.mahjongtile.ios` | `nova_mahjong_ios` | MB 通常走 nova collection 表族，必须带 `app_name`。 |
| double tile | `com.hungrystudio.mahjong` | `block_mahjong_gp` | `com.hungrystudio.mahjong.ios` | `block_mahjong_ios` | DT 通常走 block collection 表族，必须带 `app_name`。 |
| block crush | 待确认 | `block_crush_gp` | 待确认 | `block_crush_ios` | 当前只可按 `app_name` 路由，bundle_id 需补证据。 |
| jade mahjong | `com.wonderful.mahjong` | `jade_mahjong_gp` | `com.wonderful.mahjong.ios` | `jade_mahjong_ios` | 通常走 nova collection 表族。 |
| nova block | `com.nebula.blockpuzzle` | `nova_block_gp` | `com.blockpuzzle.nebula.ios` | `nova_block_ios` | 通常走 nova collection 表族。 |
| MathCross | `com.nebula.crossmath` | `cross_math_gp` | `com.nebula.crossmath.ios` | `cross_math_ios` | 通常走 nova collection 表族。 |

表名、`app_name`、`bundle_id` 三者出现冲突时：

1. 先以用户明确指定为准。
2. 再以表卡 / verified SQL 的产品过滤为准。
3. 仍冲突时输出 `product_filter_conflict`，不要自行合并。

## 主题表路由

| 主题 | 适用问题 | 优先查找表族 / 关键词 | 最细粒度 | 必要过滤 |
|---|---|---|---|---|
| 白名单事件主题 | 埋点事件、漏斗、链路、事件参数 | `white_event_unique_data` | 事件 × 人 × 天 / 小时 | 必须带 `dt`、`event_name`；共享表必须带 `app_name`。 |
| 用户属性主题 | 用户安装属性、生命周期、标签、设备属性 | `user_ha`、`user_label`、`device` | 用户 / 设备快照 | 全量快照取最新 `dt` / `hour`；不要扫用户级明细输出。 |
| 用户行为主题 | DAU、时长、局数、冷启、广告行为聚合 | `user_multi_dim` | 用户 × 天 | 增量表按业务日期窗口过滤；共享表必须带 `app_name`。 |
| 用户留存行为主题 | RR1 / RR3 / RR7、新用户留存、活跃留存 | `retention` | 用户 × 留存日 | 全量表要区分分区日和 `active_date` / `install_date` / `retention_date`。 |
| 实验方案主题 | 产品实验、方案效果、AB 组别 | `abtest_user_multi_dim` | 用户 × 天 × 方案号 | 缺起止时间时先查配置表，不直接反问。 |
| 方案用户留存主题 | 实验留存、人均留存天数、方案留存对比 | `ab_retention` | 用户 × 留存日 × 方案号 | 实验场景不要把人均留存天数误写成 RR。 |
| 商业化实验主题 | 插屏 / 激励实验、action / ready、广告收入 | `ad_realization` | 用户 × 方案号 × 留存日 | 先区分商业化实验、商业化链路、广告收入。 |
| 投放主题 | campaign / adset / ad、国家、渠道、成本、ROAS | `ad_detail`、`spend`、`cost`、`appsflyer` | 渠道 × 国家 × campaign / ad × 留存日 | 保护 campaign 原始名称；campaign_id 可作稳定 join fallback。 |
| ROI 预估主题 | 预估 LTV / ROI、投放预估偏差 | `roi_pred`、`revenue_predict` | 渠道 × 国家 × campaign / ad × 留存日 | 必须区分预估值和真实回收，按当前 ROI 预测政策选版本。 |
| 局粒度主题 | 局级玩法、胜负、复活、无尽 / 旅行模式 | `block_action_game`、`parsed_board_game_click` | 用户 × 天 × 局 | 优先局表；只有需求需要更细粒度才下钻。 |
| 轮维度主题 | 轮级玩法过程、回合内行为 | `block_action_round` | 天 × 用户 × 局 × 轮 | 只有局表无法覆盖时使用。 |
| 出块维度主题 | 块级行为、放置、消除、局内细节 | `block_action_block` | 天 × 用户 × 局 × 轮 × 块 | 仅在轮表仍无法覆盖时使用，避免默认扫块表。 |
| 模型特征工程主题 | 用户特征、模型输入、点位候选特征 | `user_feature` | 用户 × 天 | 只作特征解释或特征验证，不自动替代业务事实表。 |
| 素材映射主题 | 素材、广告素材、media material 映射 | `material`、`ad_material_maps` | 素材 / ad / campaign | 先确认媒体、campaign、ad 层级和命名。 |
| 埋点元数据主题 | 事件定义、参数定义、hudi 字段映射 | `bi_events`、`bi_attr`、`games_project` | 产品 × 事件 / 参数 | 只解释事件和参数，不当作行为发生事实。 |

白名单事件表的具体查询护栏见 `白名单事件表查询协议.md`；商业化链路和商业化实验见 `商业化SQL协议.md`；产品实验配置和方案效果见 `实验配置与方案查询规则.md`；投放、AF 激活、成本、SDK 收入和 ROI 预估见 `投放与ROI预估SQL协议.md`；用户行为 / 留存 / 画像见 `用户行为留存画像查询规则.md`；Block Blast 局 / 轮 / 出块下钻见 `局轮出块粒度查询规则.md`；模型特征和埋点元数据见 `特征工程与埋点元数据查询规则.md`；皇室麻将 / MB 看板专项见 `皇室麻将BI看板查询规则.md`。

## 全量表和增量表

全量表：

- `dt` 代表快照分区，优先取最新可用分区或配置表对应快照分区。
- 若有 `hour`，通常取最终小时；但必须先看表卡规则。
- 业务日期范围用业务字段过滤，如 `active_date`、`install_date`、`retention_date`。

增量表：

- `dt` 通常按事件日、行为日或收入日过滤；必须下推到最内层。
- 共享事件表必须限制 `event_name`。
- 共享产品表必须限制 `app_name` 或 `bundle_id`。

不用分区或配置视图：

- 配置表 / 视图只用于补实验、商业化、方案元信息。
- 不把配置表结果当最终指标事实。

## 产品表族倾向

| 产品 / 表族 | 常见用途 | 注意事项 |
|---|---|---|
| BB GP / iOS 独立表 | BB 用户属性、行为、留存、局 / 轮 / 块、商业化实验 | 表名含 GP / iOS 时端由表名决定；不要再用另一端 app_name。 |
| nova collection all | MB、BC、JM、NB、MathCross 等 nova 系产品 | 必须带 `app_name`；MB 还有独有解析表和 BI 看板层。 |
| block collection all | DT GP / iOS | 必须带 `app_name`；DT 广告收入字段族和 BB 不同。 |
| market / AppsFlyer 表族 | 投放、归因、成本、素材、SKAN、SDK 收入 | 先按投放政策区分真实回收、预估回收、AF 安装、SKAN 聚合限制。 |
| 埋点元数据表族 | 事件和参数定义 | 适合找事件名、参数名、hudi 字段映射；不能替代事件事实表。 |

## 选表步骤

1. 标准化产品、端、时间、维度和指标。
2. 先查 verified SQL 和 semantic_contract 是否已有可复用路径。
3. 查 `ai_hive/agent_knowledge/catalog.yaml` 和对应表卡，确认候选表是否已入库。
4. 按本文主题路由选择最粗可覆盖粒度。
5. 列出字段证据：需求项、映射字段、来源表、验证来源。
6. 缺字段、缺 join key、缺表卡时输出 `待确认` 或 `candidate_table_requires_intake`。

## 维护规则

本文只维护路由和选表规则。具体字段、分区、join、PII、freshness 和 example SQL 必须回到 `ai_hive/agent_knowledge/tables/` 一表一卡治理。候选表 intake backlog 放在 `TODO/SQL写作链候选表准入积压清单.md`，不作为默认事实来源。
