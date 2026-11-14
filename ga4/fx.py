# 💱 fx.py — Frankfurter API nunchi USD→INR rates techi, prathi calendar day ki oka rate undela fill cheyyadam
from datetime import timedelta

import pandas as pd
import requests

API = "https://api.frankfurter.dev/v2/rates"
LOOKBACK_DAYS = 7  # 1 Nov 2020 Sunday — mundu Friday rate kavali, anduke konchem mundu nunchi techukuntam


def fetch(start, end, http=requests):
    params = {
        "from": (start - timedelta(days=LOOKBACK_DAYS)).isoformat(),
        "to": end.isoformat(),
        "base": "USD",
        "quotes": "INR",
        "providers": "ECB",  # okka source matrame — re-run chesina same numbers ravali
    }
    resp = http.get(API, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def to_daily(rows, start, end):
    """API rows [{date, base, quote, rate}] -> one row per calendar day: day, usd_inr, is_filled."""
    df = pd.DataFrame(rows, columns=["date", "base", "quote", "rate"])
    df = df[(df["base"].str.upper() == "USD") & (df["quote"].str.upper() == "INR")]
    if df.empty:
        raise ValueError("API returned no USD→INR rates for this date range")

    rates = (df.assign(date=pd.to_datetime(df["date"]))
               .drop_duplicates("date", keep="last")
               .set_index("date")["rate"]
               .sort_index())
    days = pd.date_range(start, end, freq="D")
    # 🗓️ ECB weekends / holidays lo rate publish cheyyadu — last known rate ni carry forward chestam
    filled = rates.reindex(rates.index.union(days)).ffill().reindex(days)
    return pd.DataFrame({
        "day": days.date,
        "usd_inr": filled.round(4).to_numpy(),
        "is_filled": ~days.isin(rates.index),
    })
