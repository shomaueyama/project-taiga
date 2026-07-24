from __future__ import annotations

import json
import uuid
from datetime import timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from taiga.api_schemas import (
    CreateExamAttemptRequest,
    ExamAttemptDetail,
    ExamAttemptResponse,
    ExamPage,
    ExamSummary,
    OralReviewRequest,
    StartExamRequest,
    SubmitExamRequest,
)
from taiga.auth import Principal
from taiga.authorization import is_reviewer, require_reviewer
from taiga.config import get_settings
from taiga.errors import ConflictError, FeatureDisabledError, NotFoundError
from taiga.state_transitions import (
    oral_review_transition,
    start_exam_transition,
    submit_exam_transition,
)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _attempt(row: Any) -> ExamAttemptResponse:
    return ExamAttemptResponse(
        id=row["id"],
        examId=row["exam_id"],
        status=row["status"],
        attemptNumber=row["attempt_number"],
    )


def list_exams(session: Session, _principal: Principal, limit: int = 20) -> ExamPage:
    rows = (
        session.execute(
            text(
                """
                SELECT e.id, e.stable_code, e.scheduled_at, e.blueprint_json ->> 'title' AS title
                FROM exams e
                ORDER BY e.scheduled_at
                LIMIT :limit
                """
            ),
            {"limit": limit},
        )
        .mappings()
        .all()
    )
    return ExamPage(
        items=[
            ExamSummary(
                id=row["id"],
                stableCode=row["stable_code"],
                title=row["title"] or row["stable_code"],
                scheduledAt=row["scheduled_at"].isoformat(),
            )
            for row in rows
        ],
        nextCursor=None,
    )


def reserve_attempt(
    session: Session,
    principal: Principal,
    exam_id: uuid.UUID,
    _request: CreateExamAttemptRequest,
) -> ExamAttemptResponse:
    if not get_settings().exam_enabled:
        raise FeatureDisabledError("Exam is disabled", code="exam_disabled")
    variant = (
        session.execute(
            text(
                """
                SELECT v.id, v.problem_snapshot_json
                FROM exam_variants v
                WHERE v.exam_id = :exam_id
                  AND v.active = true
                  AND NOT EXISTS (
                    SELECT 1 FROM exam_attempts a
                    WHERE a.exam_id = :exam_id
                      AND a.learner_id = :learner_id
                      AND a.exam_variant_id = v.id
                  )
                ORDER BY v.stable_code
                LIMIT 1
                FOR UPDATE
                """
            ),
            {"exam_id": exam_id, "learner_id": principal.id},
        )
        .mappings()
        .first()
    )
    if variant is None:
        raise ConflictError("No unseen exam variant is available", code="no_exam_variant_available")
    attempt_number = int(
        session.execute(
            text(
                """
                SELECT COALESCE(max(attempt_number), 0) + 1
                FROM exam_attempts
                WHERE exam_id = :exam_id AND learner_id = :learner_id
                """
            ),
            {"exam_id": exam_id, "learner_id": principal.id},
        ).scalar_one()
    )
    attempt_id = uuid.uuid4()
    session.execute(
        text(
            """
            INSERT INTO exam_attempts (
                id, exam_id, exam_variant_id, learner_id, attempt_number, status,
                variant_snapshot_json
            )
            VALUES (
                :id, :exam_id, :exam_variant_id, :learner_id, :attempt_number, 'ready',
                CAST(:variant_snapshot_json AS jsonb)
            )
            """
        ),
        {
            "id": attempt_id,
            "exam_id": exam_id,
            "exam_variant_id": variant["id"],
            "learner_id": principal.id,
            "attempt_number": attempt_number,
            "variant_snapshot_json": _json(variant["problem_snapshot_json"]),
        },
    )
    return get_attempt_summary(session, principal, attempt_id)


def get_attempt_summary(
    session: Session,
    principal: Principal,
    attempt_id: uuid.UUID,
) -> ExamAttemptResponse:
    row = _attempt_row(session, principal, attempt_id)
    return _attempt(row)


def _attempt_row(session: Session, principal: Principal, attempt_id: uuid.UUID) -> Any:
    row = (
        session.execute(
            text(
                """
                SELECT id, exam_id, status::text, attempt_number, variant_snapshot_json,
                       starts_at, deadline_at, submitted_at, result_json
                FROM exam_attempts
                WHERE id = :id AND (:is_reviewer OR learner_id = :learner_id)
                """
            ),
            {
                "id": attempt_id,
                "learner_id": principal.id,
                "is_reviewer": is_reviewer(principal),
            },
        )
        .mappings()
        .first()
    )
    if row is None:
        raise NotFoundError("Exam attempt not found", code="exam_attempt_not_found")
    return row


