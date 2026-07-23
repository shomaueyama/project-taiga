from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import text

from alembic import command
from taiga.config import get_settings
from taiga.curriculum_seed import seed
from taiga.infrastructure.database import SessionLocal
from taiga.main import app
from taiga.runner_jobs import process_next_runner_job
from taiga.security import rate_limiter

CURRICULUM_DIR = Path(__file__).parents[3] / "design/taiga-42-v4.0-implementation-pack/curriculum"
PHASE4_OTHER_EMAIL = "phase4-other@example.local"


def migrate() -> None:
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    command.upgrade(config, "head")


def cleanup_phase4_other_user() -> None:
    with SessionLocal.begin() as session:
        session.execute(
            text(
                """
                WITH phase4_user AS (
                    SELECT id FROM users WHERE cognito_sub = :email
                ), phase4_assignments AS (
                    SELECT id FROM task_assignments
                    WHERE learner_id IN (SELECT id FROM phase4_user)
                ), phase4_submissions AS (
                    SELECT id FROM submissions
                    WHERE assignment_id IN (SELECT id FROM phase4_assignments)
                       OR learner_id IN (SELECT id FROM phase4_user)
                ), phase4_runner_jobs AS (
                    SELECT id FROM runner_jobs
                    WHERE submission_id IN (SELECT id FROM phase4_submissions)
                )
                DELETE FROM outbox_events
                WHERE aggregate_id IN (SELECT id FROM phase4_runner_jobs)
                """
            ),
            {"email": PHASE4_OTHER_EMAIL},
        )
        session.execute(
            text(
                """
                DELETE FROM reviews
                WHERE submission_id IN (
                    SELECT s.id
                    FROM submissions s
                    JOIN users u ON u.id = s.learner_id
                    WHERE u.cognito_sub = :email
                )
                """
            ),
            {"email": PHASE4_OTHER_EMAIL},
        )
        session.execute(
            text(
                """
                DELETE FROM runner_jobs
                WHERE submission_id IN (
                    SELECT s.id
                    FROM submissions s
                    JOIN users u ON u.id = s.learner_id
                    WHERE u.cognito_sub = :email
                )
                """
            ),
            {"email": PHASE4_OTHER_EMAIL},
        )
        session.execute(
            text(
                """
                DELETE FROM submission_artifacts
                WHERE submission_id IN (
                    SELECT s.id
                    FROM submissions s
                    JOIN users u ON u.id = s.learner_id
                    WHERE u.cognito_sub = :email
                )
                """
            ),
            {"email": PHASE4_OTHER_EMAIL},
        )
        session.execute(
            text(
                """
                DELETE FROM submissions
                WHERE learner_id IN (SELECT id FROM users WHERE cognito_sub = :email)
                """
            ),
            {"email": PHASE4_OTHER_EMAIL},
        )
        session.execute(
            text(
                """
                DELETE FROM upload_sessions
                WHERE owner_id IN (SELECT id FROM users WHERE cognito_sub = :email)
                """
            ),
            {"email": PHASE4_OTHER_EMAIL},
        )
        session.execute(
            text(
                """
                DELETE FROM task_assignments
                WHERE learner_id IN (SELECT id FROM users WHERE cognito_sub = :email)
                """
            ),
            {"email": PHASE4_OTHER_EMAIL},
        )
        session.execute(
            text("DELETE FROM users WHERE cognito_sub = :email"),
            {"email": PHASE4_OTHER_EMAIL},
        )


@pytest.fixture(scope="module")
def seeded() -> Iterator[None]:
    migrate()
    cleanup_phase4_other_user()
    if not (CURRICULUM_DIR / "weeks.json").exists():
        pytest.skip("Design curriculum is not present in this checkout")
    seed()
    yield
    cleanup_phase4_other_user()


@pytest.fixture(autouse=True)
def clear_security_state(monkeypatch: pytest.MonkeyPatch) -> None:
    rate_limiter.clear()
    get_settings.cache_clear()
    monkeypatch.delenv("RUNNER_ENABLED", raising=False)
    monkeypatch.delenv("EXAM_ENABLED", raising=False)
    monkeypatch.delenv("RATE_LIMIT_MAX_REQUESTS", raising=False)
    monkeypatch.delenv("RATE_LIMIT_WINDOW_SECONDS", raising=False)
    monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)


def headers(email: str = "taiga@example.local") -> dict[str, str]:
    return {"Authorization": f"Bearer local:{email}", "Idempotency-Key": str(uuid4())}


def scalar(query: str, params: dict[str, object] | None = None) -> Any:
    with SessionLocal() as session:
        return session.execute(text(query), params or {}).scalar_one()


