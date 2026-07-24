from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import text

from alembic import command
from taiga.config import get_settings
from taiga.curriculum_seed import seed
from taiga.infrastructure.database import SessionLocal


def migrate() -> None:
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    command.upgrade(config, "head")


def scalar(query: str) -> int:
    with SessionLocal() as session:
        return int(session.execute(text(query)).scalar_one())


def test_realistic_local_seed_is_idempotent() -> None:
    settings = get_settings()
    assert settings.app_env == "local"
    if not (Path(settings.curriculum_source_dir) / "weeks.json").exists():
        pytest.skip("Design curriculum is not present in this checkout")

    migrate()
    seed()
    seed()

    with SessionLocal() as session:
        users = [
            dict(row)
            for row in (
                session.execute(
                    text(
                        """
                        SELECT cognito_sub, display_name, role::text, status::text
                        FROM users
                        WHERE cognito_sub IN ('admin@example.local', 'taiga@example.local')
                        ORDER BY cognito_sub
                        """
                    )
                )
                .mappings()
                .all()
            )
        ]
        assert users == [
            {
                "cognito_sub": "admin@example.local",
                "display_name": "上山 捷馬",
                "role": "admin",
                "status": "active",
            },
            {
                "cognito_sub": "taiga@example.local",
                "display_name": "上山 虎雅",
                "role": "learner",
                "status": "active",
            },
        ]

        assignment_statuses = set(
            session.execute(
                text(
                    """
                    SELECT DISTINCT a.status::text
                    FROM task_assignments a
                    JOIN users u ON u.id = a.learner_id
                    WHERE u.cognito_sub = 'taiga@example.local'
                    """
                )
            ).scalars()
        )
        assert {
            "not_started",
            "in_progress",
            "awaiting_submission",
            "available",
            "completed",
            "missed",
        }.issubset(assignment_statuses)

        runner_statuses = set(
            session.execute(text("SELECT DISTINCT status::text FROM runner_jobs")).scalars()
        )
        assert {"queued", "claimed", "succeeded", "failed"}.issubset(runner_statuses)

        exam_statuses = set(
            session.execute(text("SELECT DISTINCT status::text FROM exam_attempts")).scalars()
        )
        assert {"ready", "in_progress", "oral_pending", "passed", "failed", "expired"}.issubset(
            exam_statuses
        )

    assert scalar("SELECT count(*) FROM weeks") == 28
    assert scalar("SELECT count(*) FROM task_templates") == 196
    assert scalar("SELECT count(*) FROM task_assignments") == 196
    assert scalar("SELECT count(*) FROM exams") == 28
    assert scalar("SELECT count(*) FROM exam_variants") == 56
