# staging/load_payment_contractor_withdrawal.py

import csv
from collections import defaultdict
from sqlalchemy import text
from utils.db_sqlserver import get_engine

CSV_PATH = r"\\ILTELRMPOPTAP01\uploads\Deel 2025\Q4-2025\Payment Table contractor withdrawal.csv"
TABLE_NAME = "stg_payment_contractor_withdrawal"


def sanitize_base(col: str) -> str:
    """
    מנקה שם עמודה שיהיה חוקי ב-SQL Server
    """
    col = (col or "").strip()
    col = col.replace("\ufeff", "")  # BOM
    col = col.replace(" ", "_").replace("-", "_")

    cleaned = []
    for ch in col:
        cleaned.append(ch if (ch.isalnum() or ch == "_") else "_")
    col = "".join(cleaned)

    return col if col else "COL"


def sanitize_and_deduplicate(headers):
    """
    מוודא שכל שמות העמודות ייחודיים
    """
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
    """
    מזהה האם השורות הן LF או CRLF
    """
    with open(path, "rb") as f:
        sample = f.read(1024 * 1024)  # 1MB
    return "0x0d0a" if b"\r\n" in sample else "0x0a"


def load_payment_contractor_withdrawal():
    engine = get_engine()

    # 1️⃣ קריאת header בלבד (CSV עם גרשיים/פסיקים נטען נכון בפייתון)
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

    if not headers:
        raise ValueError("CSV header is empty / invalid")

    cols = sanitize_and_deduplicate(headers)

    # 2️⃣ CREATE TABLE
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

    # 3️⃣ BULK INSERT עם תמיכה מלאה ב-CSV
    row_term = detect_row_terminator(CSV_PATH)

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

    with engine.begin() as conn:
        conn.execute(text(bulk_sql))
        rows = conn.execute(
            text(f"SELECT COUNT(*) FROM dbo.{TABLE_NAME}")
        ).scalar()

    print(f"✅ Loaded payment_contractor_withdrawal into dbo.{TABLE_NAME} | rows loaded: {rows}")