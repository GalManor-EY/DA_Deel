
import os
from sqlalchemy import create_engine

def get_engine():
    host = os.environ["MYSQL_HOST"]
    port = os.environ.get("MYSQL_PORT", "3306")
    user = os.environ["MYSQL_USER"]
    password = os.environ["MYSQL_PASSWORD"]
    database = os.environ["MYSQL_DB"]

    return create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}")
