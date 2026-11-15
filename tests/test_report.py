# 🧪 test_report.py — README table lo GA4 placeholders ("<Other>") kanipinchali, daakkokudadu
import pandas as pd

from ga4 import report


def test_placeholder_values_are_escaped_for_github_markdown():
    marts = {
        "mart_daily_kpis": pd.DataFrame({"revenue_usd": [10.0]}),
        "mart_revenue_inr": pd.DataFrame({"revenue_inr": [740.0]}),
        "mart_funnel": pd.DataFrame({"step_order": [1], "step": ["View item"], "users": [5],
                                     "pct_of_first_step": [100.0], "pct_of_previous_step": [None]}),
        "mart_traffic_sources": pd.DataFrame({"source": ["<Other>"], "medium": ["referral"], "users": [5],
                                              "buyer_rate_pct": [20.0]}),
        "mart_top_products": pd.DataFrame({"product": ["Tee | Black"], "category": ["Apparel"],
                                           "total_units": [1], "total_revenue_usd": [10.0]}),
    }
    profile = {"total_users": 5, "total_sessions": 6, "sessions_with_purchase": 1, "purchase_events": 1}
    text = report.build(profile, marts, [], 0)
    assert "| &lt;Other&gt; / referral |" in text
    assert "Tee \\| Black" in text
    assert "<Other>" not in text
