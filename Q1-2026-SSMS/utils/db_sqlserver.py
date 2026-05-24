# utils/db_sqlserver.py
import os
from sqlalchemy import create_engine

def get_engine():
    server = os.environ["MSSQL_SERVER"]      # למשל: ILTELRMPOPTAP01
    database = os.environ["MSSQL_DATABASE"]  # למשל: Deel_2025

    conn_str = (
        f"mssql+pyodbc://@{server}/{database}"
        "?driver=ODBC+Driver+17+for+SQL+Server"
        "&trusted_connection=yes"
    )

    return create_engine(conn_str, fast_executemany=True)