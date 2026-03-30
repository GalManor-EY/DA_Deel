
from utils.db_mysql import get_engine
from utils.sql_runner import load_sql, run_sql

def run():
    engine = get_engine()
    sql = load_sql("queries/payout_not_tms_cutoff.sql")
    df = run_sql(engine, sql)
    df.to_csv("results/payout_not_tms_cutoff.csv", index=False)
    print("payout_not_tms_cutoff rows:", len(df))
