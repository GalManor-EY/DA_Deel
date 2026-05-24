# logic/in_payout_not_tms.py

import os
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from utils.db_sqlserver import get_engine


def run():
    engine = get_engine()

    # ✅ קורא את השאילתה מבחוץ מתיקיית Queries
    # שים לב: נתיב יחסי מה-root של הפרויקט (כמו שאתה מריץ בדרך כלל)
    sql_path = Path("Queries") / "in_payout_not_TMS.sql"
    query_sql = sql_path.read_text(encoding="utf-8")

    # אין יותר temp tables בלוגיקה החדשה -> build_sql נשאר ריק (כדי לשמור את המבנה אם תרצה בעתיד)
    build_sql = ""

    # שלב 1 – SQL שלא מחזיר rows (כאן לא אמור להיות כלום)
    if build_sql.strip():
        with engine.begin() as conn:
            conn.execute(text(build_sql))

    # שלב 2 – SQL שכן מחזיר rows (זה ה-CTE/SELECT החדש מתוך הקובץ SQL)
    df = pd.read_sql(text(query_sql), engine)

    os.makedirs("results", exist_ok=True)
    df.to_csv(r"results\in_payout_not_tms.csv", index=False)

    print("in_payout_not_tms completed:", len(df), "rows")
    return df


if __name__ == "__main__":
    run()