#!/usr/bin/env python3
"""校验 knowledge 语义契约各 yaml 并编译成 model.json。

校验内容:
  1. entities.appears_in / metrics.source_table / dimensions.source_tables /
     joins.left|right 引用的表必须在 ai_ck / ai_hive 表卡中存在。
  2. metrics.base_columns 必须在其来源表(含 variants 各表)的 columns 中存在。
  3. metrics.requires_join 必须在 joins.yaml 中定义。
  4. cross_table metric 的 numerator/denominator 引用的 metric 必须存在。
  5. joins.on / keys_compat 的列必须在左右表中存在。

无第三方依赖,仅需 PyYAML。退出码非 0 表示有校验错误。
"""
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
KNOWLEDGE_ROOT = HERE.parents[1]
REPO_ROOT = KNOWLEDGE_ROOT.parent
AGENT_KNOWLEDGE = KNOWLEDGE_ROOT / "agent_knowledge" / "semantic_contract"
AI_CK_TABLES = REPO_ROOT / "ai_ck" / "agent_knowledge" / "tables"
AI_HIVE_TABLES = REPO_ROOT / "ai_hive" / "agent_knowledge" / "tables"

# MaxCompute 表按白名单纳入(语义模型只引用到的 MC 表,避免 model.json 臃肿)。
MC_INCLUDE = {
    "ads_market_roi_pred_accuracy_da.yaml",
    "ads_market_material_metric_di.yaml",
    "ads_market_device_dau_behavior_di.yaml",
}


