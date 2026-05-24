from utils.db_sqlserver import get_engine
from utils.sql_runner import run_query

engine = get_engine()
df = run_query(engine, "SELECT 1 AS ok")
print(df)


import csv

path = r"\\ILTELRMPOPTAP01\uploads\Deel 2025\Q4-2025\updated version\AR - 2025 FY 29-4-26.csv"
with open(path, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    n = sum(1 for _ in reader)
print("Python logical records (excluding header):", n)
print("Columns in header:", len(header))




# --------------------------------------------------------------



import csv

CSV_PATH = r"\\ILTELRMPOPTAP01\uploads\Deel 2025\Q4-2025\updated version\AR - 2025 FY 29-4-26.csv"

MAX_BAD_TO_SHOW = 50     # כמה שורות בעייתיות להציג (כדי לא להציף)
PREVIEW_FIELDS = 12      # כמה שדות להציג מתוך השורה (preview)
SHOW_FULL_ROW = False    # אם True - ידפיס את כל השורה (עלול להיות ארוך/רגיש)

bad_found = 0
scanned = 0

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    expected = len(header)

    print("Expected columns:", expected)
    print("Header sample:", header[:min(expected, 20)])
    print("-" * 120)

    for line_num, row in enumerate(reader, start=2):  # שורה 1 זה header
        scanned += 1
        actual = len(row)

        if actual != expected:
            bad_found += 1

            print(f"❌ Bad row #{bad_found} | file line: {line_num} | actual cols: {actual} | expected: {expected}")

            if SHOW_FULL_ROW:
                print("Row (FULL):", row)
            else:
                preview = row[:PREVIEW_FIELDS]
                tail = f"... (+{actual - PREVIEW_FIELDS} more fields)" if actual > PREVIEW_FIELDS else ""
                print("Row (PREVIEW):", preview, tail)

            print("-" * 120)

            if bad_found >= MAX_BAD_TO_SHOW:
                print(f"Stopped after showing {MAX_BAD_TO_SHOW} bad rows (MAX_BAD_TO_SHOW).")
                break

print(f"\nScanned records (excluding header): {scanned}")
print(f"Bad records found: {bad_found}")

# ------------------------
