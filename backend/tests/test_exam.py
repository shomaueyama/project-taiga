from taiga.api_schemas import OralAnswer, OralReviewRequest


def test_oral_review_schema_requires_answers() -> None:
    request = OralReviewRequest(
        passed=True,
        answers=[OralAnswer(question="q", assessment="pass")],
    )
    assert request.passed is True
    assert request.answers[0].question == "q"