def execute(query: str, params: dict[str, object] | None = None) -> None:
    with SessionLocal.begin() as session:
        session.execute(text(query), params or {})


def create_submission(client: TestClient, email: str = "taiga@example.local") -> dict[str, Any]:
    assignment_id = client.get("/api/v1/assignments", headers=headers(email)).json()["items"][0][
        "id"
    ]
    sha256 = "a" * 64
    upload = client.post(
        "/api/v1/uploads/presign",
        json={
            "originalName": f"phase4-{uuid4()}.md",
            "mediaType": "text/markdown",
            "sizeBytes": 10,
            "sha256": sha256,
        },
        headers=headers(email),
    )
    assert upload.status_code == 201
    upload_id = upload.json()["id"]
    complete = client.post(
        f"/api/v1/uploads/{upload_id}/complete",
        json={"sizeBytes": 10, "sha256": sha256},
        headers=headers(email),
    )
    assert complete.status_code == 202
    submission = client.post(
        f"/api/v1/assignments/{assignment_id}/submissions",
        json={
            "sourceType": "file_upload",
            "repositoryUrl": None,
            "commitHash": None,
            "uploadIds": [upload_id],
        },
        headers=headers(email),
    )
    assert submission.status_code == 201
    return cast(dict[str, Any], submission.json())


def create_second_learner_assignment() -> str:
    learner_id = uuid4()
    assignment_id = uuid4()
    task_template_id = scalar("SELECT id FROM task_templates ORDER BY stable_code LIMIT 1")
    execute(
        """
        INSERT INTO users (id, cognito_sub, display_name, role, status)
        VALUES (:user_id, :email, 'Phase 4 Other', 'learner', 'active')
        ON CONFLICT (cognito_sub) DO UPDATE SET status = 'active'
        """,
        {"user_id": learner_id, "email": PHASE4_OTHER_EMAIL},
    )
    actual_learner_id = scalar(
        "SELECT id FROM users WHERE cognito_sub = :email",
        {"email": PHASE4_OTHER_EMAIL},
    )
    execute(
        """
        INSERT INTO task_assignments (id, task_template_id, learner_id, scheduled_date, status)
        VALUES (:id, :task_template_id, :learner_id, current_date, 'available')
        ON CONFLICT (task_template_id, learner_id) DO UPDATE SET status = 'available'
        """,
        {
            "id": assignment_id,
            "task_template_id": task_template_id,
            "learner_id": actual_learner_id,
        },
    )
    return str(
        scalar(
            """
            SELECT id FROM task_assignments
            WHERE task_template_id = :task_template_id AND learner_id = :learner_id
            """,
            {"task_template_id": task_template_id, "learner_id": actual_learner_id},
        )
    )


