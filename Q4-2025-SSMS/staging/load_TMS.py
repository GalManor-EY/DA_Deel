# staging/load_tms.py
import csv
from collections import defaultdict
from sqlalchemy import text
from utils.db_sqlserver import get_engine

# עדכן אם שם הקובץ אצלך שונה
CSV_PATH = r"\\ILTELRMPOPTAP01\uploads\Deel 2025\Q4-2025\Q4 2025 - TMS Transactions & Reconciliations.csv"
TABLE_NAME = "stg_tms_transactions_q4_2025"

def sanitize_base(col: str) -> str:
    """
    מנקה שם עמודה שיהיה חוקי ב-SQL Server:
    - מסיר BOM אם קיים
    - מחליף רווחים/מקפים ל-_ 
    - מסיר תווים בעייתיים
    """
    col = (col or "").strip()
    col = col.replace("\ufeff", "")  # BOM
    col = col.replace(" ", "_").replace("-", "_")

    # ניקוי תווים בעייתיים לשמות עמודות
    # משאיר אותיות, מספרים ו-_
    cleaned = []
    for ch in col:
        if ch.isalnum() or ch == "_":
            cleaned.append(ch)
        else:
            cleaned.append("_")
    col = "".join(cleaned)

    # לא לאפשר שם ריק
    return col if col else "COL"

def sanitize_and_deduplicate(headers):
    """
    מוודא שכל שמות העמודות ייחודיים.
    אם יש כפילות: RECONCILIATION_ID, RECONCILIATION_ID -> RECONCILIATION_ID, RECONCILIATION_ID_2
    """
    counts = defaultdict(int)
    cols = []

    for i, h in enumerate(headers, start=1):
        base = sanitize_base(h)

        # אם יצא COL (ריק), נוסיף אינדקס כדי שלא יהיו כפילויות
        if base == "COL":
            base = f"COL_{i}"

        counts[base] += 1
        if counts[base] == 1:
            cols.append(base)
        else:
            cols.append(f"{base}_{counts[base]}")

    return cols

def load_tms():
    engine = get_engine()

    # 1) קריאת header בלבד
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

    if not headers:
        raise ValueError("CSV header is empty / invalid")

    cols = sanitize_and_deduplicate(headers)

    # 2) CREATE TABLE דינמי (staging)
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

    # 3) BULK INSERT (הנתיב חייב להיות נגיש ל-SQL Server Service)
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

    print(f"✅ Loaded TMS into dbo.{TABLE_NAME}")

