from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, NamedTuple

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
from taiga.authorization import is_reviewer, require_reviewer
from taiga.config import get_settings
from taiga.errors import ConflictError, NotFoundError
from taiga.state_transitions import (
    review_submission_transition,
    submission_status_after_creation,
)

ALLOWED_EXTENSIONS = {
    ".c",
    ".h",
    ".md",
    ".txt",
    ".json",
    ".sh",
    ".png",
    ".jpg",
    ".jpeg",
    ".heic",
    ".heif",
    ".zip",
}
ALLOWED_MEDIA_TYPES = {
    ".c": {"text/plain", "text/x-c"},
    ".h": {"text/plain", "text/x-c"},
    ".md": {"text/markdown", "text/plain"},
    ".txt": {"text/plain"},
    ".json": {"application/json", "text/json"},
    ".sh": {"text/x-shellscript", "text/plain"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".heic": {"image/heic", "image/heif", "application/octet-stream"},
    ".heif": {"image/heic", "image/heif", "application/octet-stream"},
    ".zip": {"application/zip", "application/x-zip-compressed"},
}
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _submission(row: Any) -> SubmissionResponse:
    artifact_links = row.get("artifact_links", []) or []
    return SubmissionResponse(
        id=row["id"],
        assignmentId=row["assignment_id"],
        version=row["submission_version"],
        status=row["status"],
        createdAt=row["created_at"].isoformat(),
        repositoryUrl=row.get("repository_url"),
        commitHash=row.get("commit_hash"),
        submissionNote=(row.get("artifact_manifest_json") or {}).get("submissionNote"),
        artifactNames=[str(item) for item in row.get("artifact_names", [])],
        artifactLinks=list(artifact_links),
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
    if any(ord(char) < 32 for char in request.originalName):
        return "invalid_filename"
    if Path(request.originalName).is_absolute() or request.originalName.startswith("~"):
        return "path_traversal"
    if "/" in request.originalName or "\\" in request.originalName or ".." in request.originalName:
        return "path_traversal"
    if ":" in request.originalName:
        return "path_traversal"
    extension = _extension(request.originalName)
    if extension not in ALLOWED_EXTENSIONS:
        return "extension_not_allowed"
    if request.mediaType not in ALLOWED_MEDIA_TYPES[extension]:
        return "media_type_mismatch"
    if request.sizeBytes == 0:
        return "empty_file"
    if request.sizeBytes < 0 or request.sizeBytes > MAX_UPLOAD_SIZE_BYTES:
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
    stored_original_name = request.originalName[:120]
    stored_size_bytes = min(max(request.sizeBytes, 0), MAX_UPLOAD_SIZE_BYTES)
    stored_sha256 = request.sha256 if _is_sha256(request.sha256) else "0" * 64
    object_key = f"quarantine/{principal.id}/{upload_id}/upload{_extension(stored_original_name)}"
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
            "original_name": stored_original_name,
            "declared_media_type": request.mediaType,
            "declared_size_bytes": stored_size_bytes,
            "declared_sha256": stored_sha256,
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
        raise NotFoundError("Upload not found", code="upload_not_found")
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


def upload_content(
    session: Session,
    principal: Principal,
    upload_id: uuid.UUID,
    content: bytes,
) -> UploadSessionResponse:
    row = get_upload_row(session, principal, upload_id)
    size_bytes = len(content)
    sha256 = hashlib.sha256(content).hexdigest()
    rejection_code = None
    status = "accepted"
    if row["scan_status"] == "rejected":
        status = "rejected"
        rejection_code = row["rejection_code"]
    elif size_bytes > MAX_UPLOAD_SIZE_BYTES:
        status = "rejected"
        rejection_code = "size_limit_exceeded"
    elif size_bytes != row["declared_size_bytes"] or sha256 != row["declared_sha256"]:
        status = "rejected"
        rejection_code = "metadata_mismatch"

    if status == "accepted":
        target = Path(get_settings().local_storage_root) / "uploads" / row["object_key"]
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        except OSError:
            pass

    session.execute(
        text(
            """
            UPDATE upload_sessions
            SET actual_size_bytes = :size_bytes,
                actual_sha256 = :sha256,
                scan_status = CAST(:status AS upload_scan_status),
                rejection_code = :rejection_code,
                uploaded_blob = CASE WHEN :accepted THEN :content ELSE NULL END,
                completed_at = now()
            WHERE id = :id AND owner_id = :owner_id
            """
        ),
        {
            "id": upload_id,
            "owner_id": principal.id,
            "size_bytes": size_bytes,
            "sha256": sha256,
            "status": status,
            "rejection_code": rejection_code,
            "accepted": status == "accepted",
            "content": content,
        },
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
                FOR UPDATE
                """
            ),
            {"assignment_id": assignment_id, "learner_id": principal.id},
        )
        .mappings()
        .first()
    )
    if assignment is None:
        raise NotFoundError("Assignment not found", code="assignment_not_found")
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
        raise ConflictError("All uploads must be accepted", code="uploads_not_accepted")
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
        "submissionNote": request.submissionNote,
    }
    submission_status = submission_status_after_creation()
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
                :status
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
            "status": submission_status,
        },
    )
    for upload in upload_rows:
        accepted_key = upload["object_key"].replace("quarantine/", "accepted/", 1)
        storage_root = Path(get_settings().local_storage_root) / "uploads"
        quarantine_path = storage_root / upload["object_key"]
        accepted_path = storage_root / accepted_key
        if quarantine_path.exists():
            accepted_path.parent.mkdir(parents=True, exist_ok=True)
            quarantine_path.replace(accepted_path)
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
                "s3_key": accepted_key,
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
                {"submissionId": str(submission_id), "status": submission_status}
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
                SELECT s.id, s.assignment_id, s.submission_version, s.status::text, s.created_at,
                       s.repository_url, s.commit_hash, s.artifact_manifest_json,
                       COALESCE(
                           (
                               SELECT array_agg(sa.original_name ORDER BY sa.original_name)
                               FROM submission_artifacts sa
                               WHERE sa.submission_id = s.id
                           ),
                           ARRAY[]::text[]
                       ) AS artifact_names,
                       COALESCE(
                           (
                               SELECT jsonb_agg(
                                   jsonb_build_object(
                                       'id', sa.id,
                                       'originalName', sa.original_name,
                                       'mediaType', sa.media_type,
                                       'sizeBytes', sa.size_bytes
                                   )
                                   ORDER BY sa.original_name
                               )
                               FROM submission_artifacts sa
                               WHERE sa.submission_id = s.id
                           ),
                           '[]'::jsonb
                       ) AS artifact_links
                FROM submissions s
                WHERE s.id = :id AND (:is_reviewer OR s.learner_id = :learner_id)
                """
            ),
            {
                "id": submission_id,
                "learner_id": principal.id,
                "is_reviewer": is_reviewer(principal),
            },
        )
        .mappings()
        .first()
    )
    if row is None:
        raise NotFoundError("Submission not found", code="submission_not_found")
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
                SELECT id, original_name, media_type, size_bytes, sha256
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


