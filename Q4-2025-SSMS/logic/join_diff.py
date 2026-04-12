
# logic/join_diff.py

import os
from utils.sql_runner import run_query, load_sql
from utils.db_mysql import get_engine
import pandas as pd

def run():
    query = load_sql(r"Queries/join_diff.sql")
    engine = get_engine()
    df = run_query(engine, query)

    os.makedirs("results", exist_ok=True)
    df.to_csv(r"results\join_diff.csv", index=False)
    print("join_diff completed:", len(df), "rows")
    return df


