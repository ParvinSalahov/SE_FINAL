import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")),
)

from app import app


@pytest.fixture
def client(tmp_path):
    old_testing = app.config.get("TESTING")
    old_database = app.config.get("DATABASE")
    old_secret_key = app.config.get("SECRET_KEY")

    app.config.update(
        TESTING=True,
        DATABASE=str(tmp_path / "test.db"),
        SECRET_KEY="test-secret",
    )

    with app.test_client() as test_client:
        yield test_client

    app.config.update(
        TESTING=old_testing,
        DATABASE=old_database,
        SECRET_KEY=old_secret_key,
    )


@pytest.fixture
def player_client(client):
    client.post("/enter", data={"nickname": "tester"})
    return client