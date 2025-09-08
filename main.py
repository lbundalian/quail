#!/usr/bin/env python3
# Quailtrail — prototype runner + pipeline (helpers now come from quail.core)

import os, sys, argparse, textwrap
import pandas as pd
from sqlalchemy import text, select, cast, Date, MetaData, Table
# create_engine / sessionmaker are not needed here anymore (handled in core helpers)

from quail.core import (
    qtask, qcheck, CheckResult, Runner,
    load_quail_config, build_env_from_orm, resolve_targets,
)

# ---------------------------
# Pipeline helpers
# ---------------------------

def _table_key(ctx):
    schema = ctx.env.get("schema")
    return f"{schema}.pricing_report" if schema else "pricing_report"


# ---------------------------
# Tasks
# ---------------------------

@qtask(id="reflect_tables")
def reflect_tables(ctx):
    """Reflect <schema>.pricing_report (table must already exist)."""
    engine = ctx.env["engine"]
    schema = ctx.env.get("schema")
    md = MetaData(schema=schema)
    t = Table("pricing_report", md, schema=schema, autoload_with=engine)
    key = _table_key(ctx)
    ctx.env.setdefault("tables", {})[key] = t
    # Returned dict will be merged into ctx by core.py
    return {"reflected": list(ctx.env["tables"].keys())}

@qtask(id="test_connection", requires=["reflect_tables"])
def test_connection(ctx):
    """
    Verify DB connectivity and presence of the reflected table.
    Returns a dict that includes 'connection_ok' so checks can ctx.get("connection_ok")
    without any manual ctx.put(...).
    """
    Session = ctx.env.get("session_factory")
    engine = ctx.env.get("engine")
    key = _table_key(ctx)

    if key not in ctx.env.get("tables", {}):
        return {"connection_ok": False, "error": f"Table not reflected: {key}"}

    with engine.connect() as conn:
        one = conn.execute(text("SELECT 1")).scalar()

    with Session() as s:
        row = s.execute(ctx.env["tables"][key].select().limit(1)).first()

    ok = (one == 1)
    return {
        "connection_ok": ok,
        "sample": (dict(row._mapping) if row else None)
    }

@qtask(id="load_pricing_report", requires=["test_connection"])
def load_pricing_report(ctx):
    """Return a pandas DataFrame for downstream tasks + checks."""
    if not ctx.get("connection_ok", False):
        return pd.DataFrame()

    Session = ctx.env["session_factory"]
    t = ctx.env["tables"][_table_key(ctx)]
    cols = [t.c.client_id, t.c.listing_id, t.c.email, t.c.calendar_date, t.c.report_date, t.c.optimized_price]
    stmt = select(*cols)

    # Normalize report_date to a Python date for a clean Date = Date comparison
    rd = ctx.params.get("report_date")
    if rd:
        if isinstance(rd, str):
            rd = pd.to_datetime(rd).date()
        elif hasattr(rd, "date"):  # datetime-like
            rd = rd.date()
        stmt = stmt.where(cast(t.c.report_date, Date) == rd)

    with Session() as s:
        rows = [dict(r._mapping) for r in s.execute(stmt)]
    df = pd.DataFrame(rows)

    # Align types to make client_id == listing_id comparisons meaningful
    if not df.empty:
        if "client_id" in df:   df["client_id"] = df["client_id"].astype(str)
        if "listing_id" in df:  df["listing_id"] = df["listing_id"].astype(str)

    return df

