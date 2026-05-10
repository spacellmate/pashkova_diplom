from flask import Flask, render_template, request, redirect, url_for, Response
from datetime import datetime
from pathlib import Path
import sqlite3
import html
import os

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "data.db")))
INITIAL_VISITS = 57116
INITIAL_FORMS = 2702
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "changeme-admin-token")

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
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
        conn.commit()


def get_db_count():
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM leads").fetchone()
        return row["cnt"] if row else 0


def get_form_count():
    return INITIAL_FORMS + get_db_count()


def esc(value):
    return html.escape(str(value if value is not None else ""))


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
                created_at,
                name,
                phone,
                specialization,
                city,
                employment,
                consent
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
        f"name={name!r} phone={phone!r} spec={spec!r} "
        f"city={city!r} employment={employment!r}"
    )

    return redirect(url_for("index"))


@app.route("/admin/leads", methods=["GET"])
def admin_leads():
    token = request.args.get("token", "")
    if token != ADMIN_TOKEN:
        return Response("Forbidden", status=403)

    with get_conn() as conn:
        rows = conn.execute("""
            SELECT
                id,
                name,
                phone,
                specialization,
                city,
                employment,
                consent
            FROM leads
            ORDER BY id DESC
        """).fetchall()

    rows_html = "".join(
        f"""
        <tr>
          <td>{esc(row["id"])}</td>
          <td>{esc(row["name"])}</td>
          <td>{esc(row["phone"])}</td>
          <td>{esc(row["specialization"])}</td>
          <td>{esc(row["city"])}</td>
          <td>{esc(row["employment"])}</td>
          <td>{"Да" if row["consent"] else "Нет"}</td>
        </tr>
        """
        for row in rows
    )

    page = f"""
    <!doctype html>
    <html lang="ru">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Заявки</title>
      <style>
        body {{
          margin: 0;
          font-family: Arial, sans-serif;
          background: #f6f6f4;
          color: #1a1a18;
        }}
        .wrap {{
          max-width: 1280px;
          margin: 0 auto;
          padding: 24px;
        }}
        .top {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 16px;
          flex-wrap: wrap;
          margin-bottom: 20px;
        }}
        .stats {{
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }}
        .chip {{
          background: #fff;
          border: 1px solid rgba(0, 0, 0, .08);
          border-radius: 12px;
          padding: 10px 14px;
        }}
        .table-wrap {{
          overflow: auto;
          border: 1px solid rgba(0, 0, 0, .08);
          border-radius: 16px;
          background: #fff;
        }}
        table {{
          width: 100%;
          border-collapse: collapse;
        }}
        th, td {{
          padding: 12px;
          border-bottom: 1px solid rgba(0, 0, 0, .08);
          text-align: left;
          vertical-align: top;
          font-size: 14px;
          white-space: nowrap;
        }}
        th {{
          background: #f0eee9;
          position: sticky;
          top: 0;
        }}
        tr:hover td {{
          background: #faf9f6;
        }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="top">
          <div>
            <h1 style="margin:0 0 6px;">Все заявки</h1>
            <div style="color:#6b6a66;">База: {esc(str(DB_PATH))}</div>
          </div>
          <div class="stats">
            <div class="chip">Записей в БД: <strong>{len(rows)}</strong></div>
            <div class="chip">Счётчик форм на сайте: <strong>{get_form_count()}</strong></div>
          </div>
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Имя</th>
                <th>Телефон</th>
                <th>Специализация</th>
                <th>Город</th>
                <th>Занятость</th>
                <th>Согласие</th>
              </tr>
            </thead>
            <tbody>
              {rows_html or '<tr><td colspan="7">Записей пока нет</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    </body>
    </html>
    """
    return Response(page, mimetype="text/html; charset=utf-8")


if __name__ == "__main__":
    print("DB_PATH =", DB_PATH)
    print("ADMIN URL = /admin/leads?token=" + ADMIN_TOKEN)
    app.run(host="0.0.0.0", port=8000, debug=True)