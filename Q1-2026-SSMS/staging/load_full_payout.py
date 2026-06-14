# staging/load_full_payout.py

import csv
import subprocess
from collections import defaultdict
from sqlalchemy import text
from utils.db_sqlserver import get_engine

CSV_PATH = r"\\ILTELRMPOPTAP01\uploads\Deel 2026\Q1-2026\All Payout table Withdrawals (2025,2026).csv"
TABLE_NAME = "stg_full_payout_q1_2026"


def sanitize_base(col: str) -> str:
    col = (col or "").strip()
    col = col.replace("\ufeff", "")
    col = col.replace(" ", "_").replace("-", "_")

    out = []
    for c in col:
        out.append(c if (c.isalnum() or c == "_") else "_")

    col = "".join(out)
    return col if col else "COL"


def sanitize_and_deduplicate(headers):
    counts = defaultdict(int)
    cols = []

    for i, h in enumerate(headers, 1):
        base = sanitize_base(h)
        if base == "COL":
            base = f"COL_{i}"

        counts[base] += 1
        cols.append(base if counts[base] == 1 else f"{base}_{counts[base]}")

    return cols


def get_headers():
    print("STEP 1: read headers")

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

    if not headers:
        raise ValueError("Empty header")

    print(f"  columns: {len(headers)}")
    return sanitize_and_deduplicate(headers)


def create_table(engine, cols):
    print("STEP 2: create table")

    cols_sql = ",\n        ".join(f"[{c}] NVARCHAR(MAX)" for c in cols)

    ddl = f"""
    IF OBJECT_ID('dbo.{TABLE_NAME}', 'U') IS NOT NULL
        DROP TABLE dbo.{TABLE_NAME};

    CREATE TABLE dbo.{TABLE_NAME} (
        {cols_sql}
    );
    """

    with engine.begin() as conn:
        conn.execute(text(ddl))


def get_server_db(engine):
    with engine.connect() as conn:
        server = conn.execute(text("SELECT @@SERVERNAME")).scalar()
        db = conn.execute(text("SELECT DB_NAME()")).scalar()
    return server, db



def run_bulk(engine):
    print("STEP 3: BULK INSERT (sqlcmd)")

    server = "tcp:ILTELRMPOPTAP01,1433"
    db = "deel_2026"

    path = CSV_PATH.replace("'", "''")

    sql = (    
    f"BULK INSERT dbo.{TABLE_NAME} "
    f"FROM '{path}' "
    f"WITH ("
    f"FIRSTROW = 2, "
    f"FIELDTERMINATOR = ',', "
    f"ROWTERMINATOR = '0x0a', "
    f"CODEPAGE = '65001', "
    f"TABLOCK, "
    f"BATCHSIZE = 100000, "
    f"ROWS_PER_BATCH = 100000, "
    f"MAXERRORS = 10000"
    f");"
    )

    print(f"  server={server}")

    subprocess.run(
        ["sqlcmd", "-S", server, "-d", db, "-E", "-Q", sql],
        check=True
    )



def count_rows(engine):
    print("STEP 4: count rows")

    with engine.connect() as conn:
        cnt = conn.execute(text(f"SELECT COUNT(*) FROM dbo.{TABLE_NAME}")).scalar()

    print(f"  rows loaded: {cnt:,}")


def load_full_payout():
    print("START")

    engine = get_engine()

    cols = get_headers()
    create_table(engine, cols)
    run_bulk(engine)
    count_rows(engine)

    print("DONE ✅")


if __name__ == "__main__":
    load_full_payout()