from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import text
from test_production_users import launch_specs, production_settings

from alembic import command
from taiga.curriculum_seed import seed_curriculum
from taiga.infrastructure.database import SessionLocal
from taiga.production_seed import load_production_users
from taiga.production_users import bootstrap_production_users
from taiga.schedule_seed import seed_schedule_items

CURRICULUM_DIR = Path(__file__).parents[3] / "design/taiga-42-v4.0-implementation-pack/curriculum"


def migrate() -> None:
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    command.upgrade(config, "head")


def test_production_seed_uses_approved_users_without_local_demo_state(tmp_path: Path) -> None:
    if not (CURRICULUM_DIR / "weeks.json").exists():
        pytest.skip("Design curriculum is not present in this checkout")

    migrate()
    settings = production_settings()
    with SessionLocal.begin() as session:
        bootstrap_production_users(session, settings, launch_specs(), apply=True)
        users = load_production_users(session, settings)
        seed_curriculum(
            session,
            CURRICULUM_DIR,
            tmp_path,
            users=users,
            include_local_demo_state=False,
        )
        seed_schedule_items(session, learner_email="taiga-albatross@softbank.ne.jp")
        seed_schedule_items(session, learner_email="taiga-albatross@softbank.ne.jp")

    with SessionLocal() as session:
        count_rows = (
            session.execute(
                text(
                    """
                    SELECT 'weeks' AS name, count(*) AS count FROM weeks
                    UNION ALL SELECT 'task_templates', count(*) FROM task_templates
                    UNION ALL
                    SELECT 'task_assignments', count(*)
                    FROM task_assignments a
                    JOIN users u ON u.id = a.learner_id
                    WHERE u.cognito_sub = 'taiga-albatross@softbank.ne.jp'
                    UNION ALL SELECT 'exams', count(*) FROM exams
                    UNION ALL SELECT 'exam_variants', count(*) FROM exam_variants
                    UNION ALL
                    SELECT 'schedule_days', count(DISTINCT scheduled_date)
                    FROM schedule_items s
                    JOIN users u ON u.id = s.learner_id
                    WHERE u.cognito_sub = 'taiga-albatross@softbank.ne.jp'
                    UNION ALL
                    SELECT 'schedule_items', count(*)
                    FROM schedule_items s
                    JOIN users u ON u.id = s.learner_id
                    WHERE u.cognito_sub = 'taiga-albatross@softbank.ne.jp'
                    UNION ALL
                    SELECT 'runner_jobs', count(*)
                    FROM runner_jobs r
                    JOIN submissions s ON s.id = r.submission_id
                    JOIN users u ON u.id = s.learner_id
                    WHERE u.cognito_sub = 'taiga-albatross@softbank.ne.jp'
                    UNION ALL
                    SELECT 'exam_attempts', count(*)
                    FROM exam_attempts e
                    JOIN users u ON u.id = e.learner_id
                    WHERE u.cognito_sub = 'taiga-albatross@softbank.ne.jp'
                    """
                )
            )
            .mappings()
            .all()
        )
        counts: dict[str, int] = {str(row["name"]): int(row["count"]) for row in count_rows}
        assert counts["weeks"] == 28
        assert counts["task_templates"] == 196
        assert counts["task_assignments"] == 196
        assert counts["exams"] == 28
        assert counts["exam_variants"] == 56
        assert counts["schedule_days"] >= 243
        assert counts["schedule_items"] >= 243
        assert counts["runner_jobs"] == 0
        assert counts["exam_attempts"] == 0

        flag_rows = (
            session.execute(text("SELECT key, enabled FROM feature_flags ORDER BY key"))
            .mappings()
            .all()
        )
        flags: dict[str, bool] = {str(row["key"]): bool(row["enabled"]) for row in flag_rows}
        assert flags == {"exam.enabled": False, "runner.enabled": False}
