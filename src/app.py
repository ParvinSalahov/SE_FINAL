import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from flask import Flask, render_template
from markupsafe import escape

import db
from auth import auth_bp, current_player
from quiz import quiz_bp
from results import results_bp


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-only-change-me",
)
app.config["DATABASE"] = os.environ.get(
    "QUIZ_DB_PATH",
    os.path.join(BASE_DIR, "quiz.db"),
)

db.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(quiz_bp)
app.register_blueprint(results_bp)


@app.get("/")
def home():
    return render_template("index.html", player=current_player())


@app.get("/greet/<name>")
def greet(name):
    return f"Hello, {escape(name)}!"


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)