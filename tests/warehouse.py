# 🦆 warehouse.py — BigQuery badulu DuckDB: same sql/ files ni sqlglot tho translate chesi local ga run cheyyadam.
# GCP account lekunda CI lo SQL logic test avvali — anduke idi.
import sqlglot

from ga4.bq import SQL_DIR
from ga4.config import DATASET, SOURCE


def to_duckdb(sql):
    sql = (sql.replace(f"`{SOURCE}`", "events")
              .replace("_TABLE_SUFFIX", "event_date")  # mana fake events okka table — suffix badulu event_date
              .replace(f"{DATASET}.", ""))
    return sqlglot.transpile(sql, read="bigquery", write="duckdb")[0]


class DuckDBWarehouse:
    """Same 3 methods as ga4.bq.BigQueryWarehouse, backed by an in-memory DuckDB."""

    def __init__(self, con):
        self.con = con

    def ensure_dataset(self):
        pass

    def load_frame(self, df, table):
        self.con.register("_frame", df)
        self.con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM _frame")
        self.con.unregister("_frame")

    def query(self, sql_file, table=None):
        df = self.con.execute(to_duckdb((SQL_DIR / sql_file).read_text())).df()
        if table:
            self.load_frame(df, table)
        return df, 0
