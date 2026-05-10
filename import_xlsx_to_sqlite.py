from pathlib import Path
import sqlite3
import pandas as pd
import os

BASE_DIR = Path(__file__).resolve().parent
XLSX_PATH = Path(os.getenv("XLSX_PATH", str(BASE_DIR / "submissions.xlsx")))
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "data.db")))

if not XLSX_PATH.exists():
    raise SystemExit(f"Excel file not found: {XLSX_PATH}")

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB_PATH)

conn.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        specialization TEXT,
        city TEXT,
        employment TEXT,
        consent INTEGER NOT NULL DEFAULT 0
    )
""")

existing = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
if existing > 0:
    raise SystemExit(
        f"Table leads already contains {existing} rows. "
        f"Stop import to avoid duplicates."
    )

df = pd.read_excel(XLSX_PATH)

required = {"name", "phone", "region", "employment", "skills"}
missing = required - set(df.columns)
if missing:
    raise SystemExit(f"Missing required columns in Excel: {sorted(missing)}")

out = pd.DataFrame({
    "created_at": [None] * len(df),
    "name": df["name"].fillna("").astype(str),
    "phone": df["phone"].fillna("").astype(str),
    "specialization": df["skills"].fillna("").astype(str),
    "city": df["region"].fillna("").astype(str),
    "employment": df["employment"].fillna("").astype(str),
    "consent": [1] * len(df),
})

out = out[
    (out["name"].str.strip() != "") &
    (out["phone"].str.strip() != "")
]

out.to_sql("leads", conn, if_exists="append", index=False)

conn.commit()
conn.close()

print(f"Imported {len(out)} rows from {XLSX_PATH} into {DB_PATH}")