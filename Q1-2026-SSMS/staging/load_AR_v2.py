# staging/load_AR_fast_validate.py
import os
import time
import csv
import json
from collections import defaultdict

from sqlalchemy import text
from utils.db_sqlserver import get_engine

# =========================
# CONFIG
# =========================
CSV_PATH = r"\\ILTELRMPOPTAP01\uploads\Deel 2025\Q4-2025\updated version\AR - 2025 FY 29-4-26.csv"
TABLE_NAME = "AR_FY_25"

# Key column used to locate missing rows
KEY_COL = "UNIQUE_KEY"              # must exist in CSV header
BATCH_KEYS = 5000                   # batch size for checking existence via OPENJSON
PROGRESS_EVERY_ROWS = 300_000        # progress print while scanning CSV to locate missing
PRINT_FIRST_MISSING = 20            # print first N missing rows to screen

# progress / performance for FAST count
COUNT_CHUNK_SIZE = 64 * 1024 * 1024   # 64MB chunks (fewer I/O calls)
COUNT_PROGRESS_MB = 256               # print every 256MB read

# outputs when mismatch
OUT_DIR = os.path.dirname(CSV_PATH)
MISSING_ROWS_OUT = os.path.join(OUT_DIR, "AR_missing_rows.csv")
MISSING_KEYS_OUT = os.path.join(OUT_DIR, "AR_missing_keys.txt")

# =========================
# Helpers (same as your working version)
# =========================
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

def detect_row_terminator_robust(path: str) -> str:
    """
    Robust-ish terminator detection:
    reads head+tail and compares CRLF vs lone LF.
    """
    size = os.stat(path).st_size
    chunk = 2 * 1024 * 1024  # 2MB
    with open(path, "rb") as f:
        head = f.read(chunk)
        if size > chunk:
            f.seek(max(0, size - chunk))
            tail = f.read(chunk)
        else:
            tail = b""
    sample = head + b"\n" + tail

    crlf = sample.count(b"\r\n")
    lf = sample.count(b"\n")
    lone_lf = max(0, lf - crlf)
    return "0x0d0a" if crlf >= lone_lf else "0x0a"

def fast_physical_data_line_count(path: str,
                                 chunk_size: int = COUNT_CHUNK_SIZE,
                                 progress_mb: int = COUNT_PROGRESS_MB) -> int:
    """
    FAST count of physical lines:
    counts b'\\n' in binary stream.
    Returns data lines count (minus header line).
    """
    t0 = time.time()
    bytes_read = 0
    newlines = 0
    next_print = progress_mb * 1024 * 1024

    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            bytes_read += len(chunk)
            newlines += chunk.count(b"\n")

            if bytes_read >= next_print:
                mb = bytes_read / (1024 * 1024)
                rate = mb / (time.time() - t0) if (time.time() - t0) > 0 else 0
                print(f"⏱️ FastCount: read {mb:,.0f} MB | physical lines≈{newlines:,} | {rate:,.1f} MB/s | elapsed={(time.time()-t0)/60:.1f} min")
                next_print += progress_mb * 1024 * 1024

    data_lines = max(newlines - 1, 0)
    print(f"✅ FastCount done: physical lines={newlines:,} | data lines (minus header)={data_lines:,} | took={(time.time()-t0)/60:.2f} min")
    return data_lines

