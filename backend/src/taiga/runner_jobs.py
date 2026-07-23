from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from taiga.api_schemas import RunnerJobResponse, RunSubmissionRequest
from taiga.auth import Principal
from taiga.config import get_settings
from taiga.submission_service import get_submission_summary


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _job(row: Any) -> RunnerJobResponse:
    return RunnerJobResponse(
        id=row["id"],
        submissionId=row["submission_id"],
        status=row["status"],
        attempt=row["attempt"],
        sanitizedResult=row["sanitized_result_json"],
    )


def queue_runner_job(
    session: Session,
    principal: Principal,
    submission_id: uuid.UUID,
    _request: RunSubmissionRequest,
) -> RunnerJobResponse:
    submission = get_submission_summary(session, principal, submission_id)
    existing = (
        session.execute(
            text(
                """
                SELECT id, submission_id, status::text, attempt, sanitized_result_json
                FROM runner_jobs
                WHERE submission_id = :submission_id
                ORDER BY attempt DESC
                LIMIT 1
                """
            ),
            {"submission_id": submission.id},
        )
        .mappings()
        .first()
    )
    if existing is not None and existing["status"] in {"queued", "claimed", "succeeded"}:
        return _job(existing)
    attempt = int(
        session.execute(
            text("SELECT COALESCE(max(attempt), 0) + 1 FROM runner_jobs WHERE submission_id = :id"),
            {"id": submission.id},
        ).scalar_one()
    )
    job_id = uuid.uuid4()
    session.execute(
        text(
            """
            INSERT INTO runner_jobs (
                id, submission_id, status, attempt, image_digest, security_profile_version
            )
            VALUES (
                :id, :submission_id, 'queued', :attempt,
                'local-runner-disabled', 'RUNNER_SECURITY_V1'
            )
            """
        ),
        {"id": job_id, "submission_id": submission.id, "attempt": attempt},
    )
    session.execute(
        text(
            """
            INSERT INTO outbox_events (id, aggregate_type, aggregate_id, event_type, payload_json)
            VALUES (:id, 'runner_job', :aggregate_id, 'runner_job.queued', CAST(:payload AS jsonb))
            """
        ),
        {
            "id": uuid.uuid4(),
            "aggregate_id": job_id,
            "payload": _json({"runnerJobId": str(job_id), "submissionId": str(submission.id)}),
        },
    )
    session.execute(
        text("UPDATE submissions SET status = 'queued' WHERE id = :id"),
        {"id": submission.id},
    )
    row = (
        session.execute(
            text(
                """
                SELECT id, submission_id, status::text, attempt, sanitized_result_json
                FROM runner_jobs WHERE id = :id
                """
            ),
            {"id": job_id},
        )
        .mappings()
        .one()
    )
    return _job(row)


def process_next_runner_job(session: Session) -> bool:
    event = (
        session.execute(
            text(
                """
                SELECT id, aggregate_id
                FROM outbox_events
                WHERE published_at IS NULL AND event_type = 'runner_job.queued'
                ORDER BY next_attempt_at, created_at
                LIMIT 1
                FOR UPDATE SKIP LOCKED
                """
            )
        )
        .mappings()
        .first()
    )
    if event is None:
        return False
    settings = get_settings()
    result = {
        "summary": "Runner is disabled; local job recorded without executing learner code.",
        "runnerEnabled": settings.runner_enabled,
        "publicTests": [],
        "hiddenTests": "redacted",
    }
    status = "succeeded" if not settings.runner_enabled else "security_rejected"
    submission_status = "manual_review_pending" if status == "succeeded" else "needs_revision"
    session.execute(
        text(
            """
            UPDATE runner_jobs
            SET status = :status,
                started_at = COALESCE(started_at, now()),
                finished_at = now(),
                sanitized_result_json = CAST(:result AS jsonb),
                resource_usage_json = '{"mode":"disabled"}'::jsonb,
                version = version + 1
            WHERE id = :id
            """
        ),
        {"id": event["aggregate_id"], "status": status, "result": _json(result)},
    )
    session.execute(
        text(
            """
            UPDATE submissions
            SET status = :status
            WHERE id = (SELECT submission_id FROM runner_jobs WHERE id = :job_id)
            """
        ),
        {"job_id": event["aggregate_id"], "status": submission_status},
    )
    session.execute(
        text("UPDATE outbox_events SET published_at = now() WHERE id = :id"),
        {"id": event["id"]},
    )
    return True
