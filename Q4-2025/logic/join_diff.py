
# logic/join_diff.py

from utils.db_mysql import run_query, load_sql
import pandas as pd

def run_join_diff():
    query = load_sql("queries/join_diff.sql")
    df = run_query(query)
    df.to_csv("results/join_diff.csv", index=False)
    print("join_diff completed:", len(df), "rows")

