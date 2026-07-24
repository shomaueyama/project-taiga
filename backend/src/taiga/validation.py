from pathlib import Path

from sqlalchemy import inspect

from taiga.config import get_settings
from taiga.database_schema import EXPECTED_TABLES
from taiga.infrastructure.database import engine


def main() -> None:
    settings = get_settings()
    if settings.local_auth_enabled and settings.app_env != "local":
        raise SystemExit("LOCAL_AUTH_ENABLED can only be true in local APP_ENV")
    if Path(settings.curriculum_source_dir).exists():
        required = {
            "weeks.json",
            "task_templates.json",
            "task_assignments.json",
            "exams.json",
            "exam_variants.json",
            "exam_hidden_tests.json",
        }
        available = {path.name for path in Path(settings.curriculum_source_dir).iterdir()}
        missing = sorted(required - available)
        if missing:
            raise SystemExit(f"Missing curriculum sources: {', '.join(missing)}")
    try:
        table_names = set(inspect(engine).get_table_names())
    except Exception:
        table_names = set()
    if table_names:
        missing_tables = sorted(EXPECTED_TABLES - table_names)
        if missing_tables:
            raise SystemExit(f"Missing database tables: {', '.join(missing_tables)}")
    print("Validation passed.")


if __name__ == "__main__":
    main()
