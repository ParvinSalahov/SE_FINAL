import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from quiz_logic import grade, percentage


def test_grade_all_correct():
    assert grade({1: 10, 2: 20}, {1: 10, 2: 20}) == (
        2,
        2,
        {1: True, 2: True},
    )


def test_grade_partly_correct():
    assert grade({1: 10, 2: 20}, {1: 10, 2: 99}) == (
        1,
        2,
        {1: True, 2: False},
    )


def test_grade_none_correct():
    assert grade({1: 10, 2: 20}, {1: 99, 2: 99}) == (
        0,
        2,
        {1: False, 2: False},
    )


def test_grade_unanswered_is_wrong():
    assert grade({1: 10}, {}) == (0, 1, {1: False})


def test_percentage():
    assert percentage(3, 4) == 75
    assert percentage(0, 0) == 0
