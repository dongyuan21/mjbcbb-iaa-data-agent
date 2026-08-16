# Runtime 复核 Goal 模板

## 适用场景

- 要按日期批量复核 Data Agent Runtime 日志；
- 需要 Codex 持续执行、复跑、写报告，而不是一次性聊天结论；
- 希望把 reviewer 工作做成稳定 SOP。

## 推荐 Goal 目标

```text
复核指定日期的 Data Agent Runtime 调用日志，完成问题去重、MC/CK live 验证、失败样本诊断、必要的 Runtime 修复、test 环境线上复跑与报告沉淀
```

## 推荐模型

- 长执行 reviewer 任务优先使用 `codex5.3-spark`。
- 目标不是更会“做题”，而是更稳定地走完日志读取、live probe、复跑、报告这条链。

## 推荐计划拆分

1. 读取 MySQL session / message / trace / query_records，完成问题去重。
2. 建立 MC / CK live probe 能力，确认目标表当前分区。
3. 逐个复核失败样本，区分口径问题、数据问题和 Runtime 问题。
4. 只有确认是 Runtime 缺陷时才改代码，并补本地验证。
5. 发布 test 环境，线上 replay 目标问题。
6. 核验新 trace / query_records / assistant metadata 是否完整。
7. 生成带日期报告，明确未修复项和后续动作。

## 输入模板

```text
复核日期：
日志范围：
是否只读：
是否允许发布 test：
目标问题（如有）：
报告目录：
```

## 完成标准

- 能说清 trace 总数、唯一问题数和去重规则；
- MC / CK live probe 已执行；
- 每个失败样本都有根因和证据；
- 如有修复，已经完成 test replay；
- 报告文件名带日期；
- 未修复项单独列出，不弱化成建议。
