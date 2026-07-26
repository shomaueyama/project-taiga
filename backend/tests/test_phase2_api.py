from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

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
from taiga.seed import main as seed_main
from taiga.validation import main as validation_main

CURRICULUM_DIR = Path(__file__).parents[3] / "design/taiga-42-v4.0-implementation-pack/curriculum"


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


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


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


def create_submission(client: TestClient, assignment_id: str | None = None) -> dict[str, Any]:
    if assignment_id is None:
        assignments = client.get("/api/v1/assignments", headers=headers())
        assert assignments.status_code == 200
        assignment_id = assignments.json()["items"][0]["id"]
    sha256 = "a" * 64
    upload = client.post(
        "/api/v1/uploads/presign",
        json={
            "originalName": f"phase2-{uuid4()}.md",
            "mediaType": "text/markdown",
            "sizeBytes": 10,
            "sha256": sha256,
        },
        headers=headers(),
    )
    assert upload.status_code == 201
    upload_id = upload.json()["id"]
    complete = client.post(
        f"/api/v1/uploads/{upload_id}/complete",
        json={"sizeBytes": 10, "sha256": sha256},
        headers=headers(),
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
        headers=headers(),
    )
    assert submission.status_code == 201
    return cast(dict[str, Any], submission.json())


def review(client: TestClient, submission_id: str, result: str = "approved") -> Any:
    return client.post(
        f"/api/v1/submissions/{submission_id}/reviews",
        json={
            "result": result,
            "rubric": {"correctness": "checked"},
            "comment": f"phase2 {result}",
        },
        headers=headers("admin@example.local"),
    )


def test_assignment_dashboard_detail_progress_and_ownership(
    seeded: None,
    client: TestClient,
) -> None:
    assignments = client.get("/api/v1/assignments?limit=3", headers=headers())
    assert assignments.status_code == 200
    assert len(assignments.json()["items"]) == 3
    assignment_id = assignments.json()["items"][0]["id"]
    detail = client.get(f"/api/v1/assignments/{assignment_id}", headers=headers())
    assert detail.status_code == 200
    assert detail.json()["assignment"]["id"] == assignment_id
    dashboard = client.get("/api/v1/dashboard", headers=headers())
    assert dashboard.status_code == 200
    assert "first_submission" in dashboard.json()["capabilityGaps"]
    progress = client.get("/api/v1/progress", headers=headers())
    assert progress.status_code == 200
    assert progress.json()["completedWeeks"] >= 0
    admin_assignments = client.get(
        "/api/v1/assignments?limit=3",
        headers=headers("admin@example.local"),
    )
    assert admin_assignments.status_code == 200
    assert len(admin_assignments.json()["items"]) == 3
    assert admin_assignments.json()["items"][0]["id"] == assignment_id
    admin_detail = client.get(
        f"/api/v1/assignments/{assignment_id}",
        headers=headers("admin@example.local"),
    )
    assert admin_detail.status_code == 200
    admin_dashboard = client.get("/api/v1/dashboard", headers=headers("admin@example.local"))
    assert admin_dashboard.status_code == 200
    assert len(admin_dashboard.json()["today"]) > 0
    reviewer_detail = client.get(
        f"/api/v1/assignments/{assignment_id}",
        headers=headers("reviewer@example.local"),
    )
    assert reviewer_detail.status_code == 404
    missing = client.get(f"/api/v1/assignments/{uuid4()}", headers=headers())
    assert missing.status_code == 404


def test_upload_content_accepts_real_file(seeded: None, client: TestClient) -> None:
    content = b"hello from mobile camera evidence"
    upload = client.post(
        "/api/v1/uploads/presign",
        json={
            "originalName": "evidence.jpg",
            "mediaType": "image/jpeg",
            "sizeBytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        },
        headers=headers(),
    )
    assert upload.status_code == 201
    upload_id = upload.json()["id"]
    completed = client.put(
        f"/api/v1/uploads/{upload_id}/content",
        files={"file": ("evidence.jpg", content, "image/jpeg")},
        headers=headers(),
    )
    assert completed.status_code == 202
    assert completed.json()["status"] == "accepted"


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/assignments",
        "/api/v1/reviews/queue",
        "/api/v1/exams",
        "/api/v1/admin/users",
        "/api/v1/admin/curriculum/versions",
    ],
)
def test_list_limits_are_bounded(seeded: None, client: TestClient, path: str) -> None:
    email = (
        "admin@example.local"
        if "/admin/" in path or "reviews" in path
        else "taiga@example.local"
    )
    assert client.get(f"{path}?limit=0", headers=headers(email)).status_code == 422
    assert client.get(f"{path}?limit=101", headers=headers(email)).status_code == 422
    ok = client.get(f"{path}?limit=100", headers=headers(email))
    assert ok.status_code == 200


