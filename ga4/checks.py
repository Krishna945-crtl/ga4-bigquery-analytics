# 🧪 checks.py — data quality rules: FX rates, raw GA4 profile, final marts
# Prathi rule oka row istundi: (check, value, status, detail). FAIL aithe pipeline aagipotundi.
import pandas as pd

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


def _row(check, value, ok, detail, bad=FAIL):
    return {"check": check, "value": value, "status": PASS if ok else bad, "detail": detail}


def _share(part, whole):
    return part / whole if whole else 0.0


def check_fx(daily, start, end):
    expected = (end - start).days + 1
    jumps = daily["usd_inr"].pct_change().abs().max()
    return [
        _row("fx: one rate per calendar day", len(daily), len(daily) == expected, f"expected {expected} days"),
        _row("fx: no missing rates", int(daily["usd_inr"].isna().sum()), daily["usd_inr"].notna().all(),
             "a missing rate would make INR revenue empty"),
        _row("fx: rates look like USD→INR", round(float(daily["usd_inr"].mean()), 2),
             daily["usd_inr"].between(40, 150).all(), "every rate between 40 and 150"),
        _row("fx: no sudden day-to-day jump", round(float(jumps * 100), 2) if pd.notna(jumps) else 0.0,
             not (jumps > 0.03), "max day-to-day change under 3%", bad=WARN),
    ]


def check_source(p):
    """p = the one-row profile from 00_profile_and_quality.sql, as a dict."""
    events, purchases = p["total_events"], p["purchase_events"]
    return [
        _row("raw: every day has data", p["days_with_data"], p["days_with_data"] == p["days_expected"],
             f"expected {p['days_expected']} days — a missing day breaks the rolling averages"),
        _row("raw: no events without a user", p["events_missing_user"], p["events_missing_user"] == 0,
             "user_pseudo_id is the key for users, funnel and traffic sources"),
        _row("raw: events without ga_session_id", p["events_missing_session"],
             _share(p["events_missing_session"], events) < 0.01, "under 1% of events", bad=WARN),
        _row("raw: duplicate events", p["duplicate_events"],
             _share(p["duplicate_events"], events) < 0.001, "same user + timestamp + event name, under 0.1%", bad=WARN),
        _row("raw: purchases without revenue", p["purchases_without_revenue"],
             _share(p["purchases_without_revenue"], purchases) < 0.05, "under 5% of purchases", bad=WARN),
        _row("raw: purchases without transaction_id", p["purchases_without_transaction_id"],
             p["purchases_without_transaction_id"] == 0, "obfuscated sample can hide ids — reported, not fixed", bad=WARN),
    ]


def check_marts(marts):
    funnel = marts["mart_funnel"].sort_values("step_order")["users"].tolist()
    inr = marts["mart_revenue_inr"]
    daily = marts["mart_daily_kpis"]
    return [
        _row("mart: funnel never grows step to step", funnel, all(a >= b for a, b in zip(funnel, funnel[1:])),
             "open funnel can break this slightly; flagged so it gets a look", bad=WARN),
        _row("mart: INR revenue present every day", int(inr["revenue_inr"].isna().sum()), inr["revenue_inr"].notna().all(),
             "a gap means the FX join missed a day"),
        _row("mart: KPI and INR marts cover the same days", len(daily), len(daily) == len(inr), f"{len(inr)} INR rows"),
    ]


def stop_on_fail(rows, stage):
    failed = [r for r in rows if r["status"] == FAIL]
    if failed:
        lines = "\n".join(f"  - {r['check']}: {r['value']} ({r['detail']})" for r in failed)
        raise SystemExit(f"❌ Data quality FAIL in {stage}, stopping:\n{lines}")