# =========================
# NEW: Locate missing rows by UNIQUE_KEY (fast + progress)
# =========================
def locate_missing_rows(engine, csv_path: str, expected_missing: int):
    """
    Scans the CSV and checks (in batches) which UNIQUE_KEY values are missing from dbo.TABLE_NAME.
    Writes missing rows to AR_missing_rows.csv (with source_line_num).
    Also writes missing keys to AR_missing_keys.txt.
    Stops early if it already found expected_missing rows (e.g., 13), to save time.
    """

    sql_missing_keys = f"""
    ;WITH k AS (
        SELECT [value] AS k
        FROM OPENJSON(:keys_json)
    )
    SELECT k.k
    FROM k
    LEFT JOIN dbo.{TABLE_NAME} t
        ON t.{KEY_COL} = k.k
    WHERE t.{KEY_COL} IS NULL;
    """

    print("-" * 120)
    print("🔎 Locating missing rows by UNIQUE_KEY (this may take time over UNC; progress will be printed)")
    print("CSV scan path:", csv_path)
    print("Output rows   :", MISSING_ROWS_OUT)
    print("Output keys   :", MISSING_KEYS_OUT)
    print(f"Batch={BATCH_KEYS} | Progress every {PROGRESS_EVERY_ROWS:,} rows | Stop early at {expected_missing} missing (if possible)")
    print("-" * 120)

    t0 = time.time()
    scanned = 0
    missing_found = 0
    printed = 0

    with open(csv_path, newline="", encoding="utf-8-sig") as f, \
         open(MISSING_ROWS_OUT, "w", newline="", encoding="utf-8") as out_csv, \
         open(MISSING_KEYS_OUT, "w", encoding="utf-8") as out_keys:

        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            raise ValueError("CSV header is empty while locating missing rows.")

        try:
            key_idx = header.index(KEY_COL)
        except ValueError:
            raise ValueError(f"Column '{KEY_COL}' not found in CSV header. Cannot locate missing rows.")

        w = csv.writer(out_csv)
        w.writerow(["source_line_num"] + header)

        batch_keys = []
        batch_rows = []  # (line_num, row, key)

        def process_batch(conn):
            nonlocal missing_found, printed
            if not batch_keys:
                return

            keys_json = json.dumps(batch_keys, ensure_ascii=False)
            rows = conn.execute(text(sql_missing_keys), {"keys_json": keys_json}).fetchall()
            if not rows:
                return

            miss = set(r[0] for r in rows)
            for line_num, row, k in batch_rows:
                if k in miss:
                    missing_found += 1
                    out_keys.write(k + "\n")
                    w.writerow([line_num] + row)

                    if printed < PRINT_FIRST_MISSING:
                        printed += 1
                        print(f"❌ Missing #{printed} | file line {line_num} | {KEY_COL}={k}")

        with engine.connect() as conn:
            last = time.time()

            for line_num, row in enumerate(reader, start=2):  # header is line 1
                scanned += 1
                k = row[key_idx].strip() if key_idx < len(row) and row[key_idx] else ""
                if not k:
                    continue

                batch_keys.append(k)
                batch_rows.append((line_num, row, k))

                if len(batch_keys) >= BATCH_KEYS:
                    process_batch(conn)
                    batch_keys.clear()
                    batch_rows.clear()

                    # Early stop if we've found all missing rows (saves time if missing appear early)
                    if expected_missing and missing_found >= expected_missing:
                        break

                if scanned % PROGRESS_EVERY_ROWS == 0:
                    now = time.time()
                    elapsed = now - t0
                    rate = scanned / elapsed if elapsed else 0
                    chunk = now - last
                    last = now
                    print(f"⏱️ LocateProgress: scanned={scanned:,} | missing_found={missing_found:,} | rate={rate:,.0f} rows/sec | elapsed={elapsed/60:.1f} min | lastChunk={chunk:.2f}s")

            # flush last partial batch
            if batch_keys and (not expected_missing or missing_found < expected_missing):
                process_batch(conn)

    print("-" * 120)
    print(f"✅ Missing locator done in {(time.time()-t0)/60:.1f} min")
    print(f"Scanned rows        : {scanned:,}")
    print(f"Missing rows found  : {missing_found:,}")
    print(f"Missing rows file   : {MISSING_ROWS_OUT}")
    print(f"Missing keys file   : {MISSING_KEYS_OUT}")
    print("-" * 120)

    return missing_found