class ArtifactContent(NamedTuple):
    content: bytes
    media_type: str
    original_name: str


def get_submission_artifact_content(
    session: Session,
    principal: Principal,
    artifact_id: uuid.UUID,
) -> ArtifactContent:
    row = (
        session.execute(
            text(
                """
                SELECT sa.original_name, sa.media_type, us.uploaded_blob
                FROM submission_artifacts sa
                JOIN submissions s ON s.id = sa.submission_id
                JOIN upload_sessions us ON us.id = sa.upload_session_id
                WHERE sa.id = :artifact_id
                  AND (:is_reviewer OR s.learner_id = :learner_id)
                """
            ),
            {
                "artifact_id": artifact_id,
                "learner_id": principal.id,
                "is_reviewer": is_reviewer(principal),
            },
        )
        .mappings()
        .first()
    )
    if row is None or row["uploaded_blob"] is None:
        raise NotFoundError("Artifact not found", code="artifact_not_found")
    return ArtifactContent(
        content=bytes(row["uploaded_blob"]),
        media_type=row["media_type"],
        original_name=row["original_name"],
    )


def review_queue(session: Session, principal: Principal, limit: int = 20) -> ReviewQueuePage:
    require_reviewer(principal)
    rows = (
        session.execute(
            text(
                """
                SELECT s.id, s.assignment_id, s.submission_version, s.status::text, s.created_at,
                       s.repository_url, s.commit_hash, s.artifact_manifest_json,
                       COALESCE(
                           (
                               SELECT array_agg(sa.original_name ORDER BY sa.original_name)
                               FROM submission_artifacts sa
                               WHERE sa.submission_id = s.id
                           ),
                           ARRAY[]::text[]
                       ) AS artifact_names,
                       COALESCE(
                           (
                               SELECT jsonb_agg(
                                   jsonb_build_object(
                                       'id', sa.id,
                                       'originalName', sa.original_name,
                                       'mediaType', sa.media_type,
                                       'sizeBytes', sa.size_bytes
                                   )
                                   ORDER BY sa.original_name
                               )
                               FROM submission_artifacts sa
                               WHERE sa.submission_id = s.id
                           ),
                           '[]'::jsonb
                       ) AS artifact_links
                FROM submissions s
                WHERE s.status = 'manual_review_pending'
                ORDER BY s.created_at DESC
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
    require_reviewer(principal)
    submission_row = (
        session.execute(
            text(
                """
                SELECT id, assignment_id, submission_version, status::text, created_at
                FROM submissions
                WHERE id = :id AND (:is_reviewer OR learner_id = :learner_id)
                FOR UPDATE
                """
            ),
            {
                "id": submission_id,
                "learner_id": principal.id,
                "is_reviewer": is_reviewer(principal),
            },
        )
        .mappings()
        .first()
    )
    if submission_row is None:
        raise NotFoundError("Submission not found", code="submission_not_found")
    submission = _submission(submission_row)
    submission_status, assignment_status = review_submission_transition(
        submission.status,
        request.result,
    )
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
            "result": submission_status,
            "rubric_json": _json(request.rubric),
            "comment": request.comment,
        },
    )
    session.execute(
        text("UPDATE submissions SET status = :status WHERE id = :id"),
        {"id": submission_id, "status": submission_status},
    )
    session.execute(
        text(
            """
            UPDATE task_assignments
            SET status = :status, updated_at = now(), version = version + 1
            WHERE id = :assignment_id
            """
        ),
        {"assignment_id": submission.assignmentId, "status": assignment_status},
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
