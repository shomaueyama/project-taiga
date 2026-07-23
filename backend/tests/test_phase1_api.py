from collections.abc import Generator
from pathlib import Path
from typing import cast
from uuid import UUID

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from alembic import command
from taiga.config import get_settings
from taiga.curriculum_seed import seed
from taiga.infrastructure.database import SessionLocal
from taiga.main import app
from taiga.runner_jobs import process_next_runner_job

CURRICULUM_DIR = Path(__file__).parents[3] / "design/taiga-42-v4.0-implementation-pack/curriculum"


def migrate() -> None:
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    command.upgrade(config, "head")


@pytest.fixture(scope="module")
def seeded_local_mvp() -> Generator[None]:
    migrate()
    if not (CURRICULUM_DIR / "weeks.json").exists():
        pytest.skip("Design curriculum is not present in this checkout")
    seed()
    seed()
    yield


def headers(email: str = "taiga@example.local") -> dict[str, str]:
    return {"Authorization": f"Bearer local:{email}", "Idempotency-Key": f"phase1-{email}"}


def scalar_uuid(query: str, params: dict[str, object] | None = None) -> UUID:
    with SessionLocal() as session:
        return cast(UUID, session.execute(text(query), params or {}).scalar_one())


def create_submission(client: TestClient) -> str:
    assignment_response = client.get("/api/v1/assignments", headers=headers())
    assert assignment_response.status_code == 200
    assignment_id = assignment_response.json()["items"][0]["id"]
    sha256 = "a" * 64
    upload_response = client.post(
        "/api/v1/uploads/presign",
        json={
            "originalName": "phase1-answer.md",
            "mediaType": "text/markdown",
            "sizeBytes": 10,
            "sha256": sha256,
        },
        headers=headers(),
    )
    assert upload_response.status_code == 201
    upload_id = upload_response.json()["id"]
    complete_response = client.post(
        f"/api/v1/uploads/{upload_id}/complete",
        json={"sizeBytes": 10, "sha256": sha256},
        headers=headers(),
    )
    assert complete_response.status_code == 202
    submission_response = client.post(
        f"/api/v1/assignments/{assignment_id}/submissions",
        json={
            "sourceType": "file_upload",
            "repositoryUrl": None,
            "commitHash": None,
            "uploadIds": [upload_id],
        },
        headers=headers(),
    )
    assert submission_response.status_code == 201
    return str(submission_response.json()["id"])


def test_anonymous_user_cannot_access_protected_api() -> None:
    response = TestClient(app).get("/api/v1/me")
    assert response.status_code == 401


def test_unknown_local_user_is_rejected(seeded_local_mvp: None) -> None:
    response = TestClient(app).get(
        "/api/v1/me",
        headers={"Authorization": "Bearer local:missing@example.local"},
    )
    assert response.status_code == 401


@pytest.mark.parametrize(
    ("email", "role"),
    [
        ("taiga@example.local", "learner"),
        ("reviewer@example.local", "reviewer"),
        ("admin@example.local", "admin"),
    ],
)
def test_known_local_users_authenticate(seeded_local_mvp: None, email: str, role: str) -> None:
    response = TestClient(app).get("/api/v1/me", headers=headers(email))
    assert response.status_code == 200
    assert response.json()["role"] == role


def test_learner_cannot_access_admin_users(seeded_local_mvp: None) -> None:
    response = TestClient(app).get("/api/v1/admin/users", headers=headers("taiga@example.local"))
    assert response.status_code == 403


def test_admin_can_access_user_list(seeded_local_mvp: None) -> None:
    response = TestClient(app).get("/api/v1/admin/users", headers=headers("admin@example.local"))
    assert response.status_code == 200
    emails = {item["displayName"] for item in response.json()["items"]}
    assert "上山 捷馬" in emails
    assert "上山 虎雅" in emails