# =========================
# Main
# =========================
def load_AR():
    engine = get_engine()

    print("🚀 Starting AR load (FAST validation + locate missing rows)")
    print("CSV_PATH:", CSV_PATH)
    print("TABLE: dbo." + TABLE_NAME)
    print("-" * 120)

    # 1) Read header
    t_hdr = time.time()
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader, None)

    if not headers:
        raise ValueError("CSV header is empty / invalid")

    cols = sanitize_and_deduplicate(headers)
    print(f"✅ Header read in {time.time() - t_hdr:.2f}s | cols={len(cols)}")

    # 2) CREATE TABLE
    #    Improvement for speed & missing-check:
    #    Make UNIQUE_KEY NVARCHAR(450) so we can index it (NVARCHAR(MAX) cannot be indexed).
    t_ddl = time.time()

    sql_key_name = sanitize_base(KEY_COL)  # should be UNIQUE_KEY
    col_defs = []
    for c in cols:
        if c == sql_key_name:
            col_defs.append(f"[{c}] NVARCHAR(450) NULL")
        else:
            col_defs.append(f"[{c}] NVARCHAR(MAX) NULL")
    columns_sql = ",\n        ".join(col_defs)

    ddl_sql = f"""
    IF OBJECT_ID('dbo.{TABLE_NAME}', 'U') IS NOT NULL
        DROP TABLE dbo.{TABLE_NAME};

    CREATE TABLE dbo.{TABLE_NAME} (
        {columns_sql}
    );

    -- Index for fast existence checks:
    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE name = 'IX_{TABLE_NAME}_{sql_key_name}'
          AND object_id = OBJECT_ID('dbo.{TABLE_NAME}')
    )
    BEGIN
        CREATE NONCLUSTERED INDEX [IX_{TABLE_NAME}_{sql_key_name}]
        ON dbo.{TABLE_NAME}([{sql_key_name}]);
    END
    """
    with engine.begin() as conn:
        conn.execute(text(ddl_sql))

    print(f"✅ Table created + index in {time.time() - t_ddl:.2f}s")

    # 3) BULK INSERT
    row_term = detect_row_terminator_robust(CSV_PATH)
    print(f"✅ Detected ROWTERMINATOR={row_term}")

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
        TABLOCK,
        MAXERRORS = 0
    );
    """

    print("📥 Running BULK INSERT...")
    t_bulk = time.time()
    with engine.begin() as conn:
        conn.execute(text(bulk_sql))
        loaded = conn.execute(text(f"SELECT COUNT(*) FROM dbo.{TABLE_NAME}")).scalar()
    print(f"✅ BULK finished in {time.time() - t_bulk:.2f}s | rows loaded: {loaded:,}")

    # 4) FAST validation
    print("🔎 FAST validation: counting physical data lines (binary \\n count) ...")
    expected_fast = fast_physical_data_line_count(CSV_PATH)

    # 5) Compare + if mismatch => locate missing rows and STOP
    if loaded != expected_fast:
        diff = expected_fast - loaded
        print("-" * 120)
        print("❌ FAST VALIDATION MISMATCH!")
        print(f"Expected (fast physical data lines): {expected_fast:,}")
        print(f"Loaded (SQL COUNT)                : {loaded:,}")
        print(f"Difference (expected - loaded)    : {diff:,}")
        print("-" * 120)

        # locate missing rows by UNIQUE_KEY and write them out
        missing_found = locate_missing_rows(engine, CSV_PATH, expected_missing=diff)

        raise RuntimeError(
            f"Stopped intentionally after locating missing rows.\n"
            f"Expected (fast lines): {expected_fast:,}\n"
            f"Loaded (SQL)         : {loaded:,}\n"
            f"Missing (diff)       : {diff:,}\n"
            f"Missing located      : {missing_found:,}\n"
            f"See missing rows file: {MISSING_ROWS_OUT}"
        )

    print("✅ FAST VALIDATION PASSED: SQL COUNT matches fast physical data-line count")
    print("-" * 120)

if __name__ == "__main__":
    load_AR()