def test_admin_operations_and_notifications(seeded: None, client: TestClient) -> None:
    reviewer_users = client.get("/api/v1/admin/users", headers=headers("reviewer@example.local"))
    assert reviewer_users.status_code == 403
    users = client.get("/api/v1/admin/users", headers=headers("admin@example.local"))
    assert users.status_code == 200
    invited_email = f"phase2-{uuid4()}@example.local"
    invited = client.post(
        "/api/v1/admin/users/invitations",
        json={"email": invited_email, "displayName": "Phase 2 User", "role": "learner"},
        headers=headers("admin@example.local"),
    )
    assert invited.status_code == 201
    user_id = invited.json()["id"]
    suspended = client.post(
        f"/api/v1/admin/users/{user_id}/suspend",
        headers=headers("admin@example.local"),
    )
    assert suspended.status_code == 200
    assert suspended.json()["status"] == "suspended"
    restored = client.post(
        f"/api/v1/admin/users/{user_id}/restore",
        headers=headers("admin@example.local"),
    )
    assert restored.status_code == 200
    assert restored.json()["status"] == "active"
    flags = client.get("/api/v1/admin/feature-flags", headers=headers("admin@example.local"))
    assert flags.status_code == 200
    flag_key = flags.json()["items"][0]["key"]
    updated = client.patch(
        f"/api/v1/admin/feature-flags/{flag_key}",
        json={"enabled": True},
        headers=headers("admin@example.local"),
    )
    assert updated.status_code == 200
    assert updated.json()["enabled"] is True
    client.patch(
        f"/api/v1/admin/feature-flags/{flag_key}",
        json={"enabled": False},
        headers=headers("admin@example.local"),
    )
    analytics = client.get(
        "/api/v1/admin/analytics/learning",
        headers=headers("admin@example.local"),
    )
    assert analytics.status_code == 200
    assert analytics.json()["learners"] >= 1
    versions = client.get(
        "/api/v1/admin/curriculum/versions",
        headers=headers("admin@example.local"),
    )
    assert versions.status_code == 200
    assert versions.json()["items"][0]["status"] == "published"


def test_notification_preferences_and_review_notification(
    seeded: None,
    client: TestClient,
) -> None:
    user_id = scalar("SELECT id FROM users WHERE cognito_sub = 'taiga@example.local'")
    execute(
        """
        INSERT INTO notification_preferences (id, user_id, channel, event_type, enabled)
        VALUES (:id, :user_id, 'in_app', 'review_completed', true)
        ON CONFLICT (user_id, channel, event_type) DO UPDATE SET enabled = true
        """,
        {"id": uuid4(), "user_id": user_id},
    )
    prefs = client.get("/api/v1/notification-preferences", headers=headers())
    assert prefs.status_code == 200
    assert prefs.json()["items"][0]["eventType"] == "review_completed"
    submission = create_submission(client)
    assert review(client, submission["id"], "approved").status_code == 201
    notifications = client.get("/api/v1/notifications", headers=headers())
    assert notifications.status_code == 200
    assert notifications.json()["items"][0]["type"] == "review_completed"


def test_upload_and_submission_error_contracts(seeded: None, client: TestClient) -> None:
    bad_upload = client.post(
        "/api/v1/uploads/presign",
        json={
            "originalName": "../secret.txt",
            "mediaType": "text/plain",
            "sizeBytes": 10,
            "sha256": "a" * 64,
        },
        headers=headers(),
    )
    assert bad_upload.status_code == 201
    assert bad_upload.json()["status"] == "rejected"
    mismatch = client.post(
        "/api/v1/uploads/presign",
        json={
            "originalName": f"phase2-{uuid4()}.md",
            "mediaType": "text/markdown",
            "sizeBytes": 10,
            "sha256": "a" * 64,
        },
        headers=headers(),
    )
    upload_id = mismatch.json()["id"]
    completed = client.post(
        f"/api/v1/uploads/{upload_id}/complete",
        json={"sizeBytes": 11, "sha256": "b" * 64},
        headers=headers(),
    )
    assert completed.status_code == 202
    assert completed.json()["status"] == "rejected"
    invalid_submission = client.post(
        f"/api/v1/assignments/{uuid4()}/submissions",
        json={"sourceType": "file_upload", "uploadIds": []},
        headers=headers(),
    )
    assert invalid_submission.status_code == 404
    malformed = client.post(
        "/api/v1/uploads/presign",
        json={"originalName": "x.md"},
        headers=headers(),
    )
    assert malformed.status_code == 422
    assert "traceback" not in malformed.text.lower()
    for payload, code in [
        (
            {
                "originalName": "x" * 121 + ".md",
                "mediaType": "text/markdown",
                "sizeBytes": 10,
                "sha256": "a" * 64,
            },
            "filename_too_long",
        ),
        (
            {
                "originalName": f"phase2-{uuid4()}.md",
                "mediaType": "text/markdown",
                "sizeBytes": 50 * 1024 * 1024 + 1,
                "sha256": "a" * 64,
            },
            "size_limit_exceeded",
        ),
        (
            {
                "originalName": f"phase2-{uuid4()}.md",
                "mediaType": "text/markdown",
                "sizeBytes": 10,
                "sha256": "not-a-sha",
            },
            "invalid_sha256",
        ),
    ]:
        rejected = client.post("/api/v1/uploads/presign", json=payload, headers=headers())
        assert rejected.status_code == 201
        assert rejected.json()["rejectionCode"] == code
    missing_upload = client.get(f"/api/v1/uploads/{uuid4()}", headers=headers())
    assert missing_upload.status_code == 404


