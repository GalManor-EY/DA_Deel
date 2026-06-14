# staging/load_payment_contractor_withdrawal_diagnostic.py

import csv
from collections import defaultdict
from sqlalchemy import text
from utils.db_sqlserver import get_engine

CSV_PATH = r"\\ILTELRMPOPTAP01\uploads\Deel 2026\Q1-2026\Payments Table Contractor withdrawals.csv"
TABLE_NAME = "stg_payment_contractor_withdrawal_q1_2026"

BATCH_SIZE = 50000
PRINT_EVERY = 100000


def sanitize_base(col: str) -> str:
    col = (col or "").strip()
    col = col.replace("\ufeff", "")
    col = col.replace(" ", "_").replace("-", "_")

    return "".join(c if (c.isalnum() or c == "_") else "_" for c in col) or "COL"


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


def read_headers():
    print("STEP 1: read headers")

    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)

    if not headers:
        raise ValueError("Empty header")

    cols = sanitize_and_deduplicate(headers)
    print(f"  columns: {len(cols)}")
    return headers, cols


def create_table(engine, cols):
    print("STEP 2: create table")

    columns_sql = ",\n        ".join(f"[{c}] NVARCHAR(MAX)" for c in cols)

    ddl = f"""
    IF OBJECT_ID('dbo.{TABLE_NAME}', 'U') IS NOT NULL
        DROP TABLE dbo.{TABLE_NAME};

    CREATE TABLE dbo.{TABLE_NAME} (
        {columns_sql}
    );
    """

    with engine.begin() as conn:
        conn.execute(text(ddl))


def build_insert_sql(cols):
    placeholders = ", ".join(["?"] * len(cols))
    columns = ", ".join(f"[{c}]" for c in cols)
    return f"INSERT INTO dbo.{TABLE_NAME} ({columns}) VALUES ({placeholders})"


def normalize_row_values(row):
    return [None if v == "" else v for v in row]


def preview_row(row):
    return [str(v)[:80] for v in row[:8]]


def insert_batch(cursor, insert_sql, batch_rows, batch_meta):
    try:
        cursor.fast_executemany = True
        cursor.executemany(insert_sql, batch_rows)
    except Exception as batch_err:
        print("  batch failed → drilling down")

        for row_values, meta in zip(batch_rows, batch_meta):
            logical_row_num, physical_line_num, raw_row = meta
            try:
                cursor.execute(insert_sql, row_values)
            except Exception as row_err:
                print("\nFAILED ROW FOUND")
                print(f"  logical row : {logical_row_num:,}")
                print(f"  physical    : {physical_line_num:,}")
                print(f"  columns     : {len(raw_row)}")
                print(f"  preview     : {preview_row(raw_row)}")
                print(f"  error       : {row_err}")
                raise

        raise batch_err


def load_payment_contractor_withdrawal():
    print("START")

    engine = get_engine()

    # ✅ debug חכם – שלא תתבלבל שוב בין DBים
    with engine.connect() as conn:
        db = conn.execute(text("SELECT DB_NAME()")).scalar()
    print(f"Connected to DB: {db}")

    _, cols = read_headers()
    expected_cols = len(cols)

    create_table(engine, cols)

    print("STEP 3: diagnostic load")
    print(f"  expected columns: {expected_cols}")
    print(f"  batch size      : {BATCH_SIZE:,}")

    insert_sql = build_insert_sql(cols)

    raw_conn = engine.raw_connection()
    cursor = raw_conn.cursor()

    logical_row_num = 1

    batch_rows = []
    batch_meta = []

    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            logical_row_num += 1
            physical_line_num = reader.line_num

            if len(row) != expected_cols:
                print("\nBAD ROW STRUCTURE")
                print(f"  logical row : {logical_row_num:,}")
                print(f"  physical    : {physical_line_num:,}")
                print(f"  expected    : {expected_cols}")
                print(f"  actual      : {len(row)}")
                print(f"  preview     : {preview_row(row)}")
                raise ValueError("Column mismatch")

            batch_rows.append(normalize_row_values(row))
            batch_meta.append((logical_row_num, physical_line_num, row))

            if logical_row_num % PRINT_EVERY == 0:
                print(f"  parsed row {logical_row_num:,}")

            if len(batch_rows) >= BATCH_SIZE:
                insert_batch(cursor, insert_sql, batch_rows, batch_meta)
                raw_conn.commit()
                print(f"  loaded up to row {logical_row_num:,}")
                batch_rows.clear()
                batch_meta.clear()

    if batch_rows:
        insert_batch(cursor, insert_sql, batch_rows, batch_meta)
        raw_conn.commit()

    cursor.close()
    raw_conn.close()

    print("STEP 4: count rows")

    with engine.connect() as conn:
        cnt = conn.execute(text(f"SELECT COUNT(*) FROM dbo.{TABLE_NAME}")).scalar()

    print(f"  rows loaded: {cnt:,}")
    print("DONE ✅")


if __name__ == "__main__":
    load_payment_contractor_withdrawal()