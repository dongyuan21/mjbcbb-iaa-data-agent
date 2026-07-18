# 20260615 ai_hive PII 护栏问题记录

> 记录日期：2026-06-15
> 范围：`ai_hive/` 表知识库的 PII（个人可识别信息）护栏一致性
> 触发：ai_hive 建设水平评审，发现 PII 标注残缺且真理源分散
> 政策依据：本工程 `AGENTS.md` Always Applied Rule 5「不保存 AK/SK、数据库密码、SSO ticket、MI token、cookie、用户级明细、设备 ID、IP、user_agent」
> 真理源现状：`tables/*.yaml` 由 `tools/scripts/sync_ai_hive_schema.py` 等同步；PII 标注字段 `query_rules.pii_columns_do_not_log` 当前靠人手填，无脚本维护。

## 一、问题是什么（先对齐概念）

- **PII** = 能定位到某个具体人/某台具体设备的字段。本库实存：设备/广告标识 `device_id`/`gaid`/`idfa`/`idfv`/`oaid`/`android_id`、网络位置 `ip`/`ip_address`/`client_ip_address`/`latwgs`/`lngwgs`/`user_agent`、账号联系 `account_id`/`email`/`s_pushtoken`/`customer_user_id`/`appsflyer_id`/`distinct_id`。
- **要防的不是库内脱敏**，而是 agent 自动生成并执行 SQL 时，把这些列的**原始明细值带进 LLM 上下文 / 聊天记录 / 第三方模型日志**（即 AGENTS.md 第 5 条想防的事）。
- 护栏的载体是表卡里的 `query_rules.pii_columns_do_not_log`：告诉 agent「这张表里这几列别 SELECT/输出/打印」。

## 二、证据（100 张卡全库扫描，2026-06-15）

### 问题 1（P0）标注覆盖严重不足且不一致

| PII 列 | 出现在多少卡的列定义 | 被标进 pii 禁列的卡数 | 缺口 |
|---|---|---|---|
| `device_id` | 42 | 21 | 21 张漏标 |
| `idfv` | 11 | 1 | 10 张漏标 |
| `latwgs` / `lngwgs`（经纬度） | 12 / 12 | 0 / 0 | 全部漏标 |
| `user_agent` | 12 | 2 | 10 张漏标 |
| `account_id` | 19 | 0 | 全部漏标 |
| `oaid` / `android_id` | 5 / 5 | 0 / 0 | 全部漏标 |
| `ip` | 21 | 18 | 3 张漏标 |

另有 **52 张卡 `pii_columns_do_not_log` 为空**。结论：该字段残缺，agent 读到的护栏时有时无。

### 问题 2（P0）三处真理源互相打架，无权威全集

| 位置 | 声明的 PII 禁列 |
|---|---|
| `agent_manifest.yaml` hard_rules | `gaid, idfa, ip, user_agent`（4 个） |
| `数据地图.md` 查询护栏 | `idfa/gaid/ip`（3 个） |
| 各 `tables/*.yaml` | 各列各的（device_id/distinct_id/email/s_pushtoken…不统一） |
| `AGENTS.md` 顶层 | 「设备 ID、IP、user_agent、用户级明细」（口径，非列名清单） |

agent 加载单文件只看到残缺清单，拿不到一份 canonical 全集，也没有脚本能据此校验。

### 问题 3（P1）PII 语义二元化过粗

`distinct_id` / `appsflyer_id` / `customer_user_id` / `device_id` / `account_id` 既是 PII，又是**必需的 join 键 / 去重键**。例如 `口径决策记录.md` 的安装/激活分母 SQL：

```sql
COUNT(DISTINCT COALESCE(customer_user_id, appsflyer_id))
```

一个布尔「禁列」会让 agent 要么违规、要么不敢用 → 连分母都算不出。需分两档：彻底禁输出 vs 允许聚合/join、禁输出明细。

## 三、整改方案（建 canonical 字典 + 脚本自动盖章，根治散填）

1. 新增 `ai_hive/PII_POLICY.yaml` 单一真理源，两档分类：
   - `forbidden_output`：绝不可 SELECT/输出/日志（gaid/idfa/idfv/oaid/android_id/ip/ip_address/client_ip_address/user_agent/latwgs/lngwgs/email/s_pushtoken/activation_madid…）
   - `aggregation_only`：可做 join / `COUNT(DISTINCT)`，禁落明细行（distinct_id/device_id/appsflyer_id/customer_user_id/account_id/uuid）
2. 新增脚本 `tools/scripts/stamp_ai_hive_pii.py`：对每张卡取 `PII_POLICY ∩ 该卡实际列`，自动写回 `pii_columns_do_not_log` + 新增 `pii_aggregation_only`，消除手工漏标；并接入 `sync_ai_hive_schema.py` 流程，使后续新表自动盖章。
3. `agent_manifest.yaml` hard_rules / `数据地图.md` 改为**指向** `PII_POLICY.yaml`，不再硬编码列名；新增一条「聚合键可用于 COUNT/JOIN，禁输出明细」。

