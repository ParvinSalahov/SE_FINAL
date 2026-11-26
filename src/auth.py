import re
from functools import wraps

from flask import Blueprint, flash, redirect, session, url_for

from db import get_db


auth_bp = Blueprint("auth", __name__)

NICKNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{2,20}$")


def current_player():
    player_id = session.get("player_id")
    if player_id is None:
        return None

    return get_db().execute(
        "SELECT id, nickname, created_at FROM player WHERE id = ?",
        (player_id,),
    ).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if current_player() is None:
            flash("Please enter a nickname first.", "error")
            return redirect(url_for("home"))
        return view(*args, **kwargs)

    return wrapped_view


@auth_bp.post("/enter")
def enter():
    nickname = (request_value("nickname") or "").strip()

    if not NICKNAME_PATTERN.fullmatch(nickname):
        flash("Use 2–20 letters, digits, or underscores.", "error")
        return redirect(url_for("home"))

    conn = get_db()
    player = conn.execute(
        "SELECT id FROM player WHERE nickname = ?",
        (nickname,),
    ).fetchone()

    if player is None:
        cursor = conn.execute(
            "INSERT INTO player (nickname) VALUES (?)",
            (nickname,),
        )
        conn.commit()
        player_id = cursor.lastrowid
    else:
        player_id = player["id"]

    session["player_id"] = player_id
    return redirect(url_for("quiz.topics"))


@auth_bp.post("/leave")
def leave():
    session.clear()
    return redirect(url_for("home"))


def request_value(name):
    from flask import request

    return request.form.get(name, "")