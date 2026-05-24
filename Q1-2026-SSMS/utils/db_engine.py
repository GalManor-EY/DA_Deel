from sqlalchemy import create_engine

engine = create_engine(
    "mssql+pyodbc://SERVER_NAME/DB_NAME?driver=ODBC+Driver+17+for+SQL+Server",
    fast_executemany=True
)