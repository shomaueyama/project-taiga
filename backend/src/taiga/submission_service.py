from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from taiga.api_schemas import (
    CompleteUploadRequest,
    CreateReviewRequest,
    CreateSubmissionRequest,
    CreateUploadRequest,
    ReviewQueuePage,
    ReviewResponse,
    SubmissionDetail,
    SubmissionResponse,
    UploadSessionResponse,
)
from taiga.auth import Principal
from taiga.config import get_settings

ALLOWED_EXTENSIONS = {".c", ".h", ".md", ".txt", ".json", ".sh", ".png", ".jpg", ".jpeg", ".zip"}


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _submission(row: Any) -> SubmissionResponse:
    return SubmissionResponse(
        id=row["id"],
        assignmentId=row["assignment_id"],
        version=row["submission_version"],
        status=row["status"],
        createdAt=row["created_at"].isoformat(),
    )


def _upload(row: Any, include_url: bool = False) -> UploadSessionResponse:
    upload_url = None
    if include_url:
        upload_url = f"file://local-storage/uploads/{row['object_key']}"
    return UploadSessionResponse(
        id=row["id"],
        status=row["scan_status"],
        uploadUrl=upload_url,
        expiresAt=row["expires_at"].isoformat(),
        rejectionCode=row["rejection_code"],
    )


def _extension(name: str) -> str:
    return Path(name).suffix.lower()


def validate_upload_request(request: CreateUploadRequest) -> str | None:
    if len(request.originalName) > 120:
        return "filename_too_long"
    if "/" in request.originalName or "\\" in request.originalName or ".." in request.originalName:
        return "path_traversal"
    if _extension(request.originalName) not in ALLOWED_EXTENSIONS:
        return "extension_not_allowed"
    if request.sizeBytes < 0 or request.sizeBytes > 50 * 1024 * 1024:
        return "size_limit_exceeded"
    if not _is_sha256(request.sha256):
        return "invalid_sha256"
    return None


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def create_upload(
    session: Session,
    principal: Principal,
    request: CreateUploadRequest,
) -> UploadSessionResponse:
    upload_id = uuid.uuid4()
    rejection_code = validate_upload_request(request)
    status = "rejected" if rejection_code else "created"
    object_key = f"quarantine/{principal.id}/{upload_id}/{request.originalName}"
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    session.execute(
        text(
            """
            INSERT INTO upload_sessions (
                id, owner_id, object_key, original_name, declared_media_type,
                declared_size_bytes, declared_sha256, scan_status, rejection_code, expires_at
            )
            VALUES (
                :id, :owner_id, :object_key, :original_name, :declared_media_type,
                :declared_size_bytes, :declared_sha256, :scan_status, :rejection_code, :expires_at
            )
            """
        ),
        {
            "id": upload_id,
            "owner_id": principal.id,
            "object_key": object_key,
            "original_name": request.originalName,
            "declared_media_type": request.mediaType,
            "declared_size_bytes": request.sizeBytes,
            "declared_sha256": request.sha256,
            "scan_status": status,
            "rejection_code": rejection_code,
            "expires_at": expires_at,
        },
    )
    row = get_upload_row(session, principal, upload_id)
    return _upload(row, include_url=status == "created")


