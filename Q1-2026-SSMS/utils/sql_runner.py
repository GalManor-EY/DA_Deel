
from pathlib import Path
import pandas as pd
from sqlalchemy import text

def load_sql(sql_file_path: str) -> str:
    return Path(sql_file_path).read_text(encoding="utf-8")

def run_query(engine, sql: str, params: dict | None = None) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})