## 四、验收（整改后应满足）

- 所有卡的 PII 标注 = `PII_POLICY ∩ 实际列`，无漏标（脚本可复核）。
- `agent_manifest` / `数据地图` / 表卡三处口径一致，单一真理源为 `PII_POLICY.yaml`。
- YAML 全合法；catalog / rag_bundle 重生成。

## 五、拍板结论（2026-06-15 用户确认）

1. **本护栏要做** —— ai_hive 面向 JoyDataAgent/Datus/Cursor 自动生成+执行 SQL，护栏必要。
2. **`appsflyer_id` / `customer_user_id` → `aggregation_only`**（分母 SQL 必须用）。✅
3. **经纬度 `latwgs/lngwgs` → `forbidden_output`；`country/city_cn` 保留可用**。✅
4. **接入 `sync_ai_hive_schema.py`** 自动盖章（根治"下次又失配"）。✅

## 六、整改执行结果（2026-06-15 已完成）

| 编号 | 级别 | 问题 | 处置 | 状态 |
|---|---|---|---|---|
| HIVE-PII-01 | P0 | PII 标注覆盖不足且不一致（52 空 / device_id 21 漏 / 经纬度全漏） | 建 `PII_POLICY.yaml` + `stamp_ai_hive_pii.py` 自动盖章 100 卡；脚本内置写后重载断言 | done |
| HIVE-PII-02 | P0 | 三处真理源打架，无 canonical 全集 | `agent_manifest.yaml` 新增 `pii_policy:` 指针、hard_rules 去硬编码列名；`数据地图.md` 护栏改指向 `PII_POLICY.yaml`；`README.md` 目录树补 PII_POLICY | done |
| HIVE-PII-03 | P1 | PII 语义二元化过粗，未区分聚合键 | 两档分类：`forbidden_output`（禁输出）vs `aggregation_only`（可 JOIN/COUNT(DISTINCT)，禁明细）；各卡新增 `pii_aggregation_only` | done |

**落地清单**
- 新增 `ai_hive/PII_POLICY.yaml`（forbidden_output 33 列名 / aggregation_only 10 列名 / not_pii_lookalikes 9 列名 + 行为规则）。
- 新增 `tools/scripts/stamp_ai_hive_pii.py`：定点文本补丁（不整文件 re-dump，最小 diff），可 `import` 供 sync 调用 `stamp_all()`。
- `tools/scripts/sync_ai_hive_schema.py`：main() 末尾调用 `stamp_all()` 统一覆盖弱内联推断；新表同步即自动盖章。
- `tools/scripts/export_ai_hive_rag_bundle.py`：每卡导出 `pii_forbidden_output` / `pii_aggregation_only` 两行，agent 经 RAG 也能拿到护栏。

## 七、验收

- 100 卡盖章命中：forbidden_output 46 卡 / aggregation_only 66 卡。
- 一致性校验：100 卡 `pii_columns_do_not_log` == `PII_POLICY ∩ 该卡实际列`，**全部一致**。
- 幂等性：重复跑 `stamp_ai_hive_pii.py` 无额外 diff。
- 典型修复：`dwd_kcolb_tsalb_ios_white_event_realtime_hi` 从仅标 `[ip]` → `[account_id, device_id, distinct_id, ip, latwgs, lngwgs, uuid]`（此前 latwgs/lngwgs/account_id 全漏）。
- YAML 全合法；catalog/rag_bundle 重生成；两脚本 `py_compile` 通过。

## 八、遗留观察项

1. 列名按精确匹配。若后续同步引入新的 PII 列变体（如新媒体 API 的 id 字段），需登记进 `PII_POLICY.yaml` 再跑盖章；可定期用 token 扫描审计漏网列名。
2. 护栏是"知识层"约束（告诉 agent 别输出），非运行时强制；是否在执行层加 PII 列拦截（如 SQL 静态检查）属另一议题，未做。
3. **JSON 内嵌 PII 绕过列名匹配（2026-06-15 Cursor dogfood 发现）**：盖章按"列名"匹配，但有的 PII 以 JSON 形式藏在普通列里（如 `ods_appsflyer_all_in_app_events_report_di` 的 `custom_data`，`get_json_object(custom_data,'$.ta_distinct_id')` 抽出的是用户级 id）。该卡 example_queries 里的 `campaign_users` 正是 `SELECT DISTINCT` 这个抽取值，列名匹配抓不到。后续：对 `custom_data`/`properties`/`event_properties` 等 JSON 容器列做 `aggregation_only` 级提示，或在执行层处理。属"后续话题"，不硬补。
