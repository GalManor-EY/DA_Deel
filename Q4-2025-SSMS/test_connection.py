from utils.db_sqlserver import get_engine
from utils.sql_runner import run_query

engine = get_engine()
df = run_query(engine, "SELECT 1 AS ok")
print(df)
