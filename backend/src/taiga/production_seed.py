from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from taiga.config import Settings, get_settings
from taiga.curriculum_seed import seed_curriculum
from taiga.infrastructure.database import SessionLocal
from taiga.schedule_seed import seed_schedule_items

ADMIN_EMAIL = "shomabirdie@icloud.com"
LEARNER_EMAIL = "taiga-albatross@softbank.ne.jp"


def load_production_users(session: Session, settings: Settings) -> dict[str, UUID]:
    expected = {ADMIN_EMAIL, LEARNER_EMAIL}
    if settings.app_env != "production":
        raise RuntimeError("Production seed can only run when APP_ENV=production")
    if not expected.issubset(settings.authorized_email_set):
        raise RuntimeError("AUTHORIZED_USER_EMAILS must include the approved primary users")

    rows = (
        session.execute(
            text(
                """
                SELECT id, cognito_sub, role::text, status::text
                FROM users
                WHERE cognito_sub IN (:admin_email, :learner_email)
                """
            ),
            {"admin_email": ADMIN_EMAIL, "learner_email": LEARNER_EMAIL},
        )
        .mappings()
        .all()
    )
    by_email = {row["cognito_sub"]: row for row in rows}
    if set(by_email) != expected:
        missing = ", ".join(sorted(expected - set(by_email)))
        raise RuntimeError(f"Production users must be bootstrapped first; missing: {missing}")
    if by_email[ADMIN_EMAIL]["role"] != "admin" or by_email[ADMIN_EMAIL]["status"] != "active":
        raise RuntimeError("Approved admin user is not active admin")
    if (
        by_email[LEARNER_EMAIL]["role"] != "learner"
        or by_email[LEARNER_EMAIL]["status"] != "active"
    ):
        raise RuntimeError("Approved learner user is not active learner")

    return {
        "admin": by_email[ADMIN_EMAIL]["id"],
        "taiga": by_email[LEARNER_EMAIL]["id"],
    }


def seed() -> None:
    settings = get_settings()
    source_dir = Path(settings.curriculum_source_dir).resolve()
    storage_root = Path(settings.local_storage_root).resolve()
    with SessionLocal.begin() as session:
        users = load_production_users(session, settings)
        seed_curriculum(
            session,
            source_dir,
            storage_root,
            users=users,
            include_local_demo_state=False,
        )
        seed_schedule_items(session, learner_email=LEARNER_EMAIL)


if __name__ == "__main__":
    seed()
    print("Production curriculum seed import completed.")
