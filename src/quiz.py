import re

from flask import Blueprint, abort, redirect, render_template, request, url_for

from auth import current_player, login_required
from db import get_db
from quiz_logic import grade, percentage


quiz_bp = Blueprint("quiz", __name__)


@quiz_bp.get("/topics")
@login_required
def topics():
    conn = get_db()
    topic_rows = conn.execute(
        """
        SELECT topic.id, topic.slug, topic.title, topic.description,
               COUNT(question.id) AS n_questions
        FROM topic
        LEFT JOIN question ON question.topic_id = topic.id
        GROUP BY topic.id
        ORDER BY topic.title
        """
    ).fetchall()
    return render_template(
        "topics.html",
        topics=topic_rows,
        player=current_player(),
    )


@quiz_bp.get("/quiz/<slug>")
@login_required
def take(slug):
    conn = get_db()
    topic = conn.execute(
        "SELECT id, slug, title, description FROM topic WHERE slug = ?",
        (slug,),
    ).fetchone()
    if topic is None:
        abort(404)

    questions = conn.execute(
        """
        SELECT id, topic_id, text, explanation
        FROM question
        WHERE topic_id = ?
        ORDER BY id
        """,
        (topic["id"],),
    ).fetchall()
    items = []
    for question in questions:
        choices = conn.execute(
            "SELECT id, text FROM choice WHERE question_id = ? ORDER BY id",
            (question["id"],),
        ).fetchall()
        items.append({"q": question, "choices": choices})

    return render_template(
        "quiz.html",
        topic=topic,
        items=items,
    )


@quiz_bp.post("/quiz/<slug>")
@login_required
def submit(slug):
    conn = get_db()
    topic = conn.execute(
        "SELECT id FROM topic WHERE slug = ?",
        (slug,),
    ).fetchone()
    if topic is None:
        abort(404)

    questions = conn.execute(
        "SELECT id FROM question WHERE topic_id = ? ORDER BY id",
        (topic["id"],),
    ).fetchall()
    question_ids = [question["id"] for question in questions]

    correct_by_question = {}
    choices_by_question = {question_id: set() for question_id in question_ids}
    if question_ids:
        choice_rows = conn.execute(
            """
            SELECT choice.id, choice.question_id, choice.is_correct
            FROM choice
            JOIN question ON question.id = choice.question_id
            WHERE question.topic_id = ?
            """,
            (topic["id"],),
        ).fetchall()
        for choice in choice_rows:
            choices_by_question[choice["question_id"]].add(choice["id"])
            if choice["is_correct"]:
                correct_by_question[choice["question_id"]] = choice["id"]

    submitted = {}
    for question_id in question_ids:
        raw_choice_id = request.form.get(f"q_{question_id}", "")
        if re.fullmatch(r"[0-9]+", raw_choice_id):
            try:
                choice_id = int(raw_choice_id)
            except ValueError:
                choice_id = None
            submitted[question_id] = (
                choice_id
                if choice_id in choices_by_question[question_id]
                else None
            )
        else:
            submitted[question_id] = None

    score, total, details = grade(correct_by_question, submitted)
    cursor = conn.execute(
        """
        INSERT INTO attempt (player_id, topic_id, score, total, taken_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (current_player()["id"], topic["id"], score, total),
    )
    attempt_id = cursor.lastrowid
    for question_id in question_ids:
        conn.execute(
            """
            INSERT INTO attempt_answer
                (attempt_id, question_id, choice_id, is_correct)
            VALUES (?, ?, ?, ?)
            """,
            (
                attempt_id,
                question_id,
                submitted[question_id],
                int(details.get(question_id, False)),
            ),
        )
    conn.commit()
    return redirect(url_for("quiz.result", attempt_id=attempt_id))


@quiz_bp.get("/result/<int:attempt_id>")
@login_required
def result(attempt_id):
    conn = get_db()
    attempt = conn.execute(
        """
        SELECT attempt.id, attempt.player_id, attempt.topic_id,
               attempt.score, attempt.total, attempt.taken_at,
               topic.title AS topic_title, topic.slug AS topic_slug
        FROM attempt
        JOIN topic ON topic.id = attempt.topic_id
        WHERE attempt.id = ? AND attempt.player_id = ?
        """,
        (attempt_id, current_player()["id"]),
    ).fetchone()
    if attempt is None:
        abort(404)

    review = conn.execute(
        """
        SELECT question.text AS question,
               question.explanation,
               attempt_answer.is_correct,
               your_choice.text AS your_answer,
               right_choice.text AS right_answer
        FROM attempt_answer
        JOIN question ON question.id = attempt_answer.question_id
        LEFT JOIN choice AS your_choice
               ON your_choice.id = attempt_answer.choice_id
        JOIN choice AS right_choice
             ON right_choice.question_id = question.id
            AND right_choice.is_correct = 1
        WHERE attempt_answer.attempt_id = ?
        ORDER BY question.id
        """,
        (attempt_id,),
    ).fetchall()
    return render_template(
        "result.html",
        attempt=attempt,
        review=review,
        pct=percentage(attempt["score"], attempt["total"]),
    )