def get_upload_row(session: Session, principal: Principal, upload_id: uuid.UUID) -> Any:
    row = (
        session.execute(
            text(
                """
                SELECT id, object_key, original_name, declared_media_type, declared_size_bytes,
                       declared_sha256, scan_status::text, rejection_code, expires_at
                FROM upload_sessions
                WHERE id = :id AND owner_id = :owner_id
                """
            ),
            {"id": upload_id, "owner_id": principal.id},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise LookupError("Upload not found")
    return row


def get_upload(
    session: Session,
    principal: Principal,
    upload_id: uuid.UUID,
) -> UploadSessionResponse:
    return _upload(get_upload_row(session, principal, upload_id))


def complete_upload(
    session: Session,
    principal: Principal,
    upload_id: uuid.UUID,
    request: CompleteUploadRequest,
) -> UploadSessionResponse:
    row = get_upload_row(session, principal, upload_id)
    rejection_code = None
    status = "accepted"
    if row["scan_status"] == "rejected":
        status = "rejected"
        rejection_code = row["rejection_code"]
    elif (
        request.sizeBytes != row["declared_size_bytes"]
        or request.sha256 != row["declared_sha256"]
    ):
        status = "rejected"
        rejection_code = "metadata_mismatch"
    session.execute(
        text(
            """
            UPDATE upload_sessions
            SET actual_size_bytes = :size_bytes,
                actual_sha256 = :sha256,
                scan_status = :status,
                rejection_code = :rejection_code,
                completed_at = now()
            WHERE id = :id AND owner_id = :owner_id
            """
        ),
        {
            "id": upload_id,
            "owner_id": principal.id,
            "size_bytes": request.sizeBytes,
            "sha256": request.sha256,
            "status": status,
            "rejection_code": rejection_code,
        },
    )
    accepted_dir = Path(get_settings().local_storage_root) / "uploads"
    accepted_dir.mkdir(parents=True, exist_ok=True)
    if status == "accepted":
        (accepted_dir / f"{upload_id}.manifest.json").write_text(
            _json({"sha256": request.sha256, "sizeBytes": request.sizeBytes}) + "\n",
            encoding="utf-8",
        )
    return get_upload(session, principal, upload_id)


def create_submission(
    session: Session,
    principal: Principal,
    assignment_id: uuid.UUID,
    request: CreateSubmissionRequest,
) -> SubmissionResponse:
    assignment = (
        session.execute(
            text(
                """
                SELECT id
                FROM task_assignments
                WHERE id = :assignment_id AND learner_id = :learner_id
                """
            ),
            {"assignment_id": assignment_id, "learner_id": principal.id},
        )
        .mappings()
        .first()
    )
    if assignment is None:
        raise LookupError("Assignment not found")
    upload_rows = (
        session.execute(
            text(
                """
                SELECT id, object_key, actual_sha256, declared_sha256, detected_media_type,
                       declared_media_type, actual_size_bytes, declared_size_bytes, original_name
                FROM upload_sessions
                WHERE owner_id = :owner_id
                  AND id = ANY(:upload_ids)
                  AND scan_status = 'accepted'
                """
            ),
            {"owner_id": principal.id, "upload_ids": request.uploadIds},
        )
        .mappings()
        .all()
    )
    if len(upload_rows) != len(request.uploadIds):
        raise ValueError("All uploads must be accepted")
    version = int(
        session.execute(
            text(
                """
                SELECT COALESCE(max(submission_version), 0) + 1
                FROM submissions
                WHERE assignment_id = :assignment_id
                """
            ),
            {"assignment_id": assignment_id},
        ).scalar_one()
    )
    submission_id = uuid.uuid4()
    manifest = {
        "uploadIds": [str(upload_id) for upload_id in request.uploadIds],
        "sourceType": request.sourceType,
    }
    session.execute(
        text(
            """
            INSERT INTO submissions (
                id, assignment_id, learner_id, submission_version, source_type,
                repository_url, commit_hash, artifact_manifest_json, status
            )
            VALUES (
                :id, :assignment_id, :learner_id, :submission_version, :source_type,
                :repository_url, :commit_hash, CAST(:artifact_manifest_json AS jsonb),
                'manual_review_pending'
            )
            """
        ),
        {
            "id": submission_id,
            "assignment_id": assignment_id,
            "learner_id": principal.id,
            "submission_version": version,
            "source_type": request.sourceType,
            "repository_url": request.repositoryUrl,
            "commit_hash": request.commitHash,
            "artifact_manifest_json": _json(manifest),
        },
    )
    for upload in upload_rows:
        session.execute(
            text(
                """
                INSERT INTO submission_artifacts (
                    id, submission_id, upload_session_id, s3_key, sha256,
                    media_type, size_bytes, original_name
                )
                VALUES (
                    :id, :submission_id, :upload_session_id, :s3_key, :sha256,
                    :media_type, :size_bytes, :original_name
                )
                """
            ),
            {
                "id": uuid.uuid4(),
                "submission_id": submission_id,
                "upload_session_id": upload["id"],
                "s3_key": upload["object_key"].replace("quarantine/", "accepted/", 1),
                "sha256": upload["actual_sha256"] or upload["declared_sha256"],
                "media_type": upload["detected_media_type"] or upload["declared_media_type"],
                "size_bytes": upload["actual_size_bytes"] or upload["declared_size_bytes"],
                "original_name": upload["original_name"],
            },
        )
    session.execute(
        text(
            """
            INSERT INTO outbox_events (id, aggregate_type, aggregate_id, event_type, payload_json)
            VALUES (:id, 'submission', :aggregate_id, 'submission.created', CAST(:payload AS jsonb))
            """
        ),
        {
            "id": uuid.uuid4(),
            "aggregate_id": submission_id,
            "payload": _json(
                {"submissionId": str(submission_id), "status": "manual_review_pending"}
            ),
        },
    )
    session.execute(
        text(
            """
            INSERT INTO audit_events (
                id, actor_id, actor_role, action, entity_type, entity_id, outcome
            )
            VALUES (
                :id, :actor_id, :actor_role, 'submission.create', 'submission',
                :entity_id, 'success'
            )
            """
        ),
        {
            "id": uuid.uuid4(),
            "actor_id": principal.id,
            "actor_role": principal.role,
            "entity_id": submission_id,
        },
    )
    return get_submission_summary(session, principal, submission_id)


def get_submission_summary(
    session: Session,
    principal: Principal,
    submission_id: uuid.UUID,
) -> SubmissionResponse:
    row = (
        session.execute(
            text(
                """
                SELECT id, assignment_id, submission_version, status::text, created_at
                FROM submissions
                WHERE id = :id AND (:is_reviewer OR learner_id = :learner_id)
                """
            ),
            {
                "id": submission_id,
                "learner_id": principal.id,
                "is_reviewer": principal.role in {"reviewer", "admin"},
            },
        )
        .mappings()
        .first()
    )
    if row is None:
        raise LookupError("Submission not found")
    return _submission(row)


def get_submission_detail(
    session: Session,
    principal: Principal,
    submission_id: uuid.UUID,
) -> SubmissionDetail:
    submission = get_submission_summary(session, principal, submission_id)
    artifacts = (
        session.execute(
            text(
                """
                SELECT original_name, media_type, size_bytes, sha256
                FROM submission_artifacts
                WHERE submission_id = :submission_id
                ORDER BY original_name
                """
            ),
            {"submission_id": submission_id},
        )
        .mappings()
        .all()
    )
    runner_result = session.execute(
        text(
            """
            SELECT sanitized_result_json
            FROM runner_jobs
            WHERE submission_id = :submission_id
              AND sanitized_result_json IS NOT NULL
            ORDER BY attempt DESC
            LIMIT 1
            """
        ),
        {"submission_id": submission_id},
    ).scalar_one_or_none()
    return SubmissionDetail(
        submission=submission,
        artifacts=[dict(row) for row in artifacts],
        sanitizedResult=runner_result,
    )


def review_queue(session: Session, principal: Principal, limit: int = 20) -> ReviewQueuePage:
    if principal.role not in {"reviewer", "admin"}:
        raise PermissionError("Reviewer role required")
    rows = (
        session.execute(
            text(
                """
                SELECT id, assignment_id, submission_version, status::text, created_at
                FROM submissions
                WHERE status = 'manual_review_pending'
                ORDER BY created_at
                LIMIT :limit
                """
            ),
            {"limit": limit},
        )
        .mappings()
        .all()
    )
    return ReviewQueuePage(items=[_submission(row) for row in rows], nextCursor=None)


def create_review(
    session: Session,
    principal: Principal,
    submission_id: uuid.UUID,
    request: CreateReviewRequest,
) -> ReviewResponse:
    if principal.role not in {"reviewer", "admin"}:
        raise PermissionError("Reviewer role required")
    submission = get_submission_summary(session, principal, submission_id)
    review_id = uuid.uuid4()
    session.execute(
        text(
            """
            INSERT INTO reviews (id, submission_id, reviewer_id, result, rubric_json, comment)
            VALUES (
                :id, :submission_id, :reviewer_id, :result,
                CAST(:rubric_json AS jsonb), :comment
            )
            """
        ),
        {
            "id": review_id,
            "submission_id": submission.id,
            "reviewer_id": principal.id,
            "result": request.result,
            "rubric_json": _json(request.rubric),
            "comment": request.comment,
        },
    )
    session.execute(
        text("UPDATE submissions SET status = :status WHERE id = :id"),
        {"id": submission_id, "status": request.result},
    )
    session.execute(
        text(
            """
            INSERT INTO notifications (
                id, user_id, type, title, body, entity_type, entity_id, deduplication_key
            )
            SELECT :id, learner_id, 'review_completed', 'Review completed',
                   :body, 'submission', id, :deduplication_key
            FROM submissions
            WHERE id = :submission_id
            """
        ),
        {
            "id": uuid.uuid4(),
            "body": request.comment,
            "deduplication_key": hashlib.sha256(f"review:{review_id}".encode()).hexdigest(),
            "submission_id": submission_id,
        },
    )
    row = (
        session.execute(
            text("SELECT id, result::text, comment, created_at FROM reviews WHERE id = :id"),
            {"id": review_id},
        )
        .mappings()
        .one()
    )
    return ReviewResponse(
        id=row["id"],
        result=row["result"],
        comment=row["comment"],
        createdAt=row["created_at"].isoformat(),
    )
