import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from taiga.cloudflare_access import AccessVerificationError, verify_cloudflare_access
from taiga.config import Settings, get_settings
from taiga.infrastructure.database import get_session

settings_dependency = Depends(get_settings)
session_dependency = Depends(get_session)
SESSION_COOKIE_NAME = "taiga_session"


@dataclass(frozen=True)
class Principal:
    id: UUID
    email: str
    display_name: str
    role: str
    status: str
    timezone: str


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _session_secret(settings: Settings) -> bytes:
    secret = settings.app_session_secret
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APP_SESSION_SECRET is not configured",
        )
    return secret.encode("utf-8")


def _sign(payload: str, settings: Settings) -> str:
    digest = hmac.new(_session_secret(settings), payload.encode("ascii"), hashlib.sha256).digest()
    return _base64url_encode(digest)


def create_session_token(email: str, settings: Settings) -> str:
    payload = _base64url_encode(
        json.dumps(
            {"email": email.lower(), "exp": int(time.time()) + settings.app_session_ttl_seconds},
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return f"{payload}.{_sign(payload, settings)}"


def email_from_session_token(token: str, settings: Settings) -> str | None:
    try:
        payload, signature = token.split(".", 1)
        if not hmac.compare_digest(signature, _sign(payload, settings)):
            return None
        data = json.loads(_base64url_decode(payload))
        if not isinstance(data, dict) or int(data.get("exp", 0)) < int(time.time()):
            return None
        email = data.get("email")
        if not isinstance(email, str) or not email:
            return None
        return email.lower()
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def app_login_credentials(settings: Settings) -> dict[str, str]:
    raw = settings.app_login_credentials or ""
    credentials: dict[str, str] = {}
    for pair in raw.split(","):
        if not pair.strip():
            continue
        email, separator, password = pair.partition(":")
        if not separator or not email.strip() or not password:
            continue
        credentials[email.strip().lower()] = password
    return credentials


def authenticate_app_login(email: str, password: str, settings: Settings) -> str:
    expected = app_login_credentials(settings).get(email.lower())
    if expected is None or not hmac.compare_digest(expected, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if email.lower() not in settings.authorized_email_set:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not authorized")
    return email.lower()


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
    taiga_session: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    cf_access_jwt_assertion: str | None = Header(
        default=None,
        alias="Cf-Access-Jwt-Assertion",
    ),
    settings: Settings = settings_dependency,
    session: Session = session_dependency,
) -> Principal:
    if settings.app_env == "local":
        email = local_email_from_headers(authorization, x_local_user, settings)
        return principal_for_email(session, email)
    production_email = email_from_session_token(taiga_session, settings) if taiga_session else None
    if production_email is None:
        try:
            production_email = verify_cloudflare_access(cf_access_jwt_assertion, settings).email
        except AccessVerificationError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": str(exc), "message": "Authentication required"},
            ) from exc
    return principal_for_email(session, production_email)


def principal_for_email(session: Session, email: str) -> Principal:
    row = (
        session.execute(
            text(
                """
                SELECT id, cognito_sub, display_name, role::text, status::text, timezone
                FROM users
                WHERE cognito_sub = :email AND deleted_at IS NULL
                """
            ),
            {"email": email.lower()},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user")
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
