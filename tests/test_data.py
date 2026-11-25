import glob
import json
import os


DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../src/data")
)


def test_every_quiz_json_is_valid():
    files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    assert files, "Expected at least one quiz JSON file"

    slugs = set()

    for path in files:
        with open(path, encoding="utf-8") as data_file:
            quiz = json.load(data_file)

        assert quiz["slug"]
        assert quiz["slug"] not in slugs
        slugs.add(quiz["slug"])
        assert quiz["title"]
        assert quiz["questions"]

        for question in quiz["questions"]:
            assert question["text"]
            assert len(question["choices"]) == 4
            assert all(choice.strip() for choice in question["choices"])
            assert type(question["answer"]) is int
            assert 0 <= question["answer"] <= 3
            assert question["explanation"]