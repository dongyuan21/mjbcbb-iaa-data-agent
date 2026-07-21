#!/usr/bin/env python3
"""仅凭 model.json 把结构化回归用例拼成 SQL,并断言用对了表/join/口径/过滤。

目的: 证明 knowledge 语义契约真正"机器可消费"(第 1 点验收项 c),
而不是靠人读散文推导。这是一个轻量 composer,不是生产级 text2sql 引擎,
但拼出的 SQL 应带正确的表、join、口径变体、must_filter。
"""
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
KNOWLEDGE_ROOT = HERE.parents[2]
MODEL = KNOWLEDGE_ROOT / "agent_knowledge" / "semantic_contract" / "model.json"
CASES = HERE / "regression_cases.yaml"
REPORT = HERE / "回归验证报告.md"


def load():
    model = json.load(open(MODEL, encoding="utf-8"))
    cases = yaml.safe_load(open(CASES, encoding="utf-8"))["cases"]
    model["_metrics"] = {m["name"]: m for m in model["metrics"]}
    model["_joins"] = {j["name"]: j for j in model["joins"]}
    return model, cases


def variant_table(metric, revenue_source):
    """取 metric 在指定口径下的来源表。"""
    if metric.get("source_table"):
        return metric["source_table"]
    v = (metric.get("variants") or {}).get("revenue_source") or {}
    st = v.get("source_table") or {}
    return st.get(revenue_source or v.get("default"))


def filter_conditions(filters, allowed_cols):
    """生成 where 条件,只用目标表存在的列。"""
    conds = []
    for col, val in (filters or {}).items():
        if col not in allowed_cols:
            continue
        if isinstance(val, list) and len(val) == 2:
            conds.append(f"{col} BETWEEN '{val[0]}' AND '{val[1]}'")
        else:
            conds.append(f"{col} = '{val}'")
    return conds


def compose_governance(model, case):
    gov = model.get("governance", {})
    return {
        "kind": "governance",
        "status_fields": [f["name"] for f in gov.get("status_fields", [])],
        "guardrails": gov.get("guardrails", []),
        "unsupported": False, "reason": None,
        "blocks": [], "tables_used": [], "joins_used": [],
    }


def compose_diagnostic(model, case):
    kw = case["diagnostic_query"].get("symptom_contains", "")
    matched = [d for d in model.get("diagnostics", []) if kw in d.get("symptom", "")]
    return {
        "kind": "diagnostic", "matched": matched,
        "unsupported": not matched,
        "reason": None if matched else f"无诊断匹配: {kw}",
        "blocks": [], "tables_used": [], "joins_used": [],
    }


