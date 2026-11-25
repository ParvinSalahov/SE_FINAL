# tests/test_app.py
import sys
import os
# Add the ’src’ directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
# Now we can import the ’app’ object from our source code
from app import app
def test_greet_route():
    """Tests the ’/greet/<name>’ route with a sample name."""
    client = app.test_client()
    # Make a GET request to the dynamic greet route
    response = client.get('/greet/TestUser')
    assert response.status_code == 200
    # Check that the personalized greeting is in the response data
    assert b'Hello, TestUser!' in response.data
def test_index_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"QuizHub" in response.data


def test_greet_route(client):
    response = client.get("/greet/TestUser")
    assert response.status_code == 200
    assert b"Hello, TestUser!" in response.data


def test_greet_escapes_html(client):
    response = client.get("/greet/%3Cscript%3E")
    assert response.status_code == 200
    assert b"<script>" not in response.data