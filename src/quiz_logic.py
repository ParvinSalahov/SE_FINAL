def grade(correct_by_question, submitted):
    """Return the number correct, total questions, and per-question results."""
    details = {
        question_id: submitted.get(question_id) == correct_answer
        for question_id, correct_answer in correct_by_question.items()
    }
    score = sum(details.values())
    return score, len(correct_by_question), details


def percentage(score, total):
    """Return the rounded integer percentage, or zero when there are no questions."""
    if total == 0:
        return 0
    return round(score * 100 / total)
