# 🚀 pipeline.py — okka command tho full run: FX API → BigQuery → data quality → marts → results/ + README
import argparse
from pathlib import Path

import pandas as pd
import requests

from . import checks, fx, report
from .config import END, MARTS, PROFILE_SQL, START

ROOT = Path(__file__).resolve().parent.parent


def run(warehouse, http=requests, out_dir=ROOT / "results", readme=ROOT / "README.md"):
    warehouse.ensure_dataset()

    print("💱 USD→INR rates from Frankfurter (ECB) ...")
    rates = fx.to_daily(fx.fetch(START, END, http=http), START, END)
    dq = checks.check_fx(rates, START, END)
    checks.stop_on_fail(dq, "FX rates")
    warehouse.load_frame(rates, "fx_usd_inr")

    print("🔎 Profiling raw GA4 events ...")
    profile_df, scanned = warehouse.query(PROFILE_SQL)
    profile = {k: int(v) for k, v in profile_df.iloc[0].items()}  # anni counts — float/NA types vaddu
    source_dq = checks.check_source(profile)
    checks.stop_on_fail(source_dq, "raw GA4 events")
    dq += source_dq

    marts = {}
    for sql_file, table in MARTS:
        marts[table], used = warehouse.query(sql_file, table)
        scanned += used
        print(f"🏗️  {table}: {len(marts[table])} rows")
    dq += checks.check_marts(marts)

    out_dir.mkdir(exist_ok=True)
    for table, df in marts.items():
        df.to_csv(out_dir / f"{table}.csv", index=False)
    pd.DataFrame(dq).to_csv(out_dir / "data_quality.csv", index=False)
    report.update_readme(readme, report.build(profile, marts, dq, scanned))

    warns = sum(r["status"] == checks.WARN for r in dq)
    print(f"✅ Done: {scanned / 1e9:.2f} GB scanned, {warns} warning(s). Results in results/ and README.md")
    return marts, dq


def main():
    ap = argparse.ArgumentParser(description="Build GA4 analytics marts in BigQuery")
    ap.add_argument("--project", required=True, help="your Google Cloud project id")
    args = ap.parse_args()

    from .bq import BigQueryWarehouse
    run(BigQueryWarehouse(args.project))


if __name__ == "__main__":
    main()
