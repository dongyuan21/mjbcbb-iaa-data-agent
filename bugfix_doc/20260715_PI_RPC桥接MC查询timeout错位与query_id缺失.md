# 2026-07-15 PI RPC 桥接 MC 查询 timeout 错位与 query_id 缺失

## 问题概览

| 项 | 内容 |
|---|---|
| 编号 | BUGFIX-20260715-PI-RPC-MC-TIMEOUT-QUERYID |
| 级别 | P0 稳定性 + 可观测性 + 安全 三重缺口 |
| 状态 | 离线实现与行为回归完成，未部署 |
| 问题类型 | timeout 错位 + instance_id 丢失 + logview token 泄漏 |

## 根因（9 项）

1. TS 层 180s 单值 timeout 对 MC 错杀
2. ODPS instance.id 用完即丢
3. QueryRecord 无 instance_id 列
4. logview_url 携带签名 token 泄漏到 PI JSON / 模型上下文 / trace
5. helper 优先选本机旧版，仓库改动不生效
6. timeout 阶梯不对齐（PI idle 300s < TS 600s；父子同值）
7. wait_with_timeout 只看 is_terminated() 不看 is_successful()
8. helper 540s 超时以普通非零码退出，父层会误分类为 `executor_failed`
9. helper 在首次 flush instance_id 之前调用 logview 生成，该调用阻塞时仍可丢 query_id

## 修复方案

### timeout 阶梯（修复后）

| 层 | timeout | 余量 |
|---|---|---|
| helper `wait_with_timeout` | 540s | 最内层 |
| `run_mc` subprocess | 570s | +30s |
| TS extension MC | 600s | +30s |
| PiRpcAgent idle | 630s | +30s |
| PiRpcAgent total | 900s | 总兜底 |

所有 MC 路径（agent、executors、data_tools、bootstrap）统一使用 570s。

### 安全边界

- helper 创建 instance 后立即单独 flush `odps_instance_id`；只在查询已成功终止后探测 `logview_available: bool`，**绝不输出 raw logview URL**
- `_parse_odps_meta()` 白名单仅接受 `odps_instance_id` + `logview_available`；限制 metadata 大小、instance id 字符集/长度，要求 availability 为真正的 JSON boolean，并合并多行 metadata 中每个字段的第一个合法值
- `_exec` 返回 `logview_available: bool`，raw URL 永不跨进程
- `output_summary` 过滤 `logview_url` + `odps_instance_id` + `logview_available`
- QueryRecord 存 `logview_available Boolean`，不存 raw URL
- `_strip_odps_meta()` 从 error message 剥离 `__ODPS_META__` 行

### 终态校验

`wait_with_timeout` 在 `is_terminated()` 返回 True 后调用 `is_successful()`，非成功抛 SystemExit。
内层 helper 超时会尝试 `instance.stop()`，输出不含 SQL/rows 的错误摘要，并以保留退出码 `124` 结束；同步与异步父层均将其映射为 `executor_timeout`。

### 错误分类

- adapter 或 backend 父进程硬超时：`executor_timeout`
- helper 超时保留退出码 `124`：`executor_timeout`
- helper 其他非零退出：`executor_failed`
- helper stdout 非 JSON：`executor_invalid_json`
- canonical freshness 边界将 `executor_timeout` 归一为现有对外契约 `timeout`，不误标为 `freshness_probe_failed`

### helper 优先级

bundled（repo）优先，local（~/.maxcompute-dataworks）兜底。

## 改动文件（12 改 + 3 新）

| 文件 | 改动 |
|---|---|
| `readonly_data_query.ts` | timeout MC 600s / CK 60s 分档；TS 自身硬超时单独标记 `executor_timeout` |
| `maxcompute_sql.py` ×2 | 两阶段 print_odps_meta + wait_with_timeout(540s, is_successful, timeout stop, exit 124) |
| `data_query.py` | 多行 metadata 白名单合并 + _strip_odps_meta + timeout 124 分类 + run_mc 570s + helper 优先级 |
| `executors.py` | 多行 metadata 合并 + _strip_odps_meta + timeout 124 分类 + QueryResult 加字段 + run_maxcompute 570s |
| `config.py` | PI idle 630s + helper 优先级 |
| `models.py` | QueryRecord 加 odps_instance_id + logview_available + 索引 |
| `persistence.py` | 两个入口 + record dict + output_summary 过滤 |
| `verified_sql_bootstrap.py` | 透传 + timeout 570s |
| `analysis_contract_bootstrap.py` | 透传 + timeout 570s |
| `data_tools.py` | timeout 570s |
| migration 0009 | 加列 + 索引 |
| `test_odps_query_safety.py` | fake instance/subprocess、metadata 边界、超时分类、持久化、migration、source/dist 一致性回归 |
| 本文档 | 记录根因、安全边界、验收证据与待部署状态 |
| `bugfix_doc/README.md` | 将本修复纳入 bugfix 当前记录索引 |

## 验收

| 项 | 状态 |
|---|---|
| 改动 Python 文件 py_compile | 已通过 |
| raw logview_url 不出现在任何 _exec 返回 | 已验证 |
| is_successful() 在两个 helper 中 | 已验证 |
| timeout 阶梯 540/570/600/630/900 严格递增 | 已验证 |
| 所有 MC 路径 timeout 统一 570s | 已验证 |
| 新增专项行为回归 | 60 passed |
| 相关 backend 回归 | 223 passed |
| backend 全量回归 | 921 passed，1 条既有第三方 deprecation warning |
| `tools/scripts/tests` 全量回归 | 117 passed |
| PI replay `--validate-only` | pass（15 cases，0 errors） |
| PI extension 加载与只读检查 | PASS |
| migration 0009 真实 upgrade / downgrade（临时 SQLite） | PASS |
| 真实 MC 长查询 / 山海部署验证 | 未执行，保留为下一安全步骤 |
