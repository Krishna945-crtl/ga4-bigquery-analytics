# ⚙️ config.py — project antha share chese settings okka chota
from datetime import date

SOURCE = "bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*"
START, END = date(2020, 11, 1), date(2021, 1, 31)  # sql/ files lo kuda same range undi (test check chestundi)

DATASET = "ga4_analytics"
LOCATION = "US"  # public GA4 sample US lo undi — mana dataset kuda same location lo undali

PROFILE_SQL = "00_profile_and_quality.sql"

# (sql file, mart table) — order matters: 06 anedi 01 table + fx table meeda depend avtundi
MARTS = [
    ("01_daily_kpis.sql", "mart_daily_kpis"),
    ("02_traffic_sources.sql", "mart_traffic_sources"),
    ("03_funnel.sql", "mart_funnel"),
    ("04_rolling_trends.sql", "mart_rolling_trends"),
    ("05_top_products.sql", "mart_top_products"),
    ("06_revenue_inr.sql", "mart_revenue_inr"),
]