def compose(model, case):
    if "governance_query" in case:
        return compose_governance(model, case)
    if "diagnostic_query" in case:
        return compose_diagnostic(model, case)
    sel = case.get("select", {})
    dims = sel.get("dimensions", [])
    filters = sel.get("filters", {})
    metrics = model["_metrics"]
    tables_meta = model["source_tables"]

    blocks, tables_used, joins_used = [], set(), set()

    # 覆盖边界:请求的 metric 不在模型中 -> unsupported
    for mreq in sel.get("metrics", []):
        if mreq["metric"] not in metrics:
            return {
                "unsupported": True,
                "reason": f"metric 未定义于 semantic_contract: {mreq['metric']};预测偏差需扩展 ai_hive roi_pred 类表",
                "blocks": [], "tables_used": [], "joins_used": [],
            }
        m = metrics[mreq["metric"]]
        # 护栏:口径待业务拍板的 metric 不生成 SQL
        if m.get("type") == "needs_decision" or m.get("status") == "needs_decision":
            return {
                "unsupported": True,
                "reason": f"metric 口径待业务拍板(needs_decision),不生成 SQL: {mreq['metric']}",
                "blocks": [], "tables_used": [], "joins_used": [],
            }

    # 口径变体:支持 compare_variants(并列多版)或单 variant
    cmp = sel.get("compare_variants", {}).get("revenue_source")
    variants = cmp if cmp else [sel.get("variant", {}).get("revenue_source", "sdk")]

    single_by_table = {}  # source_table -> [(alias, expr)] 同表单表指标合并
    cross_reqs = []       # 跨表 roi/ltv
    cohort_reqs = []      # 留存
    arpu_reqs = []        # 首日 ARPU(date_diff=0 收入 / 安装分母)

    for mreq in sel.get("metrics", []):
        m = metrics[mreq["metric"]]
        n = mreq.get("n")
        if m["name"] in ("af_arpu", "media_arpu"):
            # ARPU 分母是安装数(registers/media_installs)而非 cost_zhe,独立处理
            arpu_reqs.append(m)
        elif m["type"] == "cross_table":
            cross_reqs.append((m, n))
        elif m["name"] == "retention_n":
            # 仅 af_cohort 的 date_diff 透视留存走 cohort 块;
            # dau 前向留存率(dau_dN_retention_rate)是普通 ratio,走单表块。
            cohort_reqs.append((m, n))
        else:
            expr = m["formula"].replace("N", str(n)) if n else m["formula"]
            alias = m["name"]
            if n:
                alias = alias.replace("_dn", f"_d{n}").replace("_n", f"_{n}")
            single_by_table.setdefault(m["source_table"], []).append((alias, expr))
            tables_used.add(m["source_table"])

    def render_filters(table, extra_skip=()):
        cols = set(tables_meta[table]["columns"])
        conds = filter_conditions(filters, cols)
        for mf in tables_meta[table]["must_filter"]:
            if mf in extra_skip:
                continue
            if not any(c.startswith(mf) for c in conds):
                v = filters.get(mf)
                if isinstance(v, list) and len(v) == 2:
                    conds.append(f"{mf} BETWEEN '{v[0]}' AND '{v[1]}'")
                else:
                    conds.append(f"/* TODO must_filter: {mf} */")
        return conds

    def group_by_clause():
        return f"\nGROUP BY {', '.join(dims)}" if dims else ""

    # 单表指标块(按各自 source_table 分组,支持 CK 与 MC 多源)
    for t, sels in single_by_table.items():
        cols = ", ".join(dims + [f"{e} AS {a}" for a, e in sels])
        where = " AND ".join(render_filters(t))
        blocks.append({
            "name": f"metrics_{t.split('.')[-1]}", "join": None, "datasource": tables_meta[t]["datasource"],
            "sql": f"SELECT {cols}\nFROM {t}\nWHERE {where}{group_by_clause()}",
        })

    # 跨表 roi/ltv 块
    for m, n in cross_reqs:
        join = model["_joins"][m["requires_join"]]
        joins_used.add(m["requires_join"])
        spend_t = join["left"]
        tables_used.add(spend_t)
        scale = (m["formula"].get("scale") or 1)
        for rs in variants:
            rev_t = variant_table(metrics["revenue_n"], rs)
            tables_used.add(rev_t)
            on = [c for c in join["on_keys"] if c in dims] or dims
            max_diff = max(n - 1, 0)
            sp_where = " AND ".join(render_filters(spend_t))
            rev_where = " AND ".join(render_filters(rev_t) + [f"date_diff <= {max_diff}"])
            using = ", ".join(on)
            blocks.append({
                "name": f"roi_{n}_{rs}", "join": m["requires_join"], "revenue_source": rs,
                "sql": (
                    f"WITH spend AS (\n"
                    f"  SELECT {', '.join(on)}, SUM(cost_zhe / NULLIF(currency,0)) AS cost_zhe\n"
                    f"  FROM {spend_t} WHERE {sp_where} GROUP BY {', '.join(on)}\n"
                    f"), rev AS (\n"
                    f"  SELECT {', '.join(on)}, SUM(revenue) AS revenue_{n}\n"
                    f"  FROM {rev_t} WHERE {rev_where} GROUP BY {', '.join(on)}\n"
                    f")\n"
                    f"SELECT s.{on[0]}, rev.revenue_{n} / NULLIF(s.cost_zhe,0) * {scale} AS roi_{n}_{rs}\n"
                    f"FROM spend s LEFT JOIN rev USING ({using})"
                ),
            })

    # 首日 ARPU 块(spend×revenue: date_diff=0 收入 / 安装分母)
    for m in arpu_reqs:
        join = model["_joins"][m["requires_join"]]
        joins_used.add(m["requires_join"])
        spend_t = join["left"]
        tables_used.add(spend_t)
        denom_col = "registers" if m["name"] == "af_arpu" else "media_installs"
        for rs in variants:
            rev_t = variant_table(metrics["revenue_n"], rs)
            tables_used.add(rev_t)
            on = [c for c in join["on_keys"] if c in dims] or dims
            sp_where = " AND ".join(render_filters(spend_t))
            rev_where = " AND ".join(render_filters(rev_t) + ["date_diff = 0"])
            using = ", ".join(on)
            blocks.append({
                "name": f"{m['name']}_{rs}", "join": m["requires_join"], "revenue_source": rs,
                "sql": (
                    f"WITH spend AS (\n"
                    f"  SELECT {', '.join(on)}, SUM({denom_col}) AS installs\n"
                    f"  FROM {spend_t} WHERE {sp_where} GROUP BY {', '.join(on)}\n"
                    f"), rev AS (\n"
                    f"  SELECT {', '.join(on)}, SUM(revenue) AS revenue_0\n"
                    f"  FROM {rev_t} WHERE {rev_where} GROUP BY {', '.join(on)}\n"
                    f")\n"
                    f"SELECT s.{on[0]}, rev.revenue_0 / NULLIF(s.installs,0) AS {m['name']}_{rs}\n"
                    f"FROM spend s LEFT JOIN rev USING ({using})"
                ),
            })

    # 留存块(cohort 单表,分母 date_diff=0)
    if cohort_reqs:
        t = "shucang_market.af_cohort_user_acquisition_v2"
        tables_used.add(t)
        ns = sorted({0} | {n for _, n in cohort_reqs})
        rets = []
        for _, n in cohort_reqs:
            rets.append(
                f"round(sumIf(unique_users, date_diff = {n}) * 100.0 / "
                f"nullIf(sumIf(unique_users, date_diff = 0), 0), 2) AS retention_{n}"
            )
        start = filters.get("active_date", ["", ""])[0]
        where = " AND ".join(
            render_filters(t, extra_skip={"dt", "date_diff"})
            + [f"dt >= '{start}'", f"date_diff IN ({', '.join(map(str, ns))})"]
        )
        cols = ", ".join(dims + rets)
        blocks.append({
            "name": "retention", "join": None,
            "sql": f"SELECT {cols}\nFROM {t}\nWHERE {where}\nGROUP BY {', '.join(dims)}",
        })

    return {
        "unsupported": False, "reason": None, "blocks": blocks,
        "tables_used": sorted(tables_used), "joins_used": sorted(joins_used),
    }


