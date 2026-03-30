

# load_data.py

import pandas as pd
from sqlalchemy import create_engine
import pymysql

# ---- MySQL connection settings ----
HOST = "10.120.190.86"
PORT = 3306
USER = "mysqlgal"
PASSWORD = "jjRs2q!Z"
DATABASE = "Deel_2025"

def load_payout_q4_25():
    TABLE = "payout_q4_25"

    # ---- CSV file location ----
    CSV_PATH = r"\\ILTELRMPOPTAP01\uploads\Deel 2025\Q4-2025\Q4 2025 Contractor Withdrawals.csv"

    print("Loading PAYOUT CSV...")
    df = pd.read_csv(CSV_PATH)
    print(f"Rows in file: {len(df)}")

    # ---- Create MySQL engine ----
    connection_string = (
        f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    )
    engine = create_engine(connection_string)

    print("Uploading PAYOUT to MySQL...")
    df.to_sql(
        TABLE,
        engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=5000
    )

    print(f"Upload complete. {len(df)} rows inserted into '{TABLE}'.")
    print("Done.")
