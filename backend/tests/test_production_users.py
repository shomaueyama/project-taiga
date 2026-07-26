from pathlib import Path

import pytest
from alembic.config import Config
from fastapi import HTTPException
from sqlalchemy import text

from alembic import command
from taiga.auth import authenticate_app_login, create_session_token, email_from_session_token
from taiga.config import Settings
from taiga.infrastructure.database import SessionLocal
from taiga.production_users import (
    ProductionUserSpec,
    bootstrap_production_users,
    load_specs,
)


def production_settings() -> Settings:
    return Settings(
        APP_ENV="production",
        LOCAL_AUTH_ENABLED=False,
        DATABASE_URL="postgresql+psycopg://user:pass@db.example.com/taiga?sslmode=require",
        FRONTEND_ORIGINS="https://app.taiganova.app",
        RUNNER_ENABLED=False,
        CLOUDFLARE_ACCESS_TEAM_DOMAIN="https://team.cloudflareaccess.com",
        CLOUDFLARE_ACCESS_AUD="aud",
        AUTHORIZED_USER_EMAILS="shomabirdie@icloud.com,taiga-albatross@softbank.ne.jp",
    )


def launch_specs() -> tuple[ProductionUserSpec, ProductionUserSpec]:
    return (
        ProductionUserSpec(
            email="shomabirdie@icloud.com",
            display_name="Shoma",
            role="admin",
            timezone="Asia/Tokyo",
        ),
        ProductionUserSpec(
            email="taiga-albatross@softbank.ne.jp",
            display_name="Taiga",
            role="learner",
            timezone="Asia/Tokyo",
        ),
    )


def migrate() -> None:
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    command.upgrade(config, "head")


def test_load_specs_requires_owner_supplied_json(tmp_path: Path) -> None:
    path = tmp_path / "production-users.json"
    path.write_text(
        """
        [
          {
            "email": "SHOMABIRDIE@ICLOUD.COM",
            "displayName": "Shoma",
            "role": "admin",
            "timezone": "Asia/Tokyo"
          },
          {
            "email": "taiga-albatross@softbank.ne.jp",
            "displayName": "Taiga",
            "role": "learner",
            "timezone": "Asia/Tokyo"
          }
        ]
        """,
        encoding="utf-8",
    )

    specs = load_specs(path)

    assert specs[0].email == "shomabirdie@icloud.com"
    assert specs[1].role == "learner"


def test_bootstrap_validates_exact_authorized_email_set() -> None:
    specs = (
        launch_specs()[0],
        ProductionUserSpec(
            email="other@example.com",
            display_name="Other",
            role="learner",
            timezone="Asia/Tokyo",
        ),
    )

    with pytest.raises(ValueError, match="AUTHORIZED_USER_EMAILS"):
        bootstrap_production_users(
            SessionLocal(),
            production_settings(),
            specs,
            apply=False,
        )


def test_bootstrap_requires_production_environment_for_apply() -> None:
    local_settings = Settings(
        APP_ENV="local",
        LOCAL_AUTH_ENABLED=True,
        AUTHORIZED_USER_EMAILS="shomabirdie@icloud.com,taiga-albatross@softbank.ne.jp",
    )

    with pytest.raises(ValueError, match="APP_ENV=production"):
        bootstrap_production_users(
            SessionLocal(),
            local_settings,
            launch_specs(),
            apply=True,
        )


def test_password_login_credentials_and_session_tokens() -> None:
    settings = Settings(
        APP_ENV="production",
        LOCAL_AUTH_ENABLED=False,
        DATABASE_URL="postgresql+psycopg://user:pass@db.example.com/taiga?sslmode=require",
        FRONTEND_ORIGINS="https://app.taiganova.app",
        RUNNER_ENABLED=False,
        CLOUDFLARE_ACCESS_TEAM_DOMAIN="https://team.cloudflareaccess.com",
        CLOUDFLARE_ACCESS_AUD="aud",
        AUTHORIZED_USER_EMAILS="shomabirdie@icloud.com,taiga-albatross@softbank.ne.jp",
        APP_LOGIN_CREDENTIALS="shomabirdie@icloud.com:admin-pass,taiga-albatross@softbank.ne.jp:learner-pass",
        APP_SESSION_SECRET="test-session-secret",  # noqa: S106
    )

    email = authenticate_app_login("SHOMABIRDIE@ICLOUD.COM", "admin-pass", settings)
    token = create_session_token(email, settings)

    assert email == "shomabirdie@icloud.com"
    assert email_from_session_token(token, settings) == "shomabirdie@icloud.com"
    with pytest.raises(HTTPException, match="Invalid email or password"):
        authenticate_app_login("shomabirdie@icloud.com", "wrong", settings)


def test_bootstrap_upserts_exact_two_active_users_idempotently() -> None:
    migrate()
    settings = production_settings()
    specs = launch_specs()
    with SessionLocal.begin() as session:
        bootstrap_production_users(session, settings, specs, apply=True)
        bootstrap_production_users(session, settings, specs, apply=True)

    with SessionLocal() as session:
        rows = session.execute(
            text(
                """
                SELECT cognito_sub, display_name, role::text, status::text, timezone
                FROM users
                WHERE cognito_sub IN (
                    'shomabirdie@icloud.com',
                    'taiga-albatross@softbank.ne.jp'
                )
                ORDER BY cognito_sub
                """
            )
        ).mappings().all()

    assert [row["cognito_sub"] for row in rows] == [
        "shomabirdie@icloud.com",
        "taiga-albatross@softbank.ne.jp",
    ]
    assert rows[0]["role"] == "admin"
    assert rows[0]["status"] == "active"
    assert rows[1]["role"] == "learner"
    assert rows[1]["timezone"] == "Asia/Tokyo"
