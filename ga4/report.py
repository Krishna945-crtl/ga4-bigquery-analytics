# 📝 report.py — pipeline results nunchi README lo "Results" section rayadam
import html
from datetime import date

import pandas as pd

START, END = "<!-- RESULTS:START -->", "<!-- RESULTS:END -->"


def _int(n):
    return f"{int(n):,}"


def _cell(x):
    # GA4 sample lo "<Other>" lanti values untayi — escape cheyyakapothe GitHub HTML tag anukoni daachestundi
    return html.escape(str(x), quote=False).replace("|", "\\|")


def _pct(x):
    return "—" if pd.isna(x) else f"{x:.1f}%"


def build(profile, marts, dq, scanned_bytes, run_day=None):
    daily, inr = marts["mart_daily_kpis"], marts["mart_revenue_inr"]
    funnel = marts["mart_funnel"].sort_values("step_order")
    sources = marts["mart_traffic_sources"].sort_values("users", ascending=False).head(5)
    products = marts["mart_top_products"].sort_values("total_revenue_usd", ascending=False).head(5)
    sessions = profile["total_sessions"]
    conversion = 100 * profile["sessions_with_purchase"] / sessions if sessions else 0.0

    out = [
        f"_Last run: {run_day or date.today():%d %b %Y} · {len(daily)} days · {scanned_bytes / 1e9:.2f} GB scanned_",
        "",
        "| KPI (1 Nov 2020 – 31 Jan 2021) | Value |",
        "|---|---|",
        f"| Users | {_int(profile['total_users'])} |",
        f"| Sessions | {_int(sessions)} |",
        f"| Purchases | {_int(profile['purchase_events'])} |",
        f"| Revenue (USD) | ${daily['revenue_usd'].sum():,.0f} |",
        f"| Revenue (INR, daily ECB rate) | ₹{inr['revenue_inr'].sum():,.0f} |",
        f"| Session conversion rate | {conversion:.2f}% |",
        "",
        "**Funnel** (users who reached each step)",
        "",
        "| Step | Users | % of viewers | % of previous step |",
        "|---|---|---|---|",
    ]
    out += [f"| {_cell(r.step)} | {_int(r.users)} | {_pct(r.pct_of_first_step)} | {_pct(r.pct_of_previous_step)} |"
            for r in funnel.itertuples()]

    worst = funnel.dropna(subset=["pct_of_previous_step"]).sort_values("pct_of_previous_step").head(1)
    if len(worst):
        w = worst.iloc[0]
        out += ["", f"Biggest drop-off: only **{w.pct_of_previous_step:.1f}%** of users move on to *{w.step}*."]

    out += ["", "**Top first-touch traffic sources**", "", "| Source / medium | Users | Buyer rate |", "|---|---|---|"]
    out += [f"| {_cell(r.source)} / {_cell(r.medium)} | {_int(r.users)} | {_pct(r.buyer_rate_pct)} |" for r in sources.itertuples()]

    out += ["", "**Top products by revenue**", "", "| Product | Category | Units | Revenue (USD) |", "|---|---|---|---|"]
    out += [f"| {_cell(r.product)} | {_cell(r.category)} | {_int(r.total_units)} | ${r.total_revenue_usd:,.0f} |"
            for r in products.itertuples()]

    out += ["", "**Data quality checks**", "", "| Check | Value | Status |", "|---|---|---|"]
    out += [f"| {r['check']} | {r['value']} | {r['status']} |" for r in dq]
    return "\n".join(out)


def update_readme(path, text):
    s = path.read_text(encoding="utf-8")
    a, b = s.index(START) + len(START), s.index(END)
    path.write_text(s[:a] + "\n" + text + "\n" + s[b:], encoding="utf-8")