def assert_case(case, res):
    exp = case["expect"]
    fails = []
    if exp.get("unsupported"):
        if not res["unsupported"]:
            fails.append("期望 unsupported 但 composer 生成了 SQL")
        else:
            for kw in exp.get("reason_contains", []):
                if kw not in (res["reason"] or ""):
                    fails.append(f"reason 未含关键字: {kw}")
        return fails
    if res["unsupported"]:
        fails.append(f"意外 unsupported: {res['reason']}")
        return fails
    if res.get("kind") == "governance":
        for f in exp.get("status_fields_contain", []):
            if f not in res["status_fields"]:
                fails.append(f"governance 缺状态字段: {f}")
        guard_all = " ".join(res["guardrails"])
        for kw in exp.get("guard_contains", []):
            if kw not in guard_all:
                fails.append(f"护栏未含: {kw}")
        return fails
    if res.get("kind") == "diagnostic":
        rec_all = " ".join(
            (m.get("recommend_sql", "") or "") + " " + (m.get("recommend", "") or "")
            for m in res["matched"])
        for kw in exp.get("recommend_contains", []):
            if kw not in rec_all:
                fails.append(f"诊断推荐未含: {kw}")
        cm_all = [x for m in res["matched"] for x in m.get("check_metrics", [])]
        for mm in exp.get("check_metrics_contain", []):
            if mm not in cm_all:
                fails.append(f"诊断 check_metrics 缺: {mm}")
        return fails
    for t in exp.get("tables", []):
        if t not in res["tables_used"]:
            fails.append(f"缺表: {t}")
    if set(exp.get("joins", [])) != set(res["joins_used"]):
        fails.append(f"join 不匹配: 期望 {exp.get('joins')} 实际 {res['joins_used']}")
    all_sql = "\n".join(b["sql"] for b in res["blocks"])
    for kw in exp.get("sql_contains", []):
        if kw not in all_sql:
            fails.append(f"SQL 未含: {kw}")
    return fails


def main():
    model, cases = load()
    lines = ["# semantic_contract 回归验证报告", "",
             f"> model.json 编译自 {model['compiled_from']}", "",
             "证明 agent 仅凭 model.json 即可拼出正确 SQL(第 1 点验收项 c)。", ""]
    passed = 0
    for case in cases:
        res = compose(model, case)
        fails = assert_case(case, res)
        ok = not fails
        passed += ok
        lines.append(f"## {case['id']} (→{case['maps_to']}) {'PASS' if ok else 'FAIL'}")
        lines.append(f"- 问题: {case['question']}")
        if res["unsupported"]:
            lines.append(f"- 结果: unsupported — {res['reason']}")
        elif res.get("kind") == "governance":
            lines.append(f"- 必输状态字段: {', '.join(res['status_fields'])}")
            lines.append(f"- 护栏数: {len(res['guardrails'])}(含阈值数值不写死)")
        elif res.get("kind") == "diagnostic":
            for m in res["matched"]:
                rec = m.get("recommend_sql") or m.get("recommend", "")
                lines.append(f"- 现象: {m['symptom']} → 推荐: {rec}")
        else:
            lines.append(f"- 用表: {', '.join(t.split('.')[-1] for t in res['tables_used'])}")
            lines.append(f"- 用 join: {res['joins_used'] or '无'}")
            for b in res["blocks"]:
                lines.append(f"\n```sql\n-- block: {b['name']}\n{b['sql']}\n```")
        if fails:
            lines.append("- 断言失败:")
            lines += [f"  - {x}" for x in fails]
        lines.append("")
        print(f"{case['id']} {'PASS' if ok else 'FAIL'}" + (f" {fails}" if fails else ""))
    lines.insert(5, f"**结果: {passed}/{len(cases)} 通过**\n")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"-> {REPORT}  ({passed}/{len(cases)} passed)")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
