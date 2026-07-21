# 游戏名与 bundle_id 双向速查

```yaml
knowledge_status: trial_active
facts_level: trial_support_mapping
applies_to_current: true
source_type: prj_pag_list_probe
source_table: shucang_market.prj_pag_list + MI ROI360 页面字段字典
verified_at: 2026-06-24 / 2026-07-06
machine_readable_source: knowledge/agent_knowledge/report_knowledge/PACKAGE_BUNDLE_MAP.csv
```

## 使用边界

- 这是游戏 / 产品名与各端 `bundle_id` 的速查映射，支持“游戏名 -> bundle_id”和“bundle_id -> 游戏名 / 平台”双向查询。
- 2026-07-06 补入 Double Tile iOS、Word Solitaire Go GP、Arrows Blast iOS，来源为 `ai_ck/agent_knowledge/metrics/mi_roi360_page_field_dictionary.json`。
- 这不是 PGP 点位白名单、S2S 回传白名单，也不是大数据仓库权限白名单。
- 如果用户明确要求跑数、生成 SQL、查消耗 / 回收 / DNU，转 `text2sql_or_sql_planning` 或对应业务分析路由。
- 如果用户问 PGP 点位、S2S event、应推 / 实推、Campaign / AdSet 映射，转 `point_s2s_analysis`。

## 游戏名 -> bundle_id

| 游戏 / 产品 | 平台 | bundle_id |
|---|---|---|
| Block Blast | GP | `com.block.juggle` |
| Block Blast | iOS | `com.blockpuzzle.us.ios` |
| Mahjong Blast | GP | `com.nebula.mahjongtile` |
| Mahjong Blast | iOS | `com.nebula.mahjongtile.ios` |
| Jade Mahjong | GP | `com.wonderful.mahjong` |
| Jade Mahjong | iOS | `com.wonderful.mahjong.ios` |
| Block Crush | GP | `com.wood.block.sudoku.puzzle.bm` |
| Block Crush | iOS | `com.blockcrush.travelmaster` |
| Sudoku Master | GP | `com.mathbrain.sudoku` |
| Sudoku Master | iOS | `com.mathbrain.sudoku.ios` |
| Double Tile | GP | `com.hungrystudio.mahjong` |
| Double Tile | iOS | `com.hungrystudio.mahjong.ios` |
| Solitaire Master | GP | `solitaire.classic.hungrystudio.free.klondike.card.patience` |
| Solitaire Master | iOS | `solitaire.hungrystudio.freecard` |
| Tap Tile | GP | `com.nebula.tiles` |
| Tap Tile | iOS | `com.nebula.tiles.ios` |
| Nut Sort GO | iOS | `com.nebula.nutsort.ios` |
| Word Solitaire Go | GP | `com.nebula.wordsolitaire` |
| Word Solitaire Go | iOS | `com.nebula.wordsolitaire.ios` |
| Arrows Blast | GP | `com.nebula.arrows` |
| Arrows Blast | iOS | `com.nebula.arrows.ios` |

## bundle_id -> 游戏名 / 平台

| bundle_id | 游戏 / 产品 | 平台 |
|---|---|---|
| `com.block.juggle` | Block Blast | GP |
| `com.blockcrush.travelmaster` | Block Crush | iOS |
| `com.blockpuzzle.us.ios` | Block Blast | iOS |
| `com.hungrystudio.mahjong` | Double Tile | GP |
| `com.hungrystudio.mahjong.ios` | Double Tile | iOS |
| `com.mathbrain.sudoku` | Sudoku Master | GP |
| `com.mathbrain.sudoku.ios` | Sudoku Master | iOS |
| `com.nebula.arrows` | Arrows Blast | GP |
| `com.nebula.arrows.ios` | Arrows Blast | iOS |
| `com.nebula.mahjongtile` | Mahjong Blast | GP |
| `com.nebula.mahjongtile.ios` | Mahjong Blast | iOS |
| `com.nebula.nutsort.ios` | Nut Sort GO | iOS |
| `com.nebula.tiles` | Tap Tile | GP |
| `com.nebula.tiles.ios` | Tap Tile | iOS |
| `com.nebula.wordsolitaire` | Word Solitaire Go | GP |
| `com.nebula.wordsolitaire.ios` | Word Solitaire Go | iOS |
| `com.wood.block.sudoku.puzzle.bm` | Block Crush | GP |
| `com.wonderful.mahjong` | Jade Mahjong | GP |
| `com.wonderful.mahjong.ios` | Jade Mahjong | iOS |
| `solitaire.classic.hungrystudio.free.klondike.card.patience` | Solitaire Master | GP |
| `solitaire.hungrystudio.freecard` | Solitaire Master | iOS |

## 回答模板

命中游戏名时：

```text
<游戏名> 当前映射：
- <平台>: `<bundle_id>`

来源：PACKAGE_BUNDLE_MAP.csv，源表 shucang_market.prj_pag_list，verified_at=<日期>。
```

命中 bundle_id 时：

```text
`<bundle_id>` 对应 <游戏名> / <平台>。

来源：PACKAGE_BUNDLE_MAP.csv，源表 shucang_market.prj_pag_list，verified_at=<日期>。
```
