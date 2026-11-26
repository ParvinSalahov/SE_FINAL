import json
import os
import sqlite3
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")),
)

import db
from app import app


def test_schema_and_seed_are_correct(tmp_path):
    app.config.update(
        TESTING=True,
        DATABASE=str(tmp_path / "test.db"),
    )

    with app.app_context():
        conn = db.get_db()

        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert {
            "topic",
            "question",
            "choice",
            "player",
            "attempt",
            "attempt_answer",
        } <= tables

        data_dir = os.path.join(os.path.dirname(__file__), "../src/data")
        n_files = len([f for f in os.listdir(data_dir) if f.endswith(".json")])
        assert conn.execute("SELECT COUNT(*) FROM topic").fetchone()[0] == n_files

        topic_counts = conn.execute(
            """
            SELECT topic.id, COUNT(question.id) AS question_count
            FROM topic
            LEFT JOIN question ON question.topic_id = topic.id
            GROUP BY topic.id
            """
        ).fetchall()
        assert all(row["question_count"] >= 10 for row in topic_counts)

        incorrect_questions = conn.execute(
            """
            SELECT question.id
            FROM question
            JOIN choice ON choice.question_id = question.id
            GROUP BY question.id
            HAVING SUM(choice.is_correct) != 1
            """
        ).fetchall()
        assert incorrect_questions == []

        before = conn.execute(
            "SELECT COUNT(*) FROM question"
        ).fetchone()[0]
        db.seed_if_empty(conn)
        after = conn.execute(
            "SELECT COUNT(*) FROM question"
        ).fetchone()[0]
        assert after == before

def test_existing_database_gets_new_topics(tmp_path):
    db_path = tmp_path / "old.db"

    # An "old" database that was created when only one topic existed.
    conn = sqlite3.connect(db_path)
    db.init_schema(conn)
    conn.execute(
        "INSERT INTO topic (slug, title, description) VALUES (?, ?, ?)",
        ("general_programming", "General Programming", "Old copy"),
    )
    conn.commit()
    conn.close()

    app.config.update(TESTING=True, DATABASE=str(db_path))
    data_dir = os.path.join(os.path.dirname(__file__), "../src/data")
    slugs = set()
    for filename in os.listdir(data_dir):
        if filename.endswith(".json"):
            with open(os.path.join(data_dir, filename), encoding="utf-8") as f:
                slugs.add(json.load(f)["slug"])

    with app.app_context():
        conn = db.get_db()
        rows = conn.execute(
            """
            SELECT topic.slug, COUNT(question.id) AS question_count
            FROM topic
            LEFT JOIN question ON question.topic_id = topic.id
            GROUP BY topic.id
            """
        ).fetchall()

    found = [row["slug"] for row in rows]
    assert sorted(found) == sorted(slugs)
    assert found.count("general_programming") == 1
    assert all(
        row["question_count"] >= 10
        for row in rows
        if row["slug"] != "general_programming"
    )
