# 🧪 test_bq.py — BigQueryWarehouse correct jobs build chestundo chudadam (real BigQuery call ledu, client mock)
from unittest import mock

import pandas as pd
import pytest

bigquery = pytest.importorskip("google.cloud.bigquery")

from ga4.bq import BigQueryWarehouse  # noqa: E402


@pytest.fixture
def wh():
    with mock.patch.object(bigquery, "Client") as client_cls:
        w = BigQueryWarehouse("kittu-analytics")
    client_cls.assert_called_once_with(project="kittu-analytics", location="US")
    return w


def test_dataset_is_created_in_us_and_reruns_are_safe(wh):
    wh.ensure_dataset()
    ds = wh.client.create_dataset.call_args.args[0]
    assert ds.dataset_id == "ga4_analytics" and ds.location == "US"
    assert wh.client.create_dataset.call_args.kwargs == {"exists_ok": True}


def test_fx_load_uses_a_load_job_with_a_fixed_schema(wh):
    df = pd.DataFrame({"day": [pd.Timestamp("2020-11-01").date()], "usd_inr": [74.0], "is_filled": [True]})
    wh.load_frame(df, "fx_usd_inr")
    _, table = wh.client.load_table_from_dataframe.call_args.args
    cfg = wh.client.load_table_from_dataframe.call_args.kwargs["job_config"]
    assert table == "kittu-analytics.ga4_analytics.fx_usd_inr"
    assert [(f.name, f.field_type) for f in cfg.schema] == [("day", "DATE"), ("usd_inr", "FLOAT"), ("is_filled", "BOOLEAN")]
    assert cfg.write_disposition == "WRITE_TRUNCATE"


def test_mart_query_writes_to_its_table(wh):
    job = wh.client.query.return_value
    job.result.return_value.to_dataframe.return_value = pd.DataFrame({"x": [1]})
    job.total_bytes_processed = 123
    df, scanned = wh.query("03_funnel.sql", "mart_funnel")
    sql = wh.client.query.call_args.args[0]
    cfg = wh.client.query.call_args.kwargs["job_config"]
    assert "UNION ALL" in sql and scanned == 123 and len(df) == 1
    assert cfg.destination.table_id == "mart_funnel" and cfg.destination.dataset_id == "ga4_analytics"
    assert cfg.write_disposition == "WRITE_TRUNCATE"


def test_profile_query_is_not_saved(wh):
    wh.client.query.return_value.total_bytes_processed = None
    _, scanned = wh.query("00_profile_and_quality.sql")
    assert wh.client.query.call_args.kwargs["job_config"].destination is None
    assert scanned == 0
