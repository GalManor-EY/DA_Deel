from utils.db_sqlserver import get_engine
from utils.sql_runner import run_query

def run_sql_file(engine, path):
    with open(path, "r", encoding="utf-8") as f:
        run_query(engine, f.read())

def main():
    engine = get_engine()
    run_sql_file(engine, "staging/load_payout.sql")
    run_sql_file(engine, "staging/load_tms.sql")

if __name__ == "__main__":
    main()



    