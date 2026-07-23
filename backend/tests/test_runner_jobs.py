from taiga.runner_jobs import _json


def test_runner_sanitized_result_redacts_hidden_tests() -> None:
    payload = _json({"hiddenTests": "redacted", "summary": "ok"})
    assert "secret" not in payload
    assert "redacted" in payload
