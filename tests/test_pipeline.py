# 🧪 test_pipeline.py — full pipeline end to end: 92 days fake GA4 data + fake FX API, DuckDB lo
import shutil

import pandas as pd
import pytest
from conftest import FakeHttp, fx_rows
from warehouse import DuckDBWarehouse

from ga4 import pipeline, report


@pytest.fixture
def readme(tmp_path):
    path = tmp_path / "README.md"
    shutil.copy(pipeline.ROOT / "README.md", path)
    return path


def test_full_run_builds_every_mart_and_fills_the_readme(full, readme, tmp_path):
    marts, dq = pipeline.run(DuckDBWarehouse(full), http=FakeHttp(fx_rows()), out_dir=tmp_path / "results", readme=readme)

    assert {len(marts[t]) for t in ("mart_daily_kpis", "mart_rolling_trends", "mart_revenue_inr")} == {92}
    assert not [r for r in dq if r["status"] == "FAIL"]

    inr = marts["mart_revenue_inr"]
    assert (inr.revenue_inr - (inr.revenue_usd * inr.usd_inr).round(2)).abs().max() < 1e-9
    assert inr.rate_carried_forward.iloc[0]                      # 1 Nov 2020 was a Sunday

    trends = marts["mart_rolling_trends"]
    assert trends.users_wow_pct.iloc[7:].eq(0).all()             # same 3 users every day

    for name in ["mart_daily_kpis", "mart_funnel", "mart_top_products", "data_quality"]:
        assert (tmp_path / "results" / f"{name}.csv").exists()

    text = readme.read_text(encoding="utf-8")
    section = text[text.index(report.START):text.index(report.END)]
    assert "| Users | 276 |" in section                           # 92 days x 3 users
    assert "| Purchases | 92 |" in section
    assert "Biggest drop-off" in section
    assert "raw: every day has data | 92 | PASS" in section


def test_rerun_replaces_the_results_section_instead_of_stacking(full, readme, tmp_path):
    for _ in range(2):
        pipeline.run(DuckDBWarehouse(full), http=FakeHttp(fx_rows()), out_dir=tmp_path / "results", readme=readme)
    text = readme.read_text(encoding="utf-8")
    assert text.count("| Session conversion rate |") == 1


def test_missing_day_stops_before_building_marts(full, readme, tmp_path):
    full.execute("DELETE FROM events WHERE event_date = '20201215'")
    with pytest.raises(SystemExit, match="every day has data"):
        pipeline.run(DuckDBWarehouse(full), http=FakeHttp(fx_rows()), out_dir=tmp_path / "results", readme=readme)
    assert not (tmp_path / "results").exists()


def test_csv_output_is_readable(full, readme, tmp_path):
    pipeline.run(DuckDBWarehouse(full), http=FakeHttp(fx_rows()), out_dir=tmp_path / "results", readme=readme)
    funnel = pd.read_csv(tmp_path / "results" / "mart_funnel.csv")
    assert funnel.users.tolist() == [276, 184, 92, 92]
