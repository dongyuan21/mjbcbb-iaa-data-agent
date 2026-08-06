# CK schema 漂移待确认

> 状态：`superseded`（2026-07-25）  
> 本文件原挂 2026-07-09 素材入库夹带漂移清单，**已过时**，勿再当当前 blocker。

## 当前请看

| 项 | 入口 |
|---|---|
| 最新漂移检测 | `ai_ck/engineering_artifacts/schema_exports/Schema漂移检测报告.md`（当前多为 `market_api_asset_spend_v1_local.spend_usd`） |
| ASA columns + spend_usd 处置 | `TODO/ASA表卡补columns段待办.md` |
| 素材三表业务待确认 | 同目录 `01` / `03`（与 schema 基线刷新无关） |

## 历史结论（勿复活）

- 07-09 素材三表 Distributed / 表卡入库相关漂移：表卡已齐，不再跟踪。
- 「`spend_usd` 已证伪删除」：已被后续间歇性漂移现象取代，以 ASA 待办为准。
- `assets_mysql_snapshot_*` Header/Body/Footer、`code_prefix_dict`、若干非 curated 新表：若再出现以**最新**漂移报告为准单独立项，不沿用本旧清单。

规则：不因本文件去跑 `probe_ck_schema.py --write`；确认预期变更后再刷基线。