def test_runner_api_is_safe_when_disabled(seeded_local_mvp: None) -> None:
    submission_id = scalar_uuid(
        """
        SELECT s.id
        FROM submissions s
        JOIN users u ON u.id = s.learner_id
        WHERE u.cognito_sub = 'taiga@example.local'
        ORDER BY s.created_at
        LIMIT 1
        """
    )
    response = TestClient(app).post(
        f"/api/v1/submissions/{submission_id}/run",
        json={"reason": "phase1"},
        headers=headers("taiga@example.local"),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Runner is disabled"


def test_exam_mutation_is_safe_when_disabled(seeded_local_mvp: None) -> None:
    exam_id = scalar_uuid("SELECT id FROM exams ORDER BY stable_code LIMIT 1")
    response = TestClient(app).post(
        f"/api/v1/exams/{exam_id}/attempts",
        json={},
        headers=headers("taiga@example.local"),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Exam is disabled"


def test_exam_enabled_flow_is_server_authoritative(
    seeded_local_mvp: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EXAM_ENABLED", "true")
    get_settings.cache_clear()
    client = TestClient(app)
    exam_id = scalar_uuid(
        """
        SELECT e.id
        FROM exams e
        JOIN exam_variants v ON v.exam_id = e.id
        LEFT JOIN exam_attempts a
          ON a.exam_id = e.id
         AND a.exam_variant_id = v.id
         AND a.learner_id = (
           SELECT id FROM users WHERE cognito_sub = 'taiga@example.local'
         )
        WHERE a.id IS NULL
        ORDER BY e.stable_code
        LIMIT 1
        """
    )
    attempt_response = client.post(
        f"/api/v1/exams/{exam_id}/attempts",
        json={},
        headers=headers(),
    )
    assert attempt_response.status_code == 201
    attempt_id = attempt_response.json()["id"]
    start_response = client.post(
        f"/api/v1/exam-attempts/{attempt_id}/start",
        json={"acknowledgeRules": True},
        headers=headers(),
    )
    assert start_response.status_code == 200
    assert start_response.json()["attempt"]["status"] == "in_progress"
    submit_response = client.post(
        f"/api/v1/exam-attempts/{attempt_id}/submit",
        json={"answers": {"q1": "phase1"}, "submissionId": None},
        headers=headers(),
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["attempt"]["status"] == "oral_pending"
    oral_response = client.post(
        f"/api/v1/exam-attempts/{attempt_id}/oral-review",
        json={"passed": True, "answers": [{"question": "q1", "assessment": "pass"}]},
        headers=headers("admin@example.local"),
    )
    assert oral_response.status_code == 200
    assert oral_response.json()["attempt"]["status"] == "passed"
    get_settings.cache_clear()


def test_runner_enabled_flow_is_safely_rejected(
    seeded_local_mvp: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RUNNER_ENABLED", "true")
    get_settings.cache_clear()
    client = TestClient(app)
    submission_id = create_submission(client)
    response = client.post(
        f"/api/v1/submissions/{submission_id}/run",
        json={"reason": "phase1"},
        headers=headers(),
    )
    assert response.status_code == 202
    job_id = response.json()["id"]
    processed = False
    for _ in range(20):
        with SessionLocal.begin() as session:
            processed = process_next_runner_job(session) or processed
            status_row = (
                session.execute(
                    text(
                        """
                        SELECT status::text, sanitized_result_json
                        FROM runner_jobs
                        WHERE id = :id
                        """
                    ),
                    {"id": job_id},
                )
                .mappings()
                .one()
            )
            if status_row["status"] == "security_rejected":
                assert status_row["sanitized_result_json"]["hiddenTests"] == "redacted"
                break
    assert processed is True
    assert status_row["status"] == "security_rejected"
    get_settings.cache_clear()


def test_review_cannot_be_applied_twice(seeded_local_mvp: None) -> None:
    submission_id = scalar_uuid(
        """
        SELECT id
        FROM submissions
        WHERE status = 'approved'
        ORDER BY created_at
        LIMIT 1
        """
    )
    response = TestClient(app).post(
        f"/api/v1/submissions/{submission_id}/reviews",
        json={
            "result": "approved",
            "rubric": {"correctness": "checked"},
            "comment": "duplicate review should fail",
        },
        headers=headers("admin@example.local"),
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Submission is not awaiting review"