def load_yaml(name):
    with open(AGENT_KNOWLEDGE / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _read_dir(dirpath, datasource, include=None):
    tables = {}
    for path in sorted(dirpath.glob("*.yaml")):
        if include is not None and path.name not in include:
            continue
        with open(path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        if not doc or "table" not in doc:
            continue
        fqn = doc["table"].get("fqn")
        if not fqn:
            continue
        cols = {c["name"] for c in (doc.get("columns") or []) if isinstance(c, dict) and c.get("name")}
        rules = doc.get("query_rules") or {}
        tables[fqn] = {
            "columns": cols,
            "must_filter": rules.get("must_filter") or [],
            "max_scan": rules.get("max_scan_without_approval"),
            "datasource": datasource,
        }
    return tables


def load_tables():
    """多源索引: ai_ck 全部(clickhouse) + ai_hive 白名单(maxcompute)。"""
    tables = _read_dir(AI_CK_TABLES, "clickhouse")
    tables.update(_read_dir(AI_HIVE_TABLES, "maxcompute", include=MC_INCLUDE))
    return tables


def variant_tables(metric):
    """返回 metric 的所有来源表(单表或 variants 的各口径表)。"""
    tables = []
    if metric.get("source_table"):
        tables.append(metric["source_table"])
    variants = metric.get("variants") or {}
    for vdef in variants.values():
        st = vdef.get("source_table") if isinstance(vdef, dict) else None
        if isinstance(st, dict):
            tables.extend(st.values())
    return tables


def main():
    errors, warnings = [], []

    tables = load_tables()
    table_cols = {fqn: meta["columns"] for fqn, meta in tables.items()}
    table_ds = {fqn: meta["datasource"] for fqn, meta in tables.items()}
    known_tables = set(tables)

    entities = load_yaml("entities.yaml")["entities"]
    dimensions = load_yaml("dimensions.yaml")["dimensions"]
    metrics = load_yaml("metrics.yaml")["metrics"]
    joins = load_yaml("joins.yaml")["joins"]
    governance = load_yaml("governance.yaml")
    diagnostics = load_yaml("diagnostics.yaml").get("diagnostics", [])

    metric_names = {m["name"] for m in metrics}
    join_names = {j["name"] for j in joins}

    def check_table(tbl, ctx):
        if tbl not in known_tables:
            errors.append(f"[{ctx}] 表不在 ai_ck / ai_hive 知识层表卡中: {tbl}")
            return False
        return True

    def check_cols(tbl, cols, ctx):
        if tbl not in known_tables:
            return
        avail = table_cols[tbl]
        missing = []
        for c in cols:
            # 容忍 N 占位列(如 pred_dN / real_dN),用 N=7 校验存在性
            if c in avail or ("N" in c and c.replace("N", "7") in avail):
                continue
            missing.append(c)
        if missing:
            errors.append(f"[{ctx}] 表 {tbl} 缺列: {missing}")

    # entities
    for e in entities:
        for t in e.get("appears_in", []):
            check_table(t, f"entity:{e['name']}")

    # dimensions
    for d in dimensions:
        for t in d.get("source_tables", []):
            if check_table(t, f"dimension:{d['name']}"):
                check_cols(t, [d["column"]], f"dimension:{d['name']}")

    # metrics
    for m in metrics:
        ctx = f"metric:{m['name']}"
        mtype = m.get("type")
        srcs = variant_tables(m)
        for t in srcs:
            check_table(t, ctx)
        base = m.get("base_columns") or []
        for t in srcs:
            check_cols(t, base, ctx)
        if m.get("requires_join") and m["requires_join"] not in join_names:
            errors.append(f"[{ctx}] requires_join 未定义: {m['requires_join']}")
        if mtype == "cross_table":
            f = m.get("formula") or {}
            for side in ("numerator", "denominator"):
                ref = (f.get(side) or {}).get("metric")
                if ref and ref not in metric_names:
                    errors.append(f"[{ctx}] {side} 引用未知 metric: {ref}")
        if mtype not in ("cross_table", "derived") and not srcs:
            warnings.append(f"[{ctx}] 无 source_table/variants,无法校验列")

    # joins
    for j in joins:
        ctx = f"join:{j['name']}"
        left = j["left"]
        right = j["right"]
        right_tables = list(right.values()) if isinstance(right, dict) else [right]
        for t in [left] + right_tables:
            check_table(t, ctx)
        # 跨源 join 禁止: 左右表必须同 datasource
        ds_set = {table_ds.get(t) for t in [left] + right_tables if t in known_tables}
        if len(ds_set) > 1:
            errors.append(f"[{ctx}] 跨源 join 不允许: 涉及 datasource {ds_set}")
        on_cols = j.get("on_keys", [])
        if not on_cols:
            errors.append(f"[{ctx}] 缺 on_keys")
        compat = j.get("keys_compat") or {}
        compat_cols = [c for c in compat.values() if c]
        for t in [left] + right_tables:
            check_cols(t, on_cols, f"{ctx}:on")
            check_cols(t, compat_cols, f"{ctx}:keys_compat")

    # diagnostics 引用校验: check_metrics / check_joins 必须存在
    for d in diagnostics:
        dctx = f"diagnostic:{d.get('symptom')}"
        for mref in d.get("check_metrics", []):
            if mref not in metric_names:
                errors.append(f"[{dctx}] check_metrics 未知 metric: {mref}")
        for jref in d.get("check_joins", []):
            if jref not in join_names:
                errors.append(f"[{dctx}] check_joins 未知 join: {jref}")

    model = {
        "version": "0.1",
        "compiled_from": [
            "knowledge/agent_knowledge/semantic_contract/entities.yaml",
            "knowledge/agent_knowledge/semantic_contract/dimensions.yaml",
            "knowledge/agent_knowledge/semantic_contract/metrics.yaml",
            "knowledge/agent_knowledge/semantic_contract/joins.yaml",
        ],
        "source_tables": {
            t: {"datasource": m["datasource"], "columns": sorted(m["columns"]),
                "must_filter": m["must_filter"], "max_scan": m["max_scan"]}
            for t, m in tables.items()
        },
        "entities": entities,
        "dimensions": dimensions,
        "metrics": metrics,
        "joins": joins,
        "governance": governance,
        "diagnostics": diagnostics,
        "validation": {
            "tables_indexed": len(known_tables),
            "metrics": len(metrics),
            "dimensions": len(dimensions),
            "entities": len(entities),
            "joins": len(joins),
            "diagnostics": len(diagnostics),
            "errors": errors,
            "warnings": warnings,
        },
    }

    out = AGENT_KNOWLEDGE / "model.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)

    print(f"indexed tables: {len(known_tables)}")
    print(f"entities={len(entities)} dimensions={len(dimensions)} metrics={len(metrics)} joins={len(joins)} diagnostics={len(diagnostics)}")
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"-> wrote {out}")
    if errors:
        print(f"FAILED: {len(errors)} error(s)")
        return 1
    print("OK: validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
