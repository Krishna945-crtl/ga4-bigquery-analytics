from datetime import date, timedelta

import duckdb
import pytest

# 🧱 GA4 export lo mana SQL vaade columns matrame — same names, same nesting
EVENTS_DDL = """
CREATE TABLE events (
  event_date VARCHAR,
  event_timestamp BIGINT,
  event_name VARCHAR,
  event_params STRUCT("key" VARCHAR, "value" STRUCT(string_value VARCHAR, int_value BIGINT))[],
  user_pseudo_id VARCHAR,
  traffic_source STRUCT("name" VARCHAR, medium VARCHAR, source VARCHAR),
  ecommerce STRUCT(purchase_revenue_in_usd DOUBLE, transaction_id VARCHAR),
  items STRUCT(item_name VARCHAR, item_category VARCHAR, quantity BIGINT, item_revenue_in_usd DOUBLE)[]
)
"""


def ev(day, ts, name, user, sid=None, source=("google", "organic"), revenue=None, tx=None, items=()):
    params = [{"key": "page_title", "value": {"string_value": "Home", "int_value": None}}]
    if sid is not None:
        params.append({"key": "ga_session_id", "value": {"string_value": None, "int_value": sid}})
    return (day, ts, name, params, user,
            {"name": "(organic)", "medium": source[1], "source": source[0]},
            {"purchase_revenue_in_usd": revenue, "transaction_id": tx},
            [{"item_name": n, "item_category": c, "quantity": q, "item_revenue_in_usd": r} for n, c, q, r in items])


def load_events(rows):
    con = duckdb.connect()
    con.execute(EVENTS_DDL)
    con.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
    return con


DIRECT, EMAIL = ("(direct)", "(none)"), ("newsletter", "email")
D1, D2, D3 = "20201101", "20201102", "20201103"

# ✍️ chinna hand-made data — prathi expected number tests lo chethi tho lekkapettinade
TINY = [
    # day 1: u1 full funnel and buys, u2 only browses
    ev(D1, 1, "page_view", "u1", 11), ev(D1, 2, "view_item", "u1", 11), ev(D1, 3, "add_to_cart", "u1", 11),
    ev(D1, 4, "begin_checkout", "u1", 11),
    ev(D1, 5, "purchase", "u1", 11, revenue=50.0, tx="T1",
       items=[("Tee", "Apparel", 2, 40.0), ("Mug", "Home", 1, 10.0)]),
    ev(D1, 6, "page_view", "u2", 21, DIRECT), ev(D1, 7, "view_item", "u2", 21, DIRECT),
    # day 2: u2 comes back and adds to cart, u3 buys; u3 page_view is logged twice (duplicate)
    ev(D2, 8, "view_item", "u2", 22, DIRECT), ev(D2, 9, "add_to_cart", "u2", 22, DIRECT),
    ev(D2, 10, "page_view", "u3", 31), ev(D2, 10, "page_view", "u3", 31), ev(D2, 11, "view_item", "u3", 31),
    ev(D2, 12, "add_to_cart", "u3", 31), ev(D2, 13, "begin_checkout", "u3", 31),
    ev(D2, 14, "purchase", "u3", 31, revenue=30.0, tx="T2",
       items=[("Tee", "Apparel", 1, 20.0), ("Bottle", "Home", 1, 10.0), ("(not set)", "Home", 1, 5.0), ("<Other>", "Home", 1, 4.0)]),
    # day 3: u4 has no ga_session_id; u1 buys again but revenue and transaction id are missing
    ev(D3, 15, "page_view", "u4", None, EMAIL),
    ev(D3, 16, "purchase", "u1", 12, revenue=None, tx="(not set)", items=[("Cap", "Apparel", 1, 15.0)]),
]


@pytest.fixture
def tiny():
    return load_events(TINY)


def full_rows(start=date(2020, 11, 1), end=date(2021, 1, 31)):
    """Every day of the real range: 3 users a day, a clean funnel, one purchase a day."""
    rows, ts, sources = [], 0, [("google", "organic"), DIRECT, EMAIL]
    for i in range((end - start).days + 1):
        day = (start + timedelta(days=i)).strftime("%Y%m%d")
        for k in range(3):
            user, sid, src = f"u{i}_{k}", i * 10 + k, sources[k]
            steps = ["page_view", "view_item"] + (["add_to_cart"] if k < 2 else []) + (["begin_checkout"] if k < 1 else [])
            for name in steps:
                ts += 1
                rows.append(ev(day, ts, name, user, sid, src))
            if k == 0:
                ts += 1
                revenue = 10.0 * (1 + i % 3)
                rows.append(ev(day, ts, "purchase", user, sid, src, revenue, f"T{i}",
                               [("Tee", "Apparel", 1, revenue)]))
    return rows


@pytest.fixture
def full():
    return load_events(full_rows())


def fx_rows(start=date(2020, 10, 25), end=date(2021, 1, 31), base_rate=74.0):
    """Frankfurter v2 shape, weekdays only (ECB doesn't publish on weekends)."""
    rows = []
    for i in range((end - start).days + 1):
        d = start + timedelta(days=i)
        if d.weekday() < 5:
            rows.append({"date": d.isoformat(), "base": "USD", "quote": "INR", "rate": round(base_rate + (i % 5) * 0.1, 4)})
    return rows


class FakeHttp:
    def __init__(self, payload):
        self.payload, self.calls = payload, []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        payload = self.payload

        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return payload

        return Resp()
