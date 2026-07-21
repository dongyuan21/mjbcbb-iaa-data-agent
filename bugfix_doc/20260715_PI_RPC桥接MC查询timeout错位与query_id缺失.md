# 20260715 PI RPC 桥接 MC 查询 timeout 错位与 query_id 缺失

> 记录日期：2026-07-15
> 范围：PI RPC 桥接 MaxCompute 查询链路
> 级别：P0 稳定性 + 可观测性 + 安全三重缺口
> 状态：离线实现与行为回归完成，未部署

## 一、问题

PI 通过 TS extension 调用 MaxCompute 查询时，timeout 错位、ODPS instance_id 丢失、logview URL 携带签名 token 泄漏三重缺口同时存在：

1. **timeout 错位**：TS 层 180s 单值 timeout 对 MC 长查询错杀；PI idle 300s < TS 600s，父子同值；`wait_with_timeout` 只看 `is_terminated()` 不看 `is_successful()`。
2. **instance_id 丢失**：ODPS instance.id 用完即丢；QueryRecord 无 instance_id 列；helper 在首次 flush instance_id 之前调用 logview 生成，该调用阻塞时仍可丢 query_id。
3. **logview token 泄漏**：logview_url 携带签名 token 泄漏到 PI JSON / 模型上下文 / trace。
4. **helper 优先级错**：helper 优先选本机旧版，仓库改动不生效；helper 540s 超时以普通非零码退出，父层误分类为 `executor_failed`。

## 二、解决方案

### 1. timeout 阶梯对齐

| 层 | timeout | 余量 |
|---|---|---|
| helper `wait_with_timeout` | 540s | 最内层 |
| `run_mc` subprocess | 570s | +30s |
| TS extension MC | 600s | +30s |
| PiRpcAgent idle | 630s | +30s |
| PiRpcAgent total | 900s | 总兜底 |

所有 MC 路径（agent、executors、data_tools、bootstrap）统一 570s。每层留 30s 余量，避免父层先于子层超时。

### 2. 安全边界（logview token 不跨进程）

- helper 创建 instance 后立即单独 flush `odps_instance_id`；只在查询成功终止后探测 `logview_available: bool`，**绝不输出 raw logview URL**。
- `_parse_odps_meta()` 白名单仅接受 `odps_instance_id` + `logview_available`；限制 metadata 大小、instance id 字符集/长度，要求 availability 为真正的 JSON boolean。
- QueryRecord 存 `logview_available Boolean`，不存 raw URL；`output_summary` 过滤 `logview_url` + `odps_instance_id` + `logview_available`；`_strip_odps_meta()` 从 error message 剥离 `__ODPS_META__` 行。

### 3. 终态校验 + 错误分类

`wait_with_timeout` 在 `is_terminated()` 返回 True 后调用 `is_successful()`，非成功抛 SystemExit。内层 helper 超时尝试 `instance.stop()`，输出不含 SQL/rows 的错误摘要，保留退出码 `124`；父层映射为 `executor_timeout`。

| 错误形态 | 分类 |
|---|---|
| adapter/backend 父进程硬超时 | `executor_timeout` |
| helper 超时保留退出码 124 | `executor_timeout` |
| helper 其他非零退出 | `executor_failed` |
| helper stdout 非 JSON | `executor_invalid_json` |

canonical freshness 边界将 `executor_timeout` 归一为对外契约 `timeout`，不误标为 `freshness_probe_failed`。

### 4. helper 优先级

bundled（repo）优先，local（`~/.maxcompute-dataworks`）兜底。

## 三、验收

| 项 | 结果 |
|---|---|
| 改动 Python 文件 py_compile | 通过 |
| raw logview_url 不出现在任何 _exec 返回 | 已验证 |
| timeout 阶梯 540/570/600/630/900 严格递增 | 已验证 |
| 新增专项行为回归 | 60 passed |
| backend 全量回归 | 921 passed |
| `tools/scripts/tests` 全量回归 | 117 passed |
| PI replay `--validate-only` | pass（15 cases，0 errors） |
| migration 0009 真实 upgrade/downgrade | PASS |
| 真实 MC 长查询 / 山海部署验证 | 未执行，保留为下一安全步骤 |

## 四、遗留观察项

- 真实 MC 长查询和山海部署验证未执行，保留为下一安全步骤。

## 五、方法论沉淀

1. **timeout 阶梯必须严格递增且每层留余量**：父层 timeout 要大于子层，避免父层先超时导致子层结果丢失；同值或倒置会让超时分类错乱。
2. **签名 token 绝不跨进程**：logview URL 带签名，跨进程会泄漏到模型上下文/trace；只传 `logview_available: bool`，raw URL 留在 helper 进程内。
3. **ODPS instance_id 要尽早 flush**：在 logview 生成之前单独 flush instance_id，避免后续阻塞导致 query_id 丢失。
4. **helper 优先级要 repo 优先**：本机旧版 helper 优先会导致仓库改动不生效，必须 bundled 优先、local 兜底。
5. **超时退出码要保留并映射**：helper 超时用 `124` 退出码，父层据此映射为 `executor_timeout`，不用普通非零码避免误分类为 `executor_failed`。
