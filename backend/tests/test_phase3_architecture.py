from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from alembic import command
from taiga.config import get_settings
from taiga.curriculum_seed import seed
from taiga.errors import InvalidTransitionError
from taiga.infrastructure.database import SessionLocal
from taiga.main import app
from taiga.state_transitions import (
    oral_review_transition,
    review_submission_transition,
    runner_result_transition,
    start_exam_transition,
    submit_exam_transition,
)

CURRICULUM_DIR = Path(__file__).parents[3] / "design/taiga-42-v4.0-implementation-pack/curriculum"
OPENAPI_CONTRACT = (
    Path(__file__).parents[3]
    / "design/taiga-42-v4.0-implementation-pack/contracts/openapi/openapi.json"
)
IMPLEMENTED_CONTRACT_PATHS = {
    "/me",
    "/dashboard",
    "/assignments",
    "/assignments/{assignmentId}",
    "/uploads/presign",
    "/uploads/{uploadId}/complete",
    "/uploads/{uploadId}",
    "/assignments/{assignmentId}/submissions",
    "/submissions/{submissionId}",
    "/submissions/{submissionId}/run",
    "/submissions/{submissionId}/reviews",
    "/reviews/queue",
    "/exams",
    "/exams/{examId}/attempts",
    "/exam-attempts/{attemptId}",
    "/exam-attempts/{attemptId}/start",
    "/exam-attempts/{attemptId}/submit",
    "/exam-attempts/{attemptId}/oral-review",
    "/progress",
    "/notifications",
    "/notification-preferences",
    "/admin/users",
    "/admin/users/invitations",
    "/admin/users/{userId}/suspend",
    "/admin/users/{userId}/restore",
    "/admin/curriculum/versions",
    "/admin/feature-flags",
    "/admin/feature-flags/{key}",
    "/admin/analytics/learning",
    "/health/live",
    "/health/ready",
}


def migrate() -> None:
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    command.upgrade(config, "head")


@pytest.fixture(scope="module")
def seeded() -> None:
    migrate()
    if not (CURRICULUM_DIR / "weeks.json").exists():
        pytest.skip("Design curriculum is not present in this checkout")
    seed()


def headers(email: str = "taiga@example.local") -> dict[str, str]:
    return {"Authorization": f"Bearer local:{email}", "Idempotency-Key": str(uuid4())}


def scalar(query: str, params: dict[str, object] | None = None) -> Any:
    with SessionLocal() as session:
        return session.execute(text(query), params or {}).scalar_one()


def execute(query: str, params: dict[str, object] | None = None) -> None:
    with SessionLocal.begin() as session:
        session.execute(text(query), params or {})


def delete_exam_attempt(attempt_id: str) -> None:
    execute("DELETE FROM exam_attempts WHERE id = :id", {"id": UUID(attempt_id)})


def create_submission(client: TestClient) -> dict[str, Any]:
    assignment_id = client.get("/api/v1/assignments", headers=headers()).json()["items"][0]["id"]
    sha256 = "a" * 64
    upload = client.post(
        "/api/v1/uploads/presign",
        json={
            "originalName": f"phase3-{uuid4()}.md",
            "mediaType": "text/markdown",
            "sizeBytes": 10,
            "sha256": sha256,
        },
        headers=headers(),
    )
    upload_id = upload.json()["id"]
    client.post(
        f"/api/v1/uploads/{upload_id}/complete",
        json={"sizeBytes": 10, "sha256": sha256},
        headers=headers(),
    )
    submission = client.post(
        f"/api/v1/assignments/{assignment_id}/submissions",
        json={
            "sourceType": "file_upload",
            "repositoryUrl": None,
            "commitHash": None,
            "uploadIds": [upload_id],
        },
        headers=headers(),
    )
    assert submission.status_code == 201
    return dict(submission.json())


def test_state_transition_policy_accepts_valid_paths_and_rejects_invalid_review() -> None:
    assert review_submission_transition("manual_review_pending", "approved") == (
        "approved",
        "completed",
    )
    assert review_submission_transition("manual_review_pending", "needs_revision") == (
        "needs_revision",
        "in_progress",
    )
    with pytest.raises(InvalidTransitionError) as error:
        review_submission_transition("approved", "approved")
    assert error.value.code == "submission_not_reviewable"

    assert runner_result_transition(False) == ("succeeded", "manual_review_pending")
    assert runner_result_transition(True) == ("security_rejected", "needs_revision")
    assert start_exam_transition("ready") == "in_progress"
    assert start_exam_transition("in_progress") == "in_progress"
    assert submit_exam_transition("in_progress", late=False) == "oral_pending"
    assert submit_exam_transition("in_progress", late=True) == "expired"
    assert oral_review_transition("oral_pending", passed=True) == "passed"
    with pytest.raises(InvalidTransitionError):
        oral_review_transition("passed", passed=True)


def test_application_errors_keep_status_and_add_machine_code(seeded: None) -> None:
    client = TestClient(app)
    runner_disabled = client.post(
        f"/api/v1/submissions/{create_submission(client)['id']}/run",
        json={"reason": "phase3"},
        headers=headers(),
    )
    assert runner_disabled.status_code == 403
    assert runner_disabled.json()["detail"] == "Runner is disabled"
    assert runner_disabled.json()["code"] == "runner_disabled"

    unknown_upload = client.get(f"/api/v1/uploads/{uuid4()}", headers=headers())
    assert unknown_upload.status_code == 404
    assert unknown_upload.json()["code"] == "upload_not_found"


def test_oral_review_invalid_transition_rolls_back_without_rank_history(
    seeded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EXAM_ENABLED", "true")
    get_settings.cache_clear()
    client = TestClient(app)
    exam_id = scalar(
        """
        SELECT e.id
        FROM exams e
        JOIN exam_variants v ON v.exam_id = e.id
        LEFT JOIN exam_attempts a
          ON a.exam_id = e.id
         AND a.exam_variant_id = v.id
         AND a.learner_id = (SELECT id FROM users WHERE cognito_sub = 'taiga@example.local')
        WHERE a.id IS NULL
        ORDER BY e.stable_code
        LIMIT 1
        """
    )
    attempt = client.post(f"/api/v1/exams/{exam_id}/attempts", json={}, headers=headers())
    assert attempt.status_code == 201
    attempt_id = attempt.json()["id"]
    try:
        before = scalar("SELECT count(*) FROM rank_history")
        invalid = client.post(
            f"/api/v1/exam-attempts/{attempt_id}/oral-review",
            json={"passed": True, "answers": [{"question": "q", "assessment": "pass"}]},
            headers=headers("admin@example.local"),
        )
        assert invalid.status_code == 409
        assert invalid.json()["code"] == "exam_not_oral_pending"
        assert scalar("SELECT count(*) FROM rank_history") == before
        assert scalar(
            "SELECT status::text FROM exam_attempts WHERE id = :id",
            {"id": UUID(attempt_id)},
        ) == "ready"
    finally:
        delete_exam_attempt(attempt_id)
        get_settings.cache_clear()


def test_implemented_api_paths_remain_within_design_contract() -> None:
    if not OPENAPI_CONTRACT.exists():
        pytest.skip("Design OpenAPI contract is not present in this checkout")
    contract = OPENAPI_CONTRACT.read_text(encoding="utf-8")
    missing = [path for path in IMPLEMENTED_CONTRACT_PATHS if f'"{path}"' not in contract]
    assert missing == []

    generated_paths = {
        path.removeprefix("/api/v1")
        for path in app.openapi()["paths"]
        if path.startswith("/api/v1")
    }
    assert IMPLEMENTED_CONTRACT_PATHS <= generated_paths
