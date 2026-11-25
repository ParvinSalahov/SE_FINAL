import os
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")),
)

from app import app


def test_valid_entry_redirects_to_topics(client):
    response = client.post("/enter", data={"nickname": "Student"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/topics")


def test_invalid_nicknames_are_rejected(client):
    for nickname in ("A", "a" * 21, "two words", "bad-name"):
        response = client.post("/enter", data={"nickname": nickname})
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")


def test_same_nickname_reuses_player(client):
    client.post("/enter", data={"nickname": "Student"})
    client.post("/leave")
    client.post("/enter", data={"nickname": "Student"})

    with app.app_context():
        from db import get_db

        count = get_db().execute(
            "SELECT COUNT(*) FROM player WHERE nickname = ?",
            ("Student",),
        ).fetchone()[0]

    assert count == 1


def test_leave_clears_session(client):
    client.post("/enter", data={"nickname": "Student"})
    client.post("/leave")

    with client.session_transaction() as session:
        assert "player_id" not in session


def test_topics_requires_nickname(client):
    response = client.get("/topics")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")