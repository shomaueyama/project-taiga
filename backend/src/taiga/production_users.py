from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from taiga.config import Settings, get_settings
from taiga.infrastructure.database import SessionLocal

PRODUCTION_USER_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "project-taiga.production-users")
VALID_ROLES = {"learner", "reviewer", "admin"}


@dataclass(frozen=True)
class ProductionUserSpec:
    email: str
    display_name: str
    role: str
    timezone: str


@dataclass(frozen=True)
class BootstrapResult:
    planned: tuple[ProductionUserSpec, ...]
    applied: bool


def stable_production_user_id(email: str) -> uuid.UUID:
    return uuid.uuid5(PRODUCTION_USER_NAMESPACE, email.lower())


def load_specs(path: Path) -> tuple[ProductionUserSpec, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Production user bootstrap file must contain a JSON array")
    specs: list[ProductionUserSpec] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Each production user entry must be an object")
        specs.append(
            ProductionUserSpec(
                email=_required_string(item, "email").lower(),
                display_name=_required_string(item, "displayName"),
                role=_required_string(item, "role"),
                timezone=_required_string(item, "timezone"),
            )
        )
    return tuple(specs)


def validate_specs(settings: Settings, specs: tuple[ProductionUserSpec, ...]) -> None:
    if len(specs) < 2:
        raise ValueError("At least two production users must be provided")
    emails = [spec.email for spec in specs]
    if len(set(emails)) != len(emails):
        raise ValueError("Production user emails must be unique")
    if set(emails) != settings.authorized_email_set:
        raise ValueError("Production user emails must match AUTHORIZED_USER_EMAILS exactly")
    roles = {spec.role for spec in specs}
    if "admin" not in roles or "learner" not in roles:
        raise ValueError("Production users must include at least one admin and one learner")
    for spec in specs:
        if spec.role not in VALID_ROLES:
            raise ValueError(f"Unsupported production user role: {spec.role}")
        if not spec.display_name.strip():
            raise ValueError("Production user display names must not be blank")
        if not spec.timezone.strip():
            raise ValueError("Production user timezones must not be blank")


def bootstrap_production_users(
    session: Session,
    settings: Settings,
    specs: tuple[ProductionUserSpec, ...],
    *,
    apply: bool = False,
) -> BootstrapResult:
    validate_specs(settings, specs)
    if apply:
        if settings.app_env != "production":
            raise ValueError("Production users can only be applied when APP_ENV=production")
        for spec in specs:
            session.execute(
                text(
                    """
                    INSERT INTO users (
                        id, cognito_sub, display_name, role, status, timezone
                    )
                    VALUES (
                        :id, :email, :display_name, :role, 'active', :timezone
                    )
                    ON CONFLICT (cognito_sub) DO UPDATE
                    SET display_name = EXCLUDED.display_name,
                        role = EXCLUDED.role,
                        status = 'active',
                        timezone = EXCLUDED.timezone,
                        deleted_at = NULL,
                        version = users.version + 1,
                        updated_at = now()
                    """
                ),
                {
                    "id": stable_production_user_id(spec.email),
                    "email": spec.email,
                    "display_name": spec.display_name,
                    "role": spec.role,
                    "timezone": spec.timezone,
                },
            )
    return BootstrapResult(planned=specs, applied=apply)


def _required_string(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Production user field is required: {key}")
    return value.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate or apply production user bootstrap data.",
    )
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Path to owner-approved JSON file.",
    )
    parser.add_argument("--apply", action="store_true", help="Apply the idempotent user upsert.")
    args = parser.parse_args()

    settings = get_settings()
    specs = load_specs(args.file)
    with SessionLocal.begin() as session:
        result = bootstrap_production_users(session, settings, specs, apply=args.apply)
    print(json.dumps(_result_payload(result), ensure_ascii=False, sort_keys=True))


def _result_payload(result: BootstrapResult) -> dict[str, object]:
    return {
        "applied": result.applied,
        "users": [
            {
                "email": spec.email,
                "displayName": spec.display_name,
                "role": spec.role,
                "timezone": spec.timezone,
            }
            for spec in result.planned
        ],
    }


if __name__ == "__main__":
    main()
