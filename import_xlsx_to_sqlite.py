from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
XLSX_PATH = BASE_DIR / "data" / "submissions.xlsx"
DB_PATH = BASE_DIR / "data.db"

if not XLSX_PATH.exists():
    raise SystemExit(f"Excel file not found: {XLSX_PATH}")

conn = sqlite3.connect(DB_PATH)

conn.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        name TEXT,
        phone TEXT,
        specialization TEXT,
        city TEXT,
        employment TEXT,
        consent INTEGER DEFAULT 0
    )
""")

df = pd.read_excel(XLSX_PATH)
print("Original columns:", list(df.columns))

rename_map = {
    "Имя": "name",
    "Name": "name",
    "Телефон": "phone",
    "Phone": "phone",
    "Специализация": "specialization",
    "specialization": "specialization",
    "Город": "city",
    "city": "city",
    "Район": "city",
    "Занятость": "employment",
    "employment": "employment",
    "Дата": "created_at",
    "created_at": "created_at",
    "Согласие": "consent",
    "consent": "consent",
}

df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

for col in ["created_at", "name", "phone", "specialization", "city", "employment", "consent"]:
    if col not in df.columns:
        df[col] = None

out = df[["created_at", "name", "phone", "specialization", "city", "employment", "consent"]].copy()

out["consent"] = out["consent"].fillna(0).apply(
    lambda x: 1 if str(x).strip().lower() in {"1", "true", "yes", "да", "on"} else 0
)

out.to_sql("leads", conn, if_exists="append", index=False)

conn.commit()
conn.close()

print(f"Imported {len(out)} rows into {DB_PATH}")