def get_attempt_detail(
    session: Session,
    principal: Principal,
    attempt_id: uuid.UUID,
) -> ExamAttemptDetail:
    row = _attempt_row(session, principal, attempt_id)
    return ExamAttemptDetail(
        attempt=_attempt(row),
        variantSnapshot=row["variant_snapshot_json"],
        startsAt=row["starts_at"].isoformat() if row["starts_at"] else None,
        deadlineAt=row["deadline_at"].isoformat() if row["deadline_at"] else None,
        submittedAt=row["submitted_at"].isoformat() if row["submitted_at"] else None,
        result=row["result_json"],
    )


def start_attempt(
    session: Session,
    principal: Principal,
    attempt_id: uuid.UUID,
    request: StartExamRequest,
) -> ExamAttemptDetail:
    if not get_settings().exam_enabled:
        raise FeatureDisabledError("Exam is disabled", code="exam_disabled")
    if not request.acknowledgeRules:
        raise ConflictError("Exam rules must be acknowledged", code="exam_rules_not_acknowledged")
    row = _attempt_row(session, principal, attempt_id)
    next_status = start_exam_transition(row["status"])
    if next_status == "in_progress" and row["status"] != "in_progress":
        session.execute(
            text(
                """
                UPDATE exam_attempts
                SET status = :status,
                    starts_at = now(),
                    deadline_at = now() + (:duration_seconds * interval '1 second'),
                    version = version + 1
                WHERE id = :id
                """
            ),
            {
                "id": attempt_id,
                "status": next_status,
                "duration_seconds": int(timedelta(minutes=60).total_seconds()),
            },
        )
    return get_attempt_detail(session, principal, attempt_id)


def submit_attempt(
    session: Session,
    principal: Principal,
    attempt_id: uuid.UUID,
    request: SubmitExamRequest,
) -> ExamAttemptDetail:
    if not get_settings().exam_enabled:
        raise FeatureDisabledError("Exam is disabled", code="exam_disabled")
    row = _attempt_row(session, principal, attempt_id)
    if row["status"] != "in_progress":
        return get_attempt_detail(session, principal, attempt_id)
    late = bool(
        session.execute(
            text("SELECT now() > :deadline"),
            {"deadline": row["deadline_at"]},
        ).scalar_one()
    )
    if late:
        session.execute(
            text("UPDATE exam_attempts SET status = :status WHERE id = :id"),
            {"id": attempt_id, "status": submit_exam_transition(row["status"], late=True)},
        )
        return get_attempt_detail(session, principal, attempt_id)
    result = {
        "answersRecorded": bool(request.answers),
        "submissionId": str(request.submissionId) if request.submissionId else None,
    }
    session.execute(
        text(
            """
            UPDATE exam_attempts
            SET status = :status,
                submitted_at = now(),
                final_submission_id = :submission_id,
                result_json = CAST(:result AS jsonb),
                version = version + 1
            WHERE id = :id
            """
        ),
        {
            "id": attempt_id,
            "status": submit_exam_transition(row["status"], late=False),
            "submission_id": request.submissionId,
            "result": _json(result),
        },
    )
    return get_attempt_detail(session, principal, attempt_id)


def oral_review(
    session: Session,
    principal: Principal,
    attempt_id: uuid.UUID,
    request: OralReviewRequest,
) -> ExamAttemptDetail:
    if not get_settings().exam_enabled:
        raise FeatureDisabledError("Exam is disabled", code="exam_disabled")
    require_reviewer(principal)
    row = _attempt_row(session, principal, attempt_id)
    status = oral_review_transition(row["status"], passed=request.passed)
    session.execute(
        text(
            """
            UPDATE exam_attempts
            SET status = :status,
                oral_result_json = CAST(:oral_result AS jsonb),
                version = version + 1
            WHERE id = :id AND status = 'oral_pending'
            """
        ),
        {
            "id": attempt_id,
            "status": status,
            "oral_result": _json(
                {
                    "passed": request.passed,
                    "answers": [item.model_dump() for item in request.answers],
                }
            ),
        },
    )
    if status == "passed":
        session.execute(
            text(
                """
                INSERT INTO rank_history (
                    id, learner_id, rank_code, evidence_snapshot_json, achieved_at
                )
                SELECT :id, learner_id, 'local-mvp', CAST(:evidence AS jsonb), now()
                FROM exam_attempts
                WHERE id = :attempt_id
                """
            ),
            {
                "id": uuid.uuid4(),
                "attempt_id": row["id"],
                "evidence": _json({"examAttemptId": str(row["id"])}),
            },
        )
    return get_attempt_detail(session, principal, attempt_id)
