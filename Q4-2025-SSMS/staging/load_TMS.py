# staging/load_tms.py
import csv
from sqlalchemy import text
from utils.db_sqlserver import get_engine

CSV_PATH = r"\\ILTELRMPOPTAP01\uploads\Deel 2025\Q4-2025\Q4 2025 - TMS Transactions & Reconciliations.csv"
TABLE_NAME = "stg_tms_transactions_q4_2025"

def sanitize(col: str) -> str:
    col = col.strip()
    col = col.replace("\ufeff", "")
    col = col.replace(" ", "_").replace("-", "_")
    return col

def load_tms():
    engine = get_engine()

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

    cols = [sanitize(h) for h in headers if h and h.strip()]
    if not cols:
        raise ValueError("CSV header is empty / invalid")

    columns_sql = ",\n    ".join(f"[{c}] NVARCHAR(MAX)" for c in cols)

    ddl_sql = f"""
    IF OBJECT_ID('dbo.{TABLE_NAME}', 'U') IS NOT NULL DROP TABLE dbo.{TABLE_NAME};
    CREATE TABLE dbo.{TABLE_NAME} (
        {columns_sql}
    );
    """

    with engine.begin() as conn:
        conn.execute(text(ddl_sql))

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
