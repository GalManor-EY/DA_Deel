# logic/in_tms_not_in_payout.py

from utils.sql_runner import load_sql, run_query
from utils.db_sqlserver import get_engine

def run():
    engine = get_engine()
    sql = load_sql(r"Queries/in_tms_not_payout.sql")
    df = run_query(engine, sql)

    df.to_csv("results/tms_not_payout.csv", index=False)
    print("tms_not_payout rows:", len(df))
    return df