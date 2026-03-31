from utils.db_mysql import get_engine
from utils.sql_runner import load_sql, run_sql

def run():
    engine = get_engine()
    sql = load_sql("queries/tms_not_payout.sql")
    df = run_sql(engine, sql)
    df.to_csv("results/tms_not_payout.csv", index=False)
    print("tms_not_payout rows:", len(df))