@qtask(id="summarize", requires=["load_pricing_report"])
def summarize(ctx):
    df = ctx.get("load_pricing_report")
    if df is None or df.empty:
        return pd.DataFrame()

    # Partitions
    lhs = df[df.client_id == df.listing_id]
    rhs = df[df.client_id != df.listing_id]

    tmp1 = (lhs
            .groupby("client_id", dropna=False)
            .agg(email=("email","first"),
                 unique_calendar_dates=("calendar_date","nunique"),
                 max_optimized_price=("optimized_price","max"),
                 min_optimized_price=("optimized_price","min"))
            .reset_index())

    tmp2 = (rhs
            .groupby("client_id", dropna=False)
            .agg(unique_listing_count=("listing_id","nunique"))
            .reset_index())

    out = tmp1.merge(tmp2, on="client_id", how="left").fillna({"unique_listing_count": 0})

    min_listings = int(ctx.params.get("min_listing_count", 2))

    def status_row(r):
        if r.get("max_optimized_price", 0) == 0:  return "Fail (Max Price Zero)"
        if r.get("min_optimized_price", 0) == 0:  return "Fail (Min Price Zero)"
        if int(r.get("unique_listing_count", 0)) < min_listings: return f"Fail (Listing Count < {min_listings})"
        return "Pass"

    out["status"] = out.apply(status_row, axis=1)
    return out


# ---------------------------
# Checks
# ---------------------------

@qcheck(id="qc_connection_ok", requires=["test_connection"], severity="error")
def qc_connection_ok(ctx):
    ok = bool(ctx.get("connection_ok"))
    return CheckResult(
        id="qc_connection_ok",
        status="pass" if ok else "fail",
        metrics={"ok": ok},
        description="Connectivity to pricing_report",
    )

@qcheck(id="qc_reports_nonempty", requires=["load_pricing_report"], severity="error")
def qc_reports_nonempty(ctx):
    df = ctx.get("load_pricing_report")
    rowcount = int(len(df)) if df is not None else 0
    return CheckResult(
        id="qc_reports_nonempty",
        status="pass" if df is not None and rowcount > 0 else "fail",
        metrics={"rowcount": rowcount},
        description="pricing_report has rows for the given report_date"
    )

@qcheck(id="qc_summary_clean", requires=["summarize"], severity="error")
def qc_summary_clean(ctx):
    df = ctx.get("summarize")
    if df is None or df.empty:
        return CheckResult(id="qc_summary_clean", status="fail",
                           metrics={"status_counts": {}}, description="Summary is empty")
    counts = df["status"].value_counts().to_dict()
    bad = sum(v for k, v in counts.items() if str(k).startswith("Fail"))
    return CheckResult(
        id="qc_summary_clean",
        status="pass" if bad == 0 else "fail",
        metrics={"status_counts": counts},
        description="No failing statuses in summary"
    )


# ---------------------------
# Prototype runner (reads quail.yml)
# ---------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Prototype Quailtrail runner (reads quail.yml, builds ORM env, runs targets)"
    )
    ap.add_argument("--config", default="quail.yml", help="Path to quail.yml")
    ap.add_argument("--targets", nargs="*", help="Target group(s) or node ids to run")
    args = ap.parse_args()

    cfg, env_cfg, params, cfg_targets, default_covey, profile = load_quail_config(args.config)

    # Prefer native ORM section in YAML
    orm_cfg = (env_cfg or {}).get("orm")
    if not orm_cfg:
        raise SystemExit(textwrap.dedent("""
            No envs.<profile>.orm block found in quail.yml.
            Example:
              envs:
                dev:
                  orm:
                    kind: sql
                    url: ${DB_URL}
                    schema: raw_data
                    reflect: ["pricing_report"]
        """).strip())

    # Build env via ORM config
    env = build_env_from_orm(orm_cfg)

    # Merge/expand params already done in loader; allow REPORT_DATE overrides
    if os.getenv("REPORT_DATE"):
        params["report_date"] = os.environ["REPORT_DATE"]

    # Resolve targets (CLI overrides YAML)
    targets = resolve_targets(cfg_targets, default_covey, args.targets)

    # Run
    runner = Runner(env=env, params=params)
    results = runner.run(targets)

    # Pretty print
    try:
        from quail.reporting.markdown_reporter import print_markdown
        print_markdown(results)
    except Exception:
        for n, (kind, val) in results.items():
            print(f"[{kind}] {n}: {val}")

if __name__ == "__main__":
    main()
