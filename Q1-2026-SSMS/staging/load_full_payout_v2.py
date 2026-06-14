# staging/load_full_payout_diagnostic.py

import csv
from collections import defaultdict
from sqlalchemy import text
from utils.db_sqlserver import get_engine

CSV_PATH = r"\\ILTELRMPOPTAP01\uploads\Deel 2026\Q1-2026\All Payout table Withdrawals (2025,2026).csv"
TABLE_NAME = "stg_full_payout_q1_2026"

BATCH_SIZE = 100000          # אפשר להעלות ל-10000 אם בא לך
PRINT_EVERY = 100000       # הדפסת התקדמות כל X שורות


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


def build_insert_sql(cols):
    placeholders = ", ".join(["?"] * len(cols))
    columns = ", ".join(f"[{c}]" for c in cols)
    return f"INSERT INTO dbo.{TABLE_NAME} ({columns}) VALUES ({placeholders})"


def normalize_row_values(row):
    # אפשר לשנות אם אתה רוצה לשמור empty string במקום None
    return [None if v == "" else v for v in row]


def preview_row(row, max_cols=8, max_len=80):
    preview = []
    for v in row[:max_cols]:
        s = "" if v is None else str(v)
        s = s.replace("\n", "\\n").replace("\r", "\\r")
        if len(s) > max_len:
            s = s[:max_len] + "..."
        preview.append(s)
    return preview


def insert_batch(cursor, insert_sql, batch_rows, batch_meta):
    """
    batch_rows  = list of row values
    batch_meta  = list of tuples: (logical_row_num, physical_line_num, raw_row)
    """
    try:
        cursor.fast_executemany = True
        cursor.executemany(insert_sql, batch_rows)
        return None
    except Exception as batch_err:
        print("  batch failed -> drilling down to single row")
        print(f"  batch first logical row: {batch_meta[0][0]:,}")
        print(f"  batch last logical row : {batch_meta[-1][0]:,}")
        print(f"  batch error            : {batch_err}")

        # rollback before row-by-row
        cursor.connection.rollback()

        for row_values, meta in zip(batch_rows, batch_meta):
            logical_row_num, physical_line_num, raw_row = meta
            try:
                cursor.execute(insert_sql, row_values)
            except Exception as row_err:
                print()
                print("FAILED ROW FOUND")
                print(f"  logical CSV row : {logical_row_num:,}")
                print(f"  physical line   : {physical_line_num:,}")
                print(f"  column count    : {len(raw_row)}")
                print(f"  row preview     : {preview_row(raw_row)}")
                print(f"  error           : {row_err}")
                raise

        # אם מסיבה כלשהי הכל עבר row-by-row, נחזיר את השגיאה המקורית
        raise batch_err


def load_full_payout_diagnostic():
    print("START")

    engine = get_engine()

    original_headers, cols = read_headers()
    expected_cols = len(cols)

    create_table(engine, cols)

    print("STEP 3: diagnostic load")
    print(f"  expected columns: {expected_cols}")
    print(f"  batch size      : {BATCH_SIZE:,}")

    insert_sql = build_insert_sql(cols)

    raw_conn = engine.raw_connection()
    cursor = raw_conn.cursor()

    loaded_rows = 0
    logical_row_num = 1  # header = row 1 in logical CSV terms

    batch_rows = []
    batch_meta = []

    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)

        # skip header
        next(reader)

        while True:
            try:
                row = next(reader)
            except StopIteration:
                break
            except csv.Error as e:
                print()
                print("CSV PARSE ERROR")
                print(f"  around physical line: {reader.line_num:,}")
                print(f"  error               : {e}")
                raise

            logical_row_num += 1
            physical_line_num = reader.line_num

            if len(row) != expected_cols:
                print()
                print("BAD ROW STRUCTURE")
                print(f"  logical CSV row : {logical_row_num:,}")
                print(f"  physical line   : {physical_line_num:,}")
                print(f"  expected cols   : {expected_cols}")
                print(f"  actual cols     : {len(row)}")
                print(f"  row preview     : {preview_row(row)}")
                raise ValueError(
                    f"Row {logical_row_num} has {len(row)} columns instead of {expected_cols}"
                )

            batch_rows.append(normalize_row_values(row))
            batch_meta.append((logical_row_num, physical_line_num, row))

            if logical_row_num % PRINT_EVERY == 0:
                print(f"  parsed row {logical_row_num:,}")

            if len(batch_rows) >= BATCH_SIZE:
                insert_batch(cursor, insert_sql, batch_rows, batch_meta)
                raw_conn.commit()
                loaded_rows += len(batch_rows)
                print(f"  loaded up to logical row {logical_row_num:,}")
                batch_rows.clear()
                batch_meta.clear()

    if batch_rows:
        insert_batch(cursor, insert_sql, batch_rows, batch_meta)
        raw_conn.commit()
        loaded_rows += len(batch_rows)

    cursor.close()
    raw_conn.close()

    print("STEP 4: count rows")
    with engine.connect() as conn:
        cnt = conn.execute(text(f"SELECT COUNT(*) FROM dbo.{TABLE_NAME}")).scalar()
    print(f"  rows loaded: {cnt:,}")

    print("DONE ✅")


if __name__ == "__main__":
    load_full_payout_diagnostic()