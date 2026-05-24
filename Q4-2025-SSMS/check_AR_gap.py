

import csv
import json
import os
import time
from sqlalchemy import text

# משתמש באותו engine שלך
from utils.db_sqlserver import get_engine

CSV_PATH = r"\\ILTELRMPOPTAP01\uploads\Deel 2025\Q4-2025\updated version\AR - 2025 FY 29-4-26.csv"
TABLE_NAME = "dbo.AR_FY_25"
KEY_COL = "UNIQUE_KEY"

OUT_DIR = os.path.dirname(CSV_PATH)
MISSING_OUT = os.path.join(OUT_DIR, "AR_missing_rows.csv")
MISSING_KEYS_OUT = os.path.join(OUT_DIR, "AR_missing_keys.txt")

# גודל batch לבדיקה מול SQL (OPENJSON מאפשר גדול, אבל נשמור סביר)
BATCH_SIZE = 5000

# פרוגרס כל כמה רשומות להדפיס
PROGRESS_EVERY = 200_000

# כמה "דוגמאות" להדפיס למסך כשמוצאים חסרים
PRINT_FIRST_MISSING = 5


SQL_MISSING_KEYS = f"""
;WITH k AS (
    SELECT [value] AS k
    FROM OPENJSON(:keys_json)
)
SELECT k.k
FROM k
LEFT JOIN {TABLE_NAME} t
    ON t.{KEY_COL} = k.k
WHERE t.{KEY_COL} IS NULL;
"""


def fmt(n: int) -> str:
    return f"{n:,}"


def find_missing_rows():
    t0 = time.time()
    print("🚀 Starting missing-rows scan")
    print("CSV:", CSV_PATH)
    print("Table:", TABLE_NAME)
    print("Key column:", KEY_COL)
    print("Batch size:", BATCH_SIZE)
    print("Progress every:", fmt(PROGRESS_EVERY))
    print("Output missing rows:", MISSING_OUT)
    print("Output missing keys:", MISSING_KEYS_OUT)
    print("-" * 120)

    engine = get_engine()
    print("✅ Engine ready")

    # נפתח CSV ונזהה אינדקס של UNIQUE_KEY
    with open(CSV_PATH, newline="", encoding="utf-8") as f, \
         open(MISSING_OUT, "w", newline="", encoding="utf-8") as out_csv, \
         open(MISSING_KEYS_OUT, "w", encoding="utf-8") as out_keys:

        reader = csv.reader(f)
        header = next(reader)
        if not header:
            raise ValueError("Empty header")

        try:
            key_idx = header.index(KEY_COL)
        except ValueError:
            raise ValueError(f"Column {KEY_COL} not found in header")

        writer = csv.writer(out_csv)
        # נשמור את כל השורה המקורית + line_num בתחילת השורה
        writer.writerow(["source_line_num"] + header)

        print(f"✅ Header read | columns={len(header)} | key_idx={key_idx}")
        print("-" * 120)

        scanned = 0
        missing_count = 0
        printed_missing = 0

        batch_rows = []   # נשמור שורות מלאות (כדי לכתוב אותן אם חסרות)
        batch_keys = []   # נשמור מפתחות תואמים

        last_progress_t = time.time()

        def process_batch(conn):
            nonlocal missing_count, printed_missing
            if not batch_keys:
                return

            keys_json = json.dumps(batch_keys, ensure_ascii=False)

            # נשלוף מה-DB רק את המפתחות החסרים מתוך ה-batch
            missing_keys = conn.execute(text(SQL_MISSING_KEYS), {"keys_json": keys_json}).fetchall()
            if not missing_keys:
                return

            missing_set = set(k[0] for k in missing_keys)
            for line_num, row, k in batch_rows:
                if k in missing_set:
                    missing_count += 1
                    out_keys.write(f"{k}\n")
                    writer.writerow([line_num] + row)

                    if printed_missing < PRINT_FIRST_MISSING:
                        printed_missing += 1
                        print(f"❌ Missing example #{printed_missing} | file line {line_num} | key={k}")

        with engine.connect() as conn:
            print("✅ Connected to SQL")
            print("🔎 Scanning CSV and checking existence in SQL...")
            print("-" * 120)

            for line_num, row in enumerate(reader, start=2):
                scanned += 1

                # מפתח
                k = row[key_idx] if key_idx < len(row) else None
                if not k:
                    # אם יש מפתח ריק - נשמור גם את זה כמקרה חריג (אופציונלי)
                    # אבל לא נספור כחסר מול SQL כי אין מה להשוות
                    continue

                batch_rows.append((line_num, row, k))
                batch_keys.append(k)

                # עיבוד batch
                if len(batch_keys) >= BATCH_SIZE:
                    process_batch(conn)
                    batch_rows.clear()
                    batch_keys.clear()

                # פרוגרס
                if scanned % PROGRESS_EVERY == 0:
                    now = time.time()
                    elapsed = now - t0
                    rate = scanned / elapsed if elapsed > 0 else 0
                    chunk = now - last_progress_t
                    last_progress_t = now
                    print(
                        f"⏱️ Scanned={fmt(scanned)} | Missing(found so far)={fmt(missing_count)} | "
                        f"Rate={rate:,.0f} rows/sec | LastChunk={chunk:.2f}s | Elapsed={elapsed/60:.1f} min"
                    )

            # batch אחרון
            if batch_keys:
                process_batch(conn)

    total = time.time() - t0
    print("-" * 120)
    print("✅ Done")
    print(f"Total scanned rows (excluding header): {fmt(scanned)}")
    print(f"Total missing rows found: {fmt(missing_count)}")
    print(f"Total time: {total:.2f}s ({total/60:.2f} min)")
    print(f"Missing rows file: {MISSING_OUT}")
    print(f"Missing keys file: {MISSING_KEYS_OUT}")
    print("-" * 120)
    print("💡 עכשיו תוכל לפתוח את AR_missing_rows.csv וללכת לפי source_line_num לקובץ המקורי (Ctrl+G ב-VSCode).")


if __name__ == "__main__":
    find_missing_rows()
