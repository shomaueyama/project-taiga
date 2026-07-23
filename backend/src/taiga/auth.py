from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from taiga.config import Settings, get_settings
from taiga.infrastructure.database import get_session

settings_dependency = Depends(get_settings)
session_dependency = Depends(get_session)


@dataclass(frozen=True)
class Principal:
    id: UUID
    email: str
    display_name: str
    role: str
    status: str
    timezone: str


def local_email_from_headers(
    authorization: str | None,
    x_local_user: str | None,
    settings: Settings,
) -> str:
    if not settings.local_auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    if settings.app_env != "local":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid auth config",
        )
    if x_local_user:
        return x_local_user
    prefix = "Bearer local:"
    if authorization and authorization.startswith(prefix):
        return authorization.removeprefix(prefix)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Local user header required",
    )


def get_current_principal(
    authorization: str | None = Header(default=None),
    x_local_user: str | None = Header(default=None),
    settings: Settings = settings_dependency,
    session: Session = session_dependency,
) -> Principal:
    email = local_email_from_headers(authorization, x_local_user, settings)
    row = (
        session.execute(
            text(
                """
                SELECT id, cognito_sub, display_name, role::text, status::text, timezone
                FROM users
                WHERE cognito_sub = :email AND deleted_at IS NULL
                """
            ),
            {"email": email},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown local user")
    if row["status"] != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")
    return Principal(
        id=row["id"],
        email=row["cognito_sub"],
        display_name=row["display_name"],
        role=row["role"],
        status=row["status"],
        timezone=row["timezone"],
    )