def test_review_updates_assignment_and_resubmission_increments_version(
    seeded: None,
    client: TestClient,
) -> None:
    assignment_id = client.get("/api/v1/assignments", headers=headers()).json()["items"][0]["id"]
    first = create_submission(client, assignment_id)
    rejected = review(client, first["id"], "needs_revision")
    assert rejected.status_code == 201
    assignment_status = scalar(
        "SELECT status::text FROM task_assignments WHERE id = :id",
        {"id": UUID(assignment_id)},
    )
    assert assignment_status == "in_progress"
    second = create_submission(client, assignment_id)
    assert second["version"] == first["version"] + 1
    approved = review(client, second["id"], "approved")
    assert approved.status_code == 201
    completed_status = scalar(
        "SELECT status::text FROM task_assignments WHERE id = :id",
        {"id": UUID(assignment_id)},
    )
    assert completed_status == "completed"
    duplicate = review(client, second["id"], "approved")
    assert duplicate.status_code == 409


def test_concurrent_submission_versions_are_unique(seeded: None) -> None:
    client = TestClient(app)
    assignment_id = client.get("/api/v1/assignments", headers=headers()).json()["items"][0]["id"]

    def submit_once() -> int:
        return cast(int, create_submission(TestClient(app), assignment_id)["version"])

    with ThreadPoolExecutor(max_workers=4) as executor:
        versions = list(executor.map(lambda _: submit_once(), range(4)))

    assert len(versions) == len(set(versions))
    assert sorted(versions) == list(range(min(versions), max(versions) + 1))


def test_simultaneous_review_allows_only_one_decision(seeded: None, client: TestClient) -> None:
    submission = create_submission(client)

    def approve_once() -> int:
        response = TestClient(app).post(
            f"/api/v1/submissions/{submission['id']}/reviews",
            json={
                "result": "approved",
                "rubric": {"correctness": "checked"},
                "comment": "phase2 concurrent",
            },
            headers=headers("admin@example.local"),
        )
        return cast(int, response.status_code)

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = sorted(executor.map(lambda _: approve_once(), range(2)))

    assert statuses == [201, 409]
    assert scalar(
        "SELECT count(*) FROM reviews WHERE submission_id = :id",
        {"id": UUID(submission["id"])},
    ) == 1


def test_exam_disabled_has_no_mutation_side_effect(seeded: None, client: TestClient) -> None:
    before = scalar("SELECT count(*) FROM exam_attempts")
    exam_id = scalar("SELECT id FROM exams ORDER BY stable_code LIMIT 1")
    response = client.post(f"/api/v1/exams/{exam_id}/attempts", json={}, headers=headers())
    assert response.status_code == 403
    assert scalar("SELECT count(*) FROM exam_attempts") == before


