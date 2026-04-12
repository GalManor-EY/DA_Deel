
from utils.db_mysql import get_engine

from utils.sql_runner import load_sql, run_query

def run():
    engine = get_engine()
    sql = load_sql(r"Queries/in_payout_not_tms.sql")
    df = run_query(engine, sql)
    df.to_csv("results/payout_not_tms.csv", index=False)
    print("payout_not_tms rows:", len(df))
