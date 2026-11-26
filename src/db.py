import json
import os
import sqlite3

from flask import current_app, g


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        init_schema(conn)
        seed_if_empty(conn)

        g.db = conn

    return g.db


def close_db(error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_schema(conn):
    schema_path = os.path.join(BASE_DIR, "schema.sql")
    with open(schema_path, encoding="utf-8") as schema_file:
        conn.executescript(schema_file.read())
    conn.commit()


def seed_if_empty(conn):
    # Insert every topic from src/data whose slug is not in the database yet,
    # so an existing quiz.db also picks up topics added after it was created.
    existing = {row[0] for row in conn.execute("SELECT slug FROM topic")}

    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.endswith(".json"):
            continue

        path = os.path.join(DATA_DIR, filename)
        with open(path, encoding="utf-8") as data_file:
            data = json.load(data_file)

        if data["slug"] in existing:
            continue

        cursor = conn.execute(
            "INSERT INTO topic (slug, title, description) VALUES (?, ?, ?)",
            (data["slug"], data["title"], data["description"]),
        )
        topic_id = cursor.lastrowid

        for question in data["questions"]:
            question_cursor = conn.execute(
                """
                INSERT INTO question (topic_id, text, explanation)
                VALUES (?, ?, ?)
                """,
                (topic_id, question["text"], question["explanation"]),
            )
            question_id = question_cursor.lastrowid

            for index, choice_text in enumerate(question["choices"]):
                conn.execute(
                    """
                    INSERT INTO choice (question_id, text, is_correct)
                    VALUES (?, ?, ?)
                    """,
                    (
                        question_id,
                        choice_text,
                        int(index == question["answer"]),
                    ),
                )

    conn.commit()


def init_app(app):
    app.teardown_appcontext(close_db)