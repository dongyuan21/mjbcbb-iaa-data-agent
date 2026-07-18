# PI Runtime P0 本地实现记录（2026-06-28）

> 状态：`archived_snapshot`（历史记录，P0-1/P0-3 已于 2026-07-16 进入 test 运营阶段，当前进展见 `TODO/PI Agent能力缺口小白说明.md`）
> 来源：`TODO/PI Agent能力缺口小白说明.md` 已完成段落迁移。
> 边界：这是本地工程验收记录，不等同于 test 环境两轮 replay 通过。

## 已完成

- P0-1 Replay 门禁固化：`pi_review_tool.py replay` 和 `pi_replay_regression.py` 改为基于 `/api/chat/stream`，并输出失败分类。
- P0-2 工具治理收口：补齐 read-only、PII、`SELECT *`、分区 / limit warning、`query_records` 错误码和审计摘要。
- P0-3 Debug snapshot 失败归因增强：新增失败分类、主失败层、下一步建议、敏感字段脱敏，并把 `query_records.error_msg` 纳入 snapshot。
- P0-4 异步长查询最小闭环：新增 job 持久化模型、Alembic 迁移、job 查询 API、SSE `job_id` / 状态推进、`query_records` 回填和前端刷新恢复条。

## 本地验收

```bash
PYTHONPATH=runtime/backend python3 -m pytest runtime/backend/tests -q
npm --prefix runtime/frontend run build
npm --prefix runtime/pi run check
python3 -m py_compile runtime/backend/app/main.py runtime/backend/app/models.py runtime/backend/app/schemas.py runtime/backend/app/services/persistence.py tools/scripts/_pi_failure_categories.py tools/scripts/_pi_sse_client.py tools/scripts/pi_replay_regression.py tools/scripts/pi_review_tool.py
git diff --check
cd runtime/backend
DATABASE_URL=sqlite:////tmp/data-agent-alembic-p0-4.sqlite python3 -m alembic -c alembic.ini upgrade head
DATABASE_URL=sqlite:////tmp/data-agent-alembic-p0-4.sqlite python3 -m alembic -c alembic.ini downgrade 0004_trace_agent_provider
```

本地 smoke：

```bash
curl -sS http://127.0.0.1:8765/health
curl -sS http://127.0.0.1:8765/api/preflight
```

## test 环境收口进展（2026-07-15）

- 行为提交 `54df4d8f` 已完成 API / Worker / Freshness 三服务同提交部署、machine-auth smoke 与六项 preflight。
- durable SSE 传输稳定性已由最终 14 条 live case × N=3 关闭：39 PASS、3 个预期 WARN、0 fail、0 blocked、0 flaky；114 条 query records 全部成功。
- machine replay 已证明同一 job 的 `after_seq` 续传和最终结果可恢复；浏览器实际刷新后的 UI 恢复若没有独立手工报告，仍标 `evidence_gap`，不得从机器 N=3 推断。
- `/api/debug/snapshot` 的真实失败 session 诊断仍按独立验收证据管理，不与 transport 稳定性结论混写。

## 后续代码阶段验收命令

Replay / PI review：

```bash
python3 tools/scripts/pi_review_tool.py review-day --date YYYY-MM-DD --output eval/PI调用日志复核_YYYYMMDD/复核报告.md
python3 tools/scripts/pi_review_tool.py replay --question "..." --expect-route text2sql_or_sql_planning --min-query-records 1 --output eval/PI调用日志复核_YYYYMMDD/单题复跑.md
python3 tools/scripts/pi_replay_regression.py --cases eval/pi_replay_regression/cases.yaml --output-dir eval/PI调用日志复核_YYYYMMDD
```

后端行为：

```bash
pytest runtime/backend/tests
```

前端涉及 UI 时：

```bash
npm --prefix runtime/frontend run build
```

PI 配置涉及 PI runtime 时：

```bash
npm --prefix runtime/pi run check
```

test 环境验证：

```bash
curl -sS "$BASE_URL/health"
curl -sS "$BASE_URL/api/preflight"
python3 tools/scripts/pi_replay_regression.py --cases eval/pi_replay_regression/cases.yaml --base-url "$BASE_URL" --output-dir eval/PI调用日志复核_YYYYMMDD
python3 tools/scripts/pi_replay_regression.py --cases eval/pi_replay_regression/cases.yaml --base-url "$BASE_URL" --output-dir eval/PI调用日志复核_YYYYMMDD_第二轮
```

通过标准：

- `/health` 通过。
- `/api/preflight` 通过。
- 两轮 replay 连续通过。
- replay 报告能区分最终答案失败、中间 SQL 失败、freshness blocker、工具超时。
- `query_records` 字段满足工具名、SQL hash、状态、耗时、错误码的基础可观测要求。
- debug snapshot 能用一个 session_id 定位主要失败层。
- 长查询刷新页面后能凭 `job_id` / `session_id` 找回状态和结果。
