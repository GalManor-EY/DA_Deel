# staging/load_payment_contractor_withdrawal.py
import csv
from collections import defaultdict
from sqlalchemy import text
from utils.db_sqlserver import get_engine

# 🔁 עדכן את שם הקובץ לפי מה שיש לך בפועל בתיקייה
CSV_PATH = r"\\ILTELRMPOPTAP01\uploads\Deel 2025\Q4-2025\payment_contractor_withdrawal.csv"

# שם טבלת staging ב-DB
TABLE_NAME = "stg_payment_contractor_withdrawal"


def sanitize_base(col: str) -> str:
    col = (col or "").strip()
    col = col.replace("\ufeff", "")  # BOM
    col = col.replace(" ", "_").replace("-", "_")

    cleaned = []
    for ch in col:
        if ch.isalnum() or ch == "_":
            cleaned.append(ch)
        else:
            cleaned.append("_")
    col = "".join(cleaned)

    return col if col else "COL"


def sanitize_and_deduplicate(headers):
    """
    מוודא שמות עמודות ייחודיים, כי ב-CSV לפעמים יש כפילויות.
    """
    counts = defaultdict(int)
    cols = []

    for i, h in enumerate(headers, start=1):
        base = sanitize_base(h)
        if base == "COL":
            base = f"COL_{i}"

        counts[base] += 1
        if counts[base] == 1:
            cols.append(base)
        else:
            cols.append(f"{base}_{counts[base]}")

    return cols


def load_payment_contractor_withdrawal():
    engine = get_engine()

    # 1) Read header only
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

    if not headers:
        raise ValueError("CSV header is empty / invalid")

    cols = sanitize_and_deduplicate(headers)

    # 2) Create table dynamically
    columns_sql = ",\n        ".join(f"[{c}] NVARCHAR(MAX)" for c in cols)

    ddl_sql = f"""
    IF OBJECT_ID('dbo.{TABLE_NAME}', 'U') IS NOT NULL
        DROP TABLE dbo.{TABLE_NAME};

    CREATE TABLE dbo.{TABLE_NAME} (
        {columns_sql}
    );
    """

    with engine.begin() as conn:
        conn.execute(text(ddl_sql))

    # 3) Bulk insert
    bulk_sql = f"""
    BULK INSERT dbo.{TABLE_NAME}
    FROM '{CSV_PATH}'
    WITH (
        FIRSTROW = 2,
        FIELDTERMINATOR = ',',
        ROWTERMINATOR = '0x0a',
        TABLOCK
    );
    """

    with engine.begin() as conn:
        conn.execute(text(bulk_sql))
        rows = conn.execute(text(f"SELECT COUNT(*) FROM dbo.{TABLE_NAME};")).scalar()

    print(f"✅ Loaded payment_contractor_withdrawal into dbo.{TABLE_NAME} | rows loaded: {rows}")

