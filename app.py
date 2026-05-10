from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

class Stats:
    def __init__(self):
        self.visit_count = 57112
        self.form_count = 2701

stats = Stats()

@app.before_request
def count_visit():
    # считаем только просмотры главной страницы
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
    name = request.form.get("name") or request.form.get("f-name")
    phone = request.form.get("phone") or request.form.get("f-phone")
    spec = request.form.get("skills") or request.form.get("f-spec")
    district = request.form.get("region") or request.form.get("f-district")
    work_format = request.form.get("employment") or request.form.get("f-format")

    stats.form_count += 1
    app.logger.info(
        f"[{datetime.now()}] form #{stats.form_count} "
        f"name={name!r} phone={phone!r} spec={spec!r} "
        f"district={district!r} format={work_format!r}"
    )

    # после отправки просто возвращаем ту же страницу (чтобы обновились счётчики)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)