from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from taiga.api_schemas import (
    CurriculumVersionPage,
    CurriculumVersionSummary,
    FeatureFlag,
    FeatureFlagList,
    InviteUserRequest,
    LearningAnalytics,
    NotificationPage,
    NotificationPreference,
    NotificationPreferenceList,
    NotificationResponse,
    PageUserProfile,
    UpdateFeatureFlagRequest,
    UserProfile,
)
from taiga.auth import Principal


def require_admin(principal: Principal) -> None:
    if principal.role != "admin":
        raise PermissionError("Admin role required")


def _user(row: Any) -> UserProfile:
    return UserProfile(
        id=row["id"],
        displayName=row["display_name"],
        role=row["role"],
        status=row["status"],
        timezone=row["timezone"],
    )


def list_users(session: Session, principal: Principal, limit: int = 20) -> PageUserProfile:
    require_admin(principal)
    rows = (
        session.execute(
            text(
                """
                SELECT id, display_name, role::text, status::text, timezone
                FROM users
                WHERE deleted_at IS NULL
                ORDER BY created_at
                LIMIT :limit
                """
            ),
            {"limit": limit},
        )
        .mappings()
        .all()
    )
    return PageUserProfile(items=[_user(row) for row in rows], nextCursor=None)


def invite_user(session: Session, principal: Principal, request: InviteUserRequest) -> UserProfile:
    require_admin(principal)
    user_id = uuid.uuid4()
    session.execute(
        text(
            """
            INSERT INTO users (id, cognito_sub, display_name, role, status)
            VALUES (:id, :email, :display_name, :role, 'invited')
            ON CONFLICT (cognito_sub) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                role = EXCLUDED.role,
                updated_at = now()
            """
        ),
        {
            "id": user_id,
            "email": request.email,
            "display_name": request.displayName,
            "role": request.role,
        },
    )
    row = (
        session.execute(
            text(
                """
                SELECT id, display_name, role::text, status::text, timezone
                FROM users WHERE cognito_sub = :email
                """
            ),
            {"email": request.email},
        )
        .mappings()
        .one()
    )
    return _user(row)


def set_user_status(
    session: Session,
    principal: Principal,
    user_id: uuid.UUID,
    user_status: str,
) -> UserProfile:
    require_admin(principal)
    row = (
        session.execute(
            text(
                """
                UPDATE users
                SET status = :status, updated_at = now(), version = version + 1
                WHERE id = :id
                RETURNING id, display_name, role::text, status::text, timezone
                """
            ),
            {"id": user_id, "status": user_status},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise LookupError("User not found")
    return _user(row)


def list_flags(session: Session, principal: Principal) -> FeatureFlagList:
    require_admin(principal)
    rows = (
        session.execute(text("SELECT key, enabled, version FROM feature_flags ORDER BY key"))
        .mappings()
        .all()
    )
    return FeatureFlagList(
        items=[
            FeatureFlag(key=row["key"], enabled=row["enabled"], version=row["version"])
            for row in rows
        ]
    )


def update_flag(
    session: Session,
    principal: Principal,
    key: str,
    request: UpdateFeatureFlagRequest,
) -> FeatureFlag:
    require_admin(principal)
    row = (
        session.execute(
            text(
                """
                UPDATE feature_flags
                SET enabled = :enabled,
                    updated_by = :updated_by,
                    updated_at = now(),
                    version = version + 1
                WHERE key = :key
                RETURNING key, enabled, version
                """
            ),
            {"key": key, "enabled": request.enabled, "updated_by": principal.id},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise LookupError("Feature flag not found")
    return FeatureFlag(key=row["key"], enabled=row["enabled"], version=row["version"])


def list_notifications(
    session: Session,
    principal: Principal,
    limit: int = 20,
) -> NotificationPage:
    rows = (
        session.execute(
            text(
                """
                SELECT id, type, title, body, read_at, created_at
                FROM notifications
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"user_id": principal.id, "limit": limit},
        )
        .mappings()
        .all()
    )
    return NotificationPage(
        items=[
            NotificationResponse(
                id=row["id"],
                type=row["type"],
                title=row["title"],
                body=row["body"],
                readAt=row["read_at"].isoformat() if row["read_at"] else None,
                createdAt=row["created_at"].isoformat(),
            )
            for row in rows
        ],
        nextCursor=None,
    )


def notification_preferences(session: Session, principal: Principal) -> NotificationPreferenceList:
    rows = (
        session.execute(
            text(
                """
                SELECT channel, event_type, enabled
                FROM notification_preferences
                WHERE user_id = :user_id
                ORDER BY channel, event_type
                """
            ),
            {"user_id": principal.id},
        )
        .mappings()
        .all()
    )
    return NotificationPreferenceList(
        items=[
            NotificationPreference(
                channel=row["channel"],
                eventType=row["event_type"],
                enabled=row["enabled"],
            )
            for row in rows
        ]
    )


def analytics(session: Session, principal: Principal) -> LearningAnalytics:
    require_admin(principal)
    learners = int(
        session.execute(text("SELECT count(*) FROM users WHERE role = 'learner'")).scalar_one()
    )
    submissions = int(session.execute(text("SELECT count(*) FROM submissions")).scalar_one())
    approved = int(
        session.execute(
            text("SELECT count(*) FROM submissions WHERE status = 'approved'")
        ).scalar_one()
    )
    attempts = int(session.execute(text("SELECT count(*) FROM exam_attempts")).scalar_one())
    passed = int(
        session.execute(
            text("SELECT count(*) FROM exam_attempts WHERE status = 'passed'")
        ).scalar_one()
    )
    return LearningAnalytics(
        learners=learners,
        submissions=submissions,
        approvedSubmissions=approved,
        examAttempts=attempts,
        passedExamAttempts=passed,
    )


def curriculum_versions(
    session: Session,
    principal: Principal,
    limit: int = 20,
) -> CurriculumVersionPage:
    require_admin(principal)
    rows = (
        session.execute(
            text(
                """
                SELECT id, version, status::text, content_hash
                FROM curriculum_versions
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        )
        .mappings()
        .all()
    )
    return CurriculumVersionPage(
        items=[
            CurriculumVersionSummary(
                id=row["id"],
                version=row["version"],
                status=row["status"],
                contentHash=row["content_hash"],
            )
            for row in rows
        ],
        nextCursor=None,
    )
