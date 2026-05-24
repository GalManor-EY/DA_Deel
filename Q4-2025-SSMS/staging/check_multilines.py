import csv
import os
import time

# ===== CONFIG =====
CSV_PATH = r"\\ILTELRMPOPTAP01\uploads\Deel 2025\Q4-2025\updated version\AR - 2025 FY 29-4-26.csv"
KEY_COL = "UNIQUE_KEY"

OUT_DIR = os.path.dirname(CSV_PATH)
OUT_PATH = os.path.join(OUT_DIR, "AR_multiline_records_report.csv")

PROGRESS_EVERY = 300_000        # הדפסת התקדמות כל כמה רשומות לוגיות
MAX_REPORT = None               # למשל 200 כדי להגביל. None = בלי הגבלה
PREVIEW_CHARS = 120             # כמה תווים להראות בפריוויו

def trunc(s: str, n: int) -> str:
    s = s.replace("\r", "\\r").replace("\n", "\\n")
    return s if len(s) <= n else s[:n] + "..."

def main():
    print("🚀 Scanning CSV for embedded newlines inside fields (multiline CSV records)")
    print("CSV:", CSV_PATH)
    print("OUT:", OUT_PATH)
    print("-" * 120)

    t0 = time.time()

    found = 0
    extra_physical_lines_total = 0
    scanned_records = 0

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f, open(OUT_PATH, "w", newline="", encoding="utf-8") as out:
        reader = csv.reader(f)
        writer = csv.writer(out)

        header = next(reader, None)
        if not header:
            raise ValueError("CSV header is empty / invalid")

        try:
            key_idx = header.index(KEY_COL)
        except ValueError:
            key_idx = None
            print(f"⚠️ KEY_COL '{KEY_COL}' not found in header. Report will not include UNIQUE_KEY.")

        # Report header
        writer.writerow([
            "record_num",
            "start_line",
            "end_line",
            "extra_physical_lines",
            "unique_key",
            "fields_with_newline_indexes",
            "fields_with_newline_names",
            "preview"
        ])

        # header is physical line 1
        prev_end_line = 1

        last = time.time()

        for record_num, row in enumerate(reader, start=1):
            scanned_records += 1

            # reader.line_num = physical line number read up to end of this record
            end_line = reader.line_num
            start_line = prev_end_line + 1
            prev_end_line = end_line

            # detect newline chars inside any field
            newline_fields = [i for i, v in enumerate(row) if isinstance(v, str) and ("\n" in v or "\r" in v)]

            # a record is "multiline" if it spans multiple physical lines OR has newline inside a field
            extra_lines = max(0, end_line - start_line)
            is_multiline = (extra_lines > 0) or (len(newline_fields) > 0)

            if is_multiline:
                found += 1
                extra_physical_lines_total += extra_lines

                uk = row[key_idx] if (key_idx is not None and key_idx < len(row)) else ""
                idxs = ";".join(str(i) for i in newline_fields) if newline_fields else ""
                names = ";".join(header[i] for i in newline_fields if i < len(header)) if newline_fields else ""

                # build preview from the first problematic field (or just first columns)
                if newline_fields:
                    pv = f"{header[newline_fields[0]]}: {trunc(row[newline_fields[0]], PREVIEW_CHARS)}"
                else:
                    pv = trunc(" | ".join(row[:5]), PREVIEW_CHARS)

                writer.writerow([record_num, start_line, end_line, extra_lines, uk, idxs, names, pv])

                if MAX_REPORT is not None and found >= MAX_REPORT:
                    print(f"🛑 Reached MAX_REPORT={MAX_REPORT}. Stopping early.")
                    break

            if scanned_records % PROGRESS_EVERY == 0:
                now = time.time()
                elapsed = now - t0
                rate = scanned_records / elapsed if elapsed else 0
                print(
                    f"⏱️ Progress: records={scanned_records:,} | multiline_found={found:,} | "
                    f"extra_physical_lines_sum={extra_physical_lines_total:,} | "
                    f"rate={rate:,.0f} rec/sec | elapsed={elapsed/60:.1f} min | lastChunk={now-last:.2f}s"
                )
                last = now

    total = time.time() - t0
    print("-" * 120)
    print("✅ Done")
    print(f"Scanned logical records: {scanned_records:,}")
    print(f"Multiline records found: {found:,}")
    print(f"Sum of extra physical lines (end-start): {extra_physical_lines_total:,}")
    print(f"Report written to: {OUT_PATH}")
    print(f"Total time: {total/60:.1f} min")

    print("\n📌 What to look for:")
    print("- If 'Sum of extra physical lines' ~= 13, that explains EMEditor showing +13 lines.")
    print("- Use start_line/end_line in EMEditor to jump to the exact location.")

if __name__ == "__main__":
    main()
