# 🧪 test_fx_and_checks.py — FX weekend fill + data quality rules (internet avasaram ledu)
from datetime import date

import numpy as np
import pandas as pd
import pytest
from conftest import FakeHttp, fx_rows

from ga4 import checks, fx

START, END = date(2020, 11, 1), date(2020, 11, 8)


def test_fetch_asks_for_usd_inr_from_ecb_with_lookback():
    http = FakeHttp([])
    fx.fetch(START, END, http=http)
    url, params = http.calls[0]
    assert url == fx.API
    assert params == {"from": "2020-10-25", "to": "2020-11-08", "base": "USD", "quotes": "INR", "providers": "ECB"}


def test_weekend_and_first_day_get_the_last_known_rate():
    rows = fx_rows(date(2020, 10, 25), END) + [{"date": "2020-11-02", "base": "USD", "quote": "USD", "rate": 1.0}]
    daily = fx.to_daily(rows, START, END).set_index("day")
    assert len(daily) == 8
    friday = next(r["rate"] for r in rows if r["date"] == "2020-10-30")
    assert daily.loc[date(2020, 11, 1), "usd_inr"] == friday    # 1 Nov is a Sunday
    assert daily.loc[date(2020, 11, 1), "is_filled"]
    assert not daily.loc[date(2020, 11, 2), "is_filled"]          # identity USD/USD row ignored
    assert daily.loc[date(2020, 11, 8), "usd_inr"] == daily.loc[date(2020, 11, 6), "usd_inr"]


def test_duplicate_dates_keep_the_last_value():
    rows = [{"date": "2020-11-02", "base": "USD", "quote": "INR", "rate": 73.0},
            {"date": "2020-11-02", "base": "USD", "quote": "INR", "rate": 73.5}]
    daily = fx.to_daily(rows, date(2020, 11, 2), date(2020, 11, 2))
    assert daily.usd_inr.tolist() == [73.5]


def test_no_inr_rows_is_an_error():
    with pytest.raises(ValueError):
        fx.to_daily([{"date": "2020-11-02", "base": "USD", "quote": "EUR", "rate": 0.85}], START, END)


def _status(rows):
    return {r["check"]: r["status"] for r in rows}


def test_good_fx_passes_every_check():
    daily = fx.to_daily(fx_rows(date(2020, 10, 25), END), START, END)
    assert set(_status(checks.check_fx(daily, START, END)).values()) == {"PASS"}


def test_fx_with_a_gap_or_a_jump_is_caught():
    daily = fx.to_daily(fx_rows(date(2020, 10, 25), END), START, END)
    gap = daily.assign(usd_inr=daily.usd_inr.where(daily.index != 3, np.nan))
    assert _status(checks.check_fx(gap, START, END))["fx: no missing rates"] == "FAIL"
    jump = daily.assign(usd_inr=daily.usd_inr.where(daily.index != 5, 80.0))
    assert _status(checks.check_fx(jump, START, END))["fx: no sudden day-to-day jump"] == "WARN"


def test_source_rules_on_the_tiny_profile():
    profile = {"total_events": 17, "days_with_data": 3, "days_expected": 92, "events_missing_user": 0,
               "events_missing_session": 1, "duplicate_events": 1, "purchase_events": 3,
               "purchases_without_revenue": 1, "purchases_without_transaction_id": 1}
    s = _status(checks.check_source(profile))
    assert s["raw: every day has data"] == "FAIL"
    assert s["raw: no events without a user"] == "PASS"
    assert s["raw: duplicate events"] == "WARN"
    assert s["raw: purchases without revenue"] == "WARN"


def test_stop_on_fail_only_stops_for_fail():
    checks.stop_on_fail([{"check": "x", "value": 1, "status": "WARN", "detail": ""}], "stage")
    with pytest.raises(SystemExit, match="stage"):
        checks.stop_on_fail([{"check": "x", "value": 1, "status": "FAIL", "detail": "why"}], "stage")


def test_mart_checks_flag_a_growing_funnel_and_missing_inr():
    marts = {
        "mart_funnel": pd.DataFrame({"step_order": [1, 2], "users": [5, 7]}),
        "mart_revenue_inr": pd.DataFrame({"revenue_inr": [1.0, None]}),
        "mart_daily_kpis": pd.DataFrame({"day": [1, 2]}),
    }
    s = _status(checks.check_marts(marts))
    assert s["mart: funnel never grows step to step"] == "WARN"
    assert s["mart: INR revenue present every day"] == "FAIL"
