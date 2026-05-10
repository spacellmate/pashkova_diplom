import os
import random
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from openpyxl import load_workbook

# ---------- Настройки Flask и БД ----------

app = Flask(__name__)

# SQLite в файле data.db в корне проекта
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------- Модели ----------


class Stats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visit_count = db.Column(db.Integer, nullable=False, default=0)
    form_count = db.Column(db.Integer, nullable=False, default=0)


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(255), nullable=False)
    employment = db.Column(db.String(255), nullable=False)
    skills = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())


# ---------- Инициализация БД и стартовых значений ----------


@app.before_first_request
def init_db():
    db.create_all()

    stats = Stats.query.get(1)
    if not stats:
        # стартовые значения счетчиков
        stats = Stats(id=1, visit_count=57112, form_count=2701)
        db.session.add(stats)
        db.session.commit()


# ---------- Хелпер: дописать заявку в Excel ----------


def append_to_excel(name, phone, region, employment, skills):
    """
    Дописывает новую строку в data/submissions.xlsx
    Предполагаем:
    - файл существует
    - лист называется 'submissions'
    - формат колонок: id, name, phone, region, employment, skills
    """
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "submissions.xlsx")

    if not os.path.exists(path):
        # если вдруг файла нет, можно либо создать новый, либо ничего не делать
        # здесь создадим минимальный файл такого же формата
        from openpyxl import Workbook

        wb_new = Workbook()
        ws_new = wb_new.active
        ws_new.title = "submissions"
        ws_new.append(["id", "name", "phone", "region", "employment", "skills"])
        wb_new.save(path)

    wb = load_workbook(path)
    ws = wb["submissions"]

    # последняя занятая строка
    last_row = ws.max_row
    # предполагаем, что первая строка — шапка, значит текущий max id = last_row - 1
    current_max_id = last_row - 1
    new_id = current_max_id + 1

    ws.append([new_id, name, phone, region, employment, skills])
    wb.save(path)


# ---------- Маршруты ----------


@app.route("/")
def index():
    stats = Stats.query.get(1)
    if not stats:
        stats = Stats(id=1, visit_count=57112, form_count=2701)
        db.session.add(stats)
        db.session.commit()

    stats.visit_count += 1
    db.session.commit()

    return render_template(
        "index.html",
        visit_count=stats.visit_count,
        form_count=stats.form_count,
    )


@app.route("/submit", methods=["POST"])
def submit():
    # Подгони имена полей под свой шаблон
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    region = request.form.get("region", "").strip()
    employment = request.form.get("employment", "").strip()
    skills = request.form.get("skills", "").strip()

    if not name or not phone:
        # Можно добавить флеш-сообщения, пока просто возвращаем на главную
        return redirect("/")

    # 1) сохранить в БД
    submission = Submission(
        name=name,
        phone=phone,
        region=region,
        employment=employment,
        skills=skills,
    )
    db.session.add(submission)

    stats = Stats.query.get(1)
    if not stats:
        stats = Stats(id=1, visit_count=57112, form_count=2701)
        db.session.add(stats)

    stats.form_count += 1

    db.session.commit()

    # 2) дописать в Excel поверх существующих 2701 строк
    try:
        append_to_excel(name, phone, region, employment, skills)
    except Exception as e:
        # чтобы падение Excel не ломало сайт; можно залогировать
        print("Ошибка записи в Excel:", e)

    return redirect("/")


# ---------- Локальный запуск ----------

if __name__ == "__main__":
    # на Render этот блок не используется, там запускается gunicorn app:app
    app.run(host="0.0.0.0", port=8000, debug=True)