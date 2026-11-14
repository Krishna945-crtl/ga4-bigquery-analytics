# 🧪 test_sql.py — sql/ files ni DuckDB lo hand-made GA4 data meeda run chesi, chethi tho lekkapettina answers tho match
import re
from datetime import date

import pandas as pd
import pytest
import sqlglot
from warehouse import DuckDBWarehouse

from ga4.bq import SQL_DIR
from ga4.config import END, SOURCE, START


def run(con, sql_file, table=None):
    return DuckDBWarehouse(con).query(sql_file, table)[0]


@pytest.mark.parametrize("path", sorted(SQL_DIR.glob("*.sql")), ids=lambda p: p.name)
def test_every_file_is_valid_bigquery_sql(path):
    sqlglot.parse_one(path.read_text(), read="bigquery")


@pytest.mark.parametrize("path", sorted(SQL_DIR.glob("*.sql")), ids=lambda p: p.name)
def test_sql_uses_the_configured_date_range(path):
    sql = path.read_text()
    if SOURCE not in sql:
        return
    expected = f"_TABLE_SUFFIX BETWEEN '{START:%Y%m%d}' AND '{END:%Y%m%d}'"
    assert expected in sql, "date filter missing or different from ga4/config.py"


def test_profile_counts(tiny):
    p = run(tiny, "00_profile_and_quality.sql").iloc[0]
    assert p.total_events == 17
    assert p.total_users == 4
    assert p.total_sessions == 5            # u1 has two sessions, u2 has two, u3 one; u4 has none
    assert p.sessions_with_purchase == 3
    assert (p.days_with_data, p.days_expected) == (3, 92)
    assert p.events_missing_user == 0
    assert p.events_missing_session == 1    # u4
    assert p.duplicate_events == 1          # u3 page_view logged twice
    assert p.purchase_events == 3
    assert p.purchases_without_revenue == 1
    assert p.purchases_without_transaction_id == 1


def test_daily_kpis(tiny):
    df = run(tiny, "01_daily_kpis.sql")
    assert pd.to_datetime(df.day).dt.date.tolist() == [date(2020, 11, 1), date(2020, 11, 2), date(2020, 11, 3)]
    assert df.users.tolist() == [2, 2, 2]
    assert df.sessions.tolist() == [2, 2, 1]        # a missing ga_session_id is not a session
    assert df.purchases.tolist() == [1, 1, 1]
    assert df.revenue_usd.tolist() == [50.0, 30.0, 0.0]
    assert df.purchase_sessions.tolist() == [1, 1, 1]
    assert df.conversion_pct.tolist() == [50.0, 50.0, 100.0]


def test_traffic_sources_are_first_touch_per_user(tiny):
    df = run(tiny, "02_traffic_sources.sql").set_index("source")
    assert df.loc["google", ["users", "buyers", "revenue_usd", "buyer_rate_pct"]].tolist() == [2, 2, 80.0, 100.0]
    assert df.loc["(direct)", ["users", "buyers", "buyer_rate_pct"]].tolist() == [1, 0, 0.0]
    assert df.loc["newsletter", "medium"] == "email"


def test_funnel_steps_and_drop_off(tiny):
    df = run(tiny, "03_funnel.sql")
    assert df.step.tolist() == ["View item", "Add to cart", "Begin checkout", "Purchase"]
    assert df.users.tolist() == [3, 3, 2, 2]
    assert df.pct_of_first_step.tolist() == [100.0, 100.0, 66.7, 66.7]
    assert pd.isna(df.pct_of_previous_step[0])
    assert df.pct_of_previous_step[1:].tolist() == [100.0, 66.7, 100.0]


def test_rolling_trends_window_functions(tiny):
    df = run(tiny, "04_rolling_trends.sql")
    assert df.users_7d_avg.tolist() == [2.0, 2.0, 2.0]
    assert df.revenue_7d_avg.tolist() == [50.0, 40.0, 26.67]
    assert pd.isna(df.users_change_vs_prev_day[0])
    assert df.users_change_vs_prev_day[1:].tolist() == [0, 0]
    assert df.users_wow_pct.isna().all()            # need 7 earlier days for week-over-week


def test_top_products_unnest_and_rank(tiny):
    df = run(tiny, "05_top_products.sql")
    assert not {"(not set)", "<Other>"} & set(df["product"])
    tee = df[df["product"] == "Tee"].iloc[0]
    assert (tee.total_units, tee.total_revenue_usd, tee.rank_in_category) == (3, 60.0, 1)
    cap = df[df["product"] == "Cap"].iloc[0]
    assert cap.rank_in_category == 2
    assert df[df.category == "Home"].rank_in_category.tolist() == [1, 1]  # Mug and Bottle tie


def test_revenue_inr_joins_daily_rates(tiny):
    run(tiny, "01_daily_kpis.sql", table="mart_daily_kpis")
    fx = pd.DataFrame({"day": [date(2020, 11, 1), date(2020, 11, 2), date(2020, 11, 3)],
                       "usd_inr": [74.0, 74.5, 74.5], "is_filled": [True, False, False]})
    DuckDBWarehouse(tiny).load_frame(fx, "fx_usd_inr")
    df = run(tiny, "06_revenue_inr.sql")
    assert df.revenue_inr.tolist() == [3700.0, 2235.0, 0.0]
    assert df.rate_carried_forward.tolist() == [True, False, False]


def test_no_sql_selects_star_from_the_raw_export():
    # 💸 BigQuery bills by columns read — raw export meeda SELECT * ante anni nested columns scan
    for path in SQL_DIR.glob("*.sql"):
        assert not re.search(r"SELECT\s+\*\s+FROM\s+`bigquery-public-data", path.read_text(), re.I), path.name
