# staging/load_tms.py
import csv
from collections import defaultdict
from sqlalchemy import text
from utils.db_sqlserver import get_engine
import os

CSV_PATH = r"\\ILTELRMPOPTAP01\uploads\Deel 2026\Q1-2026\TMS Withdrawals Q1 2026.csv"
TABLE_NAME = "stg_tms_transactions_q1_2026"

def sanitize_base(col: str) -> str:
    col = (col or "").strip()
    col = col.replace("\ufeff", "")  # BOM
    col = col.replace(" ", "_").replace("-", "_")
    cleaned = []
    for ch in col:
        cleaned.append(ch if (ch.isalnum() or ch == "_") else "_")
    col = "".join(cleaned)
    return col if col else "COL"

def sanitize_and_deduplicate(headers):
    counts = defaultdict(int)
    cols = []
    for i, h in enumerate(headers, start=1):
        base = sanitize_base(h)
        if base == "COL":
            base = f"COL_{i}"
        counts[base] += 1
        cols.append(base if counts[base] == 1 else f"{base}_{counts[base]}")
    return cols

def detect_row_terminator(path: str) -> str:
    with open(path, "rb") as f:
        sample = f.read(1024 * 1024)
    return "0x0d0a" if b"\r\n" in sample else "0x0a"

def load_tms():
    print("🚀 Starting load_tms...")

    engine = get_engine()

    # ✅ בדיקה לאיזה DB מחוברים
    try:
        with engine.connect() as conn:
            db = conn.execute(text("SELECT DB_NAME()")).scalar()
            print(f"✅ Connected to DB: {db}")
    except Exception as e:
        print(f"❌ Failed DB connection: {e}")
        raise

    # ✅ בדיקה שהקובץ קיים
    print(f"\n📂 File path:\n{CSV_PATH}")
    file_exists = os.path.exists(CSV_PATH)
    print(f"📌 File exists? {file_exists}")

    if not file_exists:
        raise FileNotFoundError(f"❌ File not found: {CSV_PATH}")

    # ✅ קריאת headers
    print("\n📄 Reading CSV header...")
    try:
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
        print(f"✅ Headers loaded: {len(headers)} columns")
    except Exception as e:
        print(f"❌ Failed reading CSV: {e}")
        raise

    if not headers:
        raise ValueError("❌ CSV header is empty / invalid")

    cols = sanitize_and_deduplicate(headers)

    columns_sql = ",\n        ".join(f"[{c}] NVARCHAR(MAX)" for c in cols)

    ddl_sql = f"""
    IF OBJECT_ID('dbo.{TABLE_NAME}', 'U') IS NOT NULL
        DROP TABLE dbo.{TABLE_NAME};

    CREATE TABLE dbo.{TABLE_NAME} (
        {columns_sql}
    );
    """

    print("\n🧱 Creating table...")

    try:
        with engine.begin() as conn:
            conn.execute(text(ddl_sql))
        print(f"✅ Table created: dbo.{TABLE_NAME}")
    except Exception as e:
        print(f"❌ Failed creating table: {e}")
        raise

    # ✅ detect row terminator
    row_term = detect_row_terminator(CSV_PATH)
    print(f"\n🔍 Row terminator detected: {row_term}")

    bulk_sql = f"""
    BULK INSERT dbo.{TABLE_NAME}
    FROM '{CSV_PATH}'
    WITH (
        FIRSTROW = 2,
        FORMAT = 'CSV',
        FIELDTERMINATOR = ',',
        FIELDQUOTE = '"',
        ROWTERMINATOR = '{row_term}',
        CODEPAGE = '65001',
        TABLOCK
    );
    """

    print("\n⚡ Running BULK INSERT...")
    print("---- BULK SQL START ----")
    print(bulk_sql)
    print("---- BULK SQL END ----")

    try:
        with engine.begin() as conn:
            conn.execute(text(bulk_sql))
        print("✅ BULK INSERT finished")
    except Exception as e:
        print(f"❌ BULK INSERT failed: {e}")
        raise

    # ✅ בדיקת שורות
    print("\n🔎 Checking row count...")

    try:
        with engine.connect() as conn:
            count = conn.execute(text(f"SELECT COUNT(*) FROM dbo.{TABLE_NAME}")).scalar()
            print(f"✅ Rows loaded: {count}")
    except Exception as e:
        print(f"❌ Failed counting rows: {e}")
        raise

    print(f"\n🎉 DONE: Loaded TMS into dbo.{TABLE_NAME}")


if __name__ == "__main__":
    load_tms()
