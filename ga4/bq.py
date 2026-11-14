# ☁️ bq.py — BigQuery tho matladadam. Pipeline ki kavalsindi 3 methods matrame:
# ensure_dataset(), load_frame(df, table), query(sql_file, table) — tests lo DuckDB version same shape lo undi.
from pathlib import Path

from .config import DATASET, LOCATION

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


class BigQueryWarehouse:
    def __init__(self, project):
        from google.cloud import bigquery  # ikkada import — tests ki google-cloud install avasaram ledu

        self.bq = bigquery
        self.client = bigquery.Client(project=project, location=LOCATION)
        self.project = project

    def _table(self, name):
        return f"{self.project}.{DATASET}.{name}"

    def ensure_dataset(self):
        ds = self.bq.Dataset(f"{self.project}.{DATASET}")
        ds.location = LOCATION
        self.client.create_dataset(ds, exists_ok=True)

    def load_frame(self, df, table):
        # 📥 sandbox lo streaming inserts / DML (INSERT, UPDATE) panicheyyavu — load job ye correct
        schema = [self.bq.SchemaField("day", "DATE"),
                  self.bq.SchemaField("usd_inr", "FLOAT"),
                  self.bq.SchemaField("is_filled", "BOOLEAN")]
        cfg = self.bq.LoadJobConfig(schema=schema, write_disposition="WRITE_TRUNCATE")
        self.client.load_table_from_dataframe(df, self._table(table), job_config=cfg).result()

    def query(self, sql_file, table=None):
        """Run one sql/ file. With table, the result is also saved as that mart table."""
        cfg = self.bq.QueryJobConfig()
        if table:
            cfg.destination = self._table(table)
            cfg.write_disposition = "WRITE_TRUNCATE"
        job = self.client.query((SQL_DIR / sql_file).read_text(), job_config=cfg)
        df = job.result().to_dataframe()
        return df, job.total_bytes_processed or 0