def test_security_headers_and_untrusted_cors_origin(seeded: None) -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]

    preflight = client.options(
        "/api/v1/me",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight.status_code in {400, 405}
    assert "access-control-allow-origin" not in preflight.headers


def test_protected_mutations_reject_missing_authentication(seeded: None) -> None:
    client = TestClient(app)
    assignment_id = client.get("/api/v1/assignments", headers=headers()).json()["items"][0]["id"]
    mutation_requests = [
        client.post("/api/v1/uploads/presign", json={}),
        client.post(f"/api/v1/uploads/{uuid4()}/complete", json={}),
        client.post(f"/api/v1/assignments/{assignment_id}/submissions", json={}),
        client.post(f"/api/v1/submissions/{uuid4()}/reviews", json={}),
        client.post(f"/api/v1/submissions/{uuid4()}/run", json={}),
        client.post(f"/api/v1/exams/{uuid4()}/attempts", json={}),
        client.post(f"/api/v1/exam-attempts/{uuid4()}/start", json={}),
        client.post(f"/api/v1/exam-attempts/{uuid4()}/submit", json={}),
        client.post(f"/api/v1/exam-attempts/{uuid4()}/oral-review", json={}),
        client.post("/api/v1/admin/users/invitations", json={}),
    ]
    assert {response.status_code for response in mutation_requests} == {401}


def test_learner_idor_and_role_escalation_are_denied(seeded: None) -> None:
    client = TestClient(app)
    other_assignment_id = create_second_learner_assignment()
    own_submission = create_submission(client)
    other_submission = create_submission(client, email="phase4-other@example.local")

    other_assignment = client.get(f"/api/v1/assignments/{other_assignment_id}", headers=headers())
    assert other_assignment.status_code == 404
    other_submission_detail = client.get(
        f"/api/v1/submissions/{other_submission['id']}",
        headers=headers(),
    )
    assert other_submission_detail.status_code == 404
    learner_review = client.post(
        f"/api/v1/submissions/{own_submission['id']}/reviews",
        json={"result": "approved", "rubric": {}, "comment": "no"},
        headers=headers(),
    )
    assert learner_review.status_code == 403
    reviewer_assignment = client.get(
        f"/api/v1/assignments/{other_assignment_id}",
        headers=headers("reviewer@example.local"),
    )
    assert reviewer_assignment.status_code == 404
    reviewer_admin_mutation = client.post(
        "/api/v1/admin/users/invitations",
        json={"email": "phase4-nope@example.local", "displayName": "Nope", "role": "learner"},
        headers=headers("reviewer@example.local"),
    )
    assert reviewer_admin_mutation.status_code == 403


def test_input_validation_rejects_extra_fields_malformed_json_and_rate_limits(
    seeded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = TestClient(app)
    extra = client.post(
        "/api/v1/uploads/presign",
        json={
            "originalName": "answer.md",
            "mediaType": "text/markdown",
            "sizeBytes": 10,
            "sha256": "a" * 64,
            "admin": True,
        },
        headers=headers(),
    )
    assert extra.status_code == 422
    malformed = client.post(
        "/api/v1/uploads/presign",
        content="{not-json",
        headers={**headers(), "Content-Type": "application/json"},
    )
    assert malformed.status_code == 422
    assert "traceback" not in malformed.text.lower()

    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    get_settings.cache_clear()
    rate_limiter.clear()
    assert client.get("/api/v1/health/live").status_code == 200
    assert client.get("/api/v1/health/live").status_code == 200
    limited = client.get("/api/v1/health/live")
    assert limited.status_code == 429
    assert limited.json()["code"] == "rate_limited"


def test_upload_security_rejects_unsafe_inputs_and_uses_generated_storage_key(
    seeded: None,
) -> None:
    client = TestClient(app)
    for payload, code in [
        (
            {
                "originalName": "/tmp/secret.md",  # noqa: S108 - intentional attack input
                "mediaType": "text/markdown",
                "sizeBytes": 10,
                "sha256": "a" * 64,
            },
            "path_traversal",
        ),
        (
            {
                "originalName": "answer.md",
                "mediaType": "text/markdown",
                "sizeBytes": 0,
                "sha256": "a" * 64,
            },
            "empty_file",
        ),
        (
            {
                "originalName": "answer.md",
                "mediaType": "text/html",
                "sizeBytes": 10,
                "sha256": "a" * 64,
            },
            "media_type_mismatch",
        ),
        (
            {
                "originalName": "answer.jpg.exe",
                "mediaType": "application/octet-stream",
                "sizeBytes": 10,
                "sha256": "a" * 64,
            },
            "extension_not_allowed",
        ),
    ]:
        response = client.post("/api/v1/uploads/presign", json=payload, headers=headers())
        assert response.status_code == 201
        assert response.json()["status"] == "rejected"
        assert response.json()["rejectionCode"] == code

    accepted = client.post(
        "/api/v1/uploads/presign",
        json={
            "originalName": "learner-answer.md",
            "mediaType": "text/markdown",
            "sizeBytes": 10,
            "sha256": "a" * 64,
        },
        headers=headers(),
    )
    assert accepted.status_code == 201
    assert "learner-answer" not in accepted.json()["uploadUrl"]


def test_runner_rejects_unsafe_payloads_and_worker_bounds_poison_messages(
    seeded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RUNNER_ENABLED", "true")
    get_settings.cache_clear()
    client = TestClient(app)
    submission = create_submission(client)
    injection = client.post(
        f"/api/v1/submissions/{submission['id']}/run",
        json={"reason": "manual; cat /etc/passwd"},
        headers=headers(),
    )
    assert injection.status_code == 409
    assert injection.json()["code"] == "unsafe_runner_request"
    assert (
        scalar(
            "SELECT count(*) FROM runner_jobs WHERE submission_id = :id",
            {"id": UUID(submission["id"])},
        )
        == 0
    )

    outbox_id = uuid4()
    execute(
        """
        INSERT INTO outbox_events (
            id, aggregate_type, aggregate_id, event_type, payload_json, attempt_count
        )
        VALUES (
            :id, 'runner_job', :aggregate_id, 'runner_job.queued', '{}'::jsonb, 3
        )
        """,
        {"id": outbox_id, "aggregate_id": uuid4()},
    )
    with SessionLocal.begin() as session:
        assert process_next_runner_job(session) is True
    assert scalar(
        "SELECT published_at IS NULL FROM outbox_events WHERE id = :id",
        {"id": outbox_id},
    )
    assert "poison runner job" in scalar(
        "SELECT last_error FROM outbox_events WHERE id = :id",
        {"id": outbox_id},
    )


def test_security_sensitive_flags_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUNNER_ENABLED", "definitely")
    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        get_settings()
