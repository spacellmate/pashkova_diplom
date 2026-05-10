from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
DB_PATH = BASE_DIR / "data.db"

INITIAL_VISITS = 57116
INITIAL_FORMS = 2702

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                specialization TEXT,
                city TEXT,
                employment TEXT,
                consent INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()


def get_form_count():
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM leads").fetchone()
        return INITIAL_FORMS + (row["cnt"] if row else 0)


visit_count = INITIAL_VISITS
init_db()


@app.before_request
def count_visit():
    global visit_count
    if request.endpoint == "index" and request.method == "GET":
        visit_count += 1
        app.logger.info(f"[{datetime.now()}] visit #{visit_count}")


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "povar.html",
        visit_count=visit_count,
        form_count=get_form_count(),
    )


@app.route("/submit", methods=["POST"])
def submit():
    name = (request.form.get("f-name") or "").strip()
    phone = (request.form.get("f-phone") or "").strip()
    spec = (request.form.get("f-spec") or "").strip()
    city = (request.form.get("f-district") or "").strip()
    employment = (request.form.get("f-format") or "").strip()
    consent = 1 if request.form.get("f-consent") == "on" else 0

    if not name or not phone:
        return redirect(url_for("index"))

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO leads (
                created_at, name, phone, specialization, city, employment, consent
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(timespec="seconds"),
            name,
            phone,
            spec,
            city,
            employment,
            consent,
        ))
        conn.commit()

    app.logger.info(
        f"[{datetime.now()}] lead saved "
        f"name={name!r} phone={phone!r} spec={spec!r} city={city!r} employment={employment!r}"
    )

    return redirect(url_for("index"))


if __name__ == "__main__":
    print("DB_PATH =", DB_PATH)
    print("DB_EXISTS =", DB_PATH.exists())
    app.run(host="0.0.0.0", port=8000, debug=True)