def test_exam_enabled_duplicate_and_invalid_order(
    seeded: None,
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EXAM_ENABLED", "true")
    get_settings.cache_clear()
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
    invalid_start = client.post(
        f"/api/v1/exam-attempts/{attempt_id}/start",
        json={"acknowledgeRules": False},
        headers=headers(),
    )
    assert invalid_start.status_code == 409
    ready_submit = client.post(
        f"/api/v1/exam-attempts/{attempt_id}/submit",
        json={"answers": {"q": "before start"}},
        headers=headers(),
    )
    assert ready_submit.status_code == 200
    assert ready_submit.json()["attempt"]["status"] == "ready"
    started = client.post(
        f"/api/v1/exam-attempts/{attempt_id}/start",
        json={"acknowledgeRules": True},
        headers=headers(),
    )
    assert started.json()["attempt"]["status"] == "in_progress"
    duplicate_start = client.post(
        f"/api/v1/exam-attempts/{attempt_id}/start",
        json={"acknowledgeRules": True},
        headers=headers(),
    )
    assert duplicate_start.json()["attempt"]["status"] == "in_progress"
    submitted = client.post(
        f"/api/v1/exam-attempts/{attempt_id}/submit",
        json={"answers": {"q": "after start"}},
        headers=headers(),
    )
    assert submitted.json()["attempt"]["status"] == "oral_pending"
    failed = client.post(
        f"/api/v1/exam-attempts/{attempt_id}/oral-review",
        json={"passed": False, "answers": [{"question": "q", "assessment": "fail"}]},
        headers=headers("admin@example.local"),
    )
    assert failed.json()["attempt"]["status"] == "failed"
    get_settings.cache_clear()


def test_runner_disabled_and_repeated_processing(seeded: None, client: TestClient) -> None:
    before = scalar("SELECT count(*) FROM runner_jobs")
    submission = create_submission(client)
    disabled = client.post(
        f"/api/v1/submissions/{submission['id']}/run",
        json={"reason": "phase2"},
        headers=headers(),
    )
    assert disabled.status_code == 403
    assert scalar("SELECT count(*) FROM runner_jobs") == before


def test_runner_enabled_processing_is_idempotent(
    seeded: None,
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RUNNER_ENABLED", "true")
    get_settings.cache_clear()
    submission = create_submission(client)
    queued = client.post(
        f"/api/v1/submissions/{submission['id']}/run",
        json={"reason": "phase2"},
        headers=headers(),
    )
    assert queued.status_code == 202
    with SessionLocal.begin() as session:
        assert process_next_runner_job(session) is True
    with SessionLocal.begin() as session:
        assert process_next_runner_job(session) is False
    status = scalar(
        "SELECT status::text FROM runner_jobs WHERE id = :id",
        {"id": UUID(queued.json()["id"])},
    )
    assert status == "security_rejected"
    detail = client.get(f"/api/v1/submissions/{submission['id']}", headers=headers())
    assert detail.status_code == 200
    assert detail.json()["sanitizedResult"]["hiddenTests"] == "redacted"
    get_settings.cache_clear()


def test_exam_list_detail_expiry_and_unauthorized_oral_review(
    seeded: None,
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exams = client.get("/api/v1/exams", headers=headers())
    assert exams.status_code == 200
    assert len(exams.json()["items"]) > 0
    monkeypatch.setenv("EXAM_ENABLED", "true")
    get_settings.cache_clear()
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
        ORDER BY e.stable_code DESC
        LIMIT 1
        """
    )
    attempt = client.post(f"/api/v1/exams/{exam_id}/attempts", json={}, headers=headers())
    assert attempt.status_code == 201
    attempt_id = attempt.json()["id"]
    try:
        detail = client.get(f"/api/v1/exam-attempts/{attempt_id}", headers=headers())
        assert detail.status_code == 200
        missing = client.get(f"/api/v1/exam-attempts/{uuid4()}", headers=headers())
        assert missing.status_code == 404
        started = client.post(
            f"/api/v1/exam-attempts/{attempt_id}/start",
            json={"acknowledgeRules": True},
            headers=headers(),
        )
        assert started.json()["attempt"]["status"] == "in_progress"
        execute(
            """
            UPDATE exam_attempts
            SET starts_at = now() - interval '2 hours',
                deadline_at = now() - interval '1 minute'
            WHERE id = :id
            """,
            {"id": UUID(attempt_id)},
        )
        expired = client.post(
            f"/api/v1/exam-attempts/{attempt_id}/submit",
            json={"answers": {"q": "late"}},
            headers=headers(),
        )
        assert expired.json()["attempt"]["status"] == "expired"
        learner_oral = client.post(
            f"/api/v1/exam-attempts/{attempt_id}/oral-review",
            json={"passed": True, "answers": [{"question": "q", "assessment": "pass"}]},
            headers=headers(),
        )
        assert learner_oral.status_code == 403
    finally:
        delete_exam_attempt(attempt_id)
        get_settings.cache_clear()


def test_validation_and_seed_entrypoints(seeded: None, capsys: pytest.CaptureFixture[str]) -> None:
    validation_main()
    assert "Validation passed." in capsys.readouterr().out
    seed_main()
    assert "Seed import completed." in capsys.readouterr().out
