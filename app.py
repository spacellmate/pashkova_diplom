from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'data.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Stats:
    def __init__(self):
        self.visit_count = 57112
        self.form_count = 2701


stats = Stats()


class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(64), nullable=False)
    specialization = db.Column(db.String(512), nullable=True)
    city = db.Column(db.String(255), nullable=True)
    employment = db.Column(db.String(255), nullable=True)
    consent = db.Column(db.Boolean, default=False, nullable=False)


with app.app_context():
    db.create_all()


@app.before_request
def count_visit():
    if request.endpoint == "index" and request.method == "GET":
        stats.visit_count += 1
        app.logger.info(f"[{datetime.now()}] visit #{stats.visit_count}")


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "povar.html",
        visit_count=stats.visit_count,
        form_count=stats.form_count,
    )


@app.route("/submit", methods=["POST"])
def submit():
    # Имена полей должны совпадать с атрибутами name в форме
    name = request.form.get("f-name", "").strip()
    phone = request.form.get("f-phone", "").strip()
    spec = request.form.get("f-spec", "").strip()
    city = request.form.get("f-district", "").strip()
    employment = request.form.get("f-format", "").strip()
    consent = request.form.get("f-consent") == "on"

    if not name or not phone:
        # Можно вернуть 400 или просто редирект без увеличения счётчика
        return redirect(url_for("index"))

    lead = Lead(
        name=name,
        phone=phone,
        specialization=spec,
        city=city,
        employment=employment,
        consent=consent,
    )
    db.session.add(lead)
    db.session.commit()

    stats.form_count += 1
    app.logger.info(
        f"[{datetime.now()}] form #{stats.form_count} "
        f"name={name!r} phone={phone!r} spec={spec!r} "
        f"city={city!r} employment={employment!r} consent={consent!r}"
    )

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)