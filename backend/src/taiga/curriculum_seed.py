from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, time
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from taiga.config import get_settings
from taiga.infrastructure.database import SessionLocal

NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "project-taiga.local-mvp")
CURRICULUM_VERSION = "v4.0-local-mvp"


def stable_uuid(scope: str, stable_id: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"{scope}:{stable_id}")


def load_json(source_dir: Path, name: str) -> list[dict[str, Any]]:
    data = json.loads((source_dir / f"{name}.json").read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{name}.json must contain a list")
    return data


def canonical_hash(source_dir: Path) -> str:
    digest = hashlib.sha256()
    for name in (
        "weeks",
        "task_templates",
        "task_assignments",
        "exams",
        "exam_variants",
        "exam_hidden_tests",
    ):
        digest.update((source_dir / f"{name}.json").read_bytes())
    return digest.hexdigest()


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def seed_local_users(session: Session) -> dict[str, uuid.UUID]:
    users = {
        "taiga": ("taiga@example.local", "Taiga Learner", "learner"),
        "reviewer": ("reviewer@example.local", "Local Reviewer", "reviewer"),
        "admin": ("admin@example.local", "Local Admin", "admin"),
    }
    result: dict[str, uuid.UUID] = {}
    for ref, (email, display_name, role) in users.items():
        user_id = stable_uuid("user", email)
        session.execute(
            text(
                """
                INSERT INTO users (id, cognito_sub, display_name, role, status)
                VALUES (:id, :cognito_sub, :display_name, :role, 'active')
                ON CONFLICT (cognito_sub) DO UPDATE
                SET display_name = EXCLUDED.display_name,
                    role = EXCLUDED.role,
                    status = 'active',
                    updated_at = now()
                """
            ),
            {
                "id": user_id,
                "cognito_sub": email,
                "display_name": display_name,
                "role": role,
            },
        )
        result[ref] = user_id
    return result


def seed_curriculum(session: Session, source_dir: Path, storage_root: Path) -> None:
    content_hash = canonical_hash(source_dir)
    curriculum_version_id = stable_uuid("curriculum-version", CURRICULUM_VERSION)
    session.execute(
        text(
            """
            INSERT INTO curriculum_versions (id, version, status, content_hash, published_at, locked_at)
            VALUES (:id, :version, 'published', :content_hash, now(), now())
            ON CONFLICT (version) DO UPDATE
            SET status = 'published',
                content_hash = EXCLUDED.content_hash,
                published_at = COALESCE(curriculum_versions.published_at, now()),
                locked_at = COALESCE(curriculum_versions.locked_at, now())
            """
        ),
        {"id": curriculum_version_id, "version": CURRICULUM_VERSION, "content_hash": content_hash},
    )

    users = seed_local_users(session)
    weeks = load_json(source_dir, "weeks")
    task_templates = load_json(source_dir, "task_templates")
    task_assignments = load_json(source_dir, "task_assignments")
    exams = load_json(source_dir, "exams")
    exam_variants = load_json(source_dir, "exam_variants")
    hidden_tests = load_json(source_dir, "exam_hidden_tests")

    week_ids: dict[str, uuid.UUID] = {}
    for week in weeks:
        week_id = stable_uuid("week", week["id"])
        week_ids[week["id"]] = week_id
        session.execute(
            text(
                """
                INSERT INTO weeks (id, curriculum_version_id, stable_code, number, title, goal, start_date, end_date)
                VALUES (:id, :curriculum_version_id, :stable_code, :number, :title, :goal, :start_date, :end_date)
                ON CONFLICT (curriculum_version_id, stable_code) DO UPDATE
                SET number = EXCLUDED.number,
                    title = EXCLUDED.title,
                    goal = EXCLUDED.goal,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date
                """
            ),
            {
                "id": week_id,
                "curriculum_version_id": curriculum_version_id,
                "stable_code": week["id"],
                "number": week["number"],
                "title": week["title"],
                "goal": week["goal"],
                "start_date": week["startDate"],
                "end_date": week["endDate"],
            },
        )

    task_ids: dict[str, uuid.UUID] = {}
    for task in task_templates:
        task_id = stable_uuid("task-template", task["id"])
        task_ids[task["id"]] = task_id
        instructions = {
            key: task.get(key)
            for key in (
                "requirements",
                "approvalCriteria",
                "materials",
                "aiAllowed",
                "randomUnseenComponent",
                "cumulativeScope",
                "submissionPolicy",
            )
        }
        session.execute(
            text(
                """
                INSERT INTO task_templates (
                    id, curriculum_version_id, week_id, stable_code, title, goal,
                    instructions_json, submission_spec_json, oral_check_required
                )
                VALUES (
                    :id, :curriculum_version_id, :week_id, :stable_code, :title, :goal,
                    CAST(:instructions_json AS jsonb), CAST(:submission_spec_json AS jsonb),
                    :oral_check_required
                )
                ON CONFLICT (curriculum_version_id, stable_code) DO UPDATE
                SET week_id = EXCLUDED.week_id,
                    title = EXCLUDED.title,
                    goal = EXCLUDED.goal,
                    instructions_json = EXCLUDED.instructions_json,
                    submission_spec_json = EXCLUDED.submission_spec_json,
                    oral_check_required = EXCLUDED.oral_check_required
                """
            ),
            {
                "id": task_id,
                "curriculum_version_id": curriculum_version_id,
                "week_id": week_ids[task["weekId"]],
                "stable_code": task["id"],
                "title": task["title"],
                "goal": task["goal"],
                "instructions_json": json_text(instructions),
                "submission_spec_json": json_text(task["submissionSpec"]),
                "oral_check_required": task["oralCheckRequired"],
            },
        )

    for assignment in task_assignments:
        learner_id = users[assignment["userRef"]]
        assignment_id = stable_uuid("task-assignment", assignment["id"])
        session.execute(
            text(
                """
                INSERT INTO task_assignments (
                    id, task_template_id, learner_id, scheduled_date, required,
                    activation_json, status
                )
                VALUES (
                    :id, :task_template_id, :learner_id, :scheduled_date, :required,
                    CAST(:activation_json AS jsonb), :status
                )
                ON CONFLICT (task_template_id, learner_id) DO UPDATE
                SET scheduled_date = EXCLUDED.scheduled_date,
                    required = EXCLUDED.required,
                    activation_json = EXCLUDED.activation_json,
                    status = EXCLUDED.status,
                    updated_at = now()
                """
            ),
            {
                "id": assignment_id,
                "task_template_id": task_ids[assignment["taskId"]],
                "learner_id": learner_id,
                "scheduled_date": assignment["scheduledDate"],
                "required": assignment["required"],
                "activation_json": json_text(assignment["activation"]),
                "status": assignment["status"],
            },
        )

    exam_ids: dict[str, uuid.UUID] = {}
    for exam in exams:
        exam_id = stable_uuid("exam", exam["id"])
        exam_ids[exam["id"]] = exam_id
        scheduled_at = datetime.combine(
            datetime.fromisoformat(exam["scheduledDate"]).date(),
            time(hour=9),
            tzinfo=UTC,
        )
        session.execute(
            text(
                """
                INSERT INTO exams (
                    id, curriculum_version_id, week_id, stable_code, blueprint_json, scheduled_at
                )
                VALUES (
                    :id, :curriculum_version_id, :week_id, :stable_code,
                    CAST(:blueprint_json AS jsonb), :scheduled_at
                )
                ON CONFLICT (curriculum_version_id, stable_code) DO UPDATE
                SET week_id = EXCLUDED.week_id,
                    blueprint_json = EXCLUDED.blueprint_json,
                    scheduled_at = EXCLUDED.scheduled_at
                """
            ),
            {
                "id": exam_id,
                "curriculum_version_id": curriculum_version_id,
                "week_id": week_ids[exam["weekId"]],
                "stable_code": exam["id"],
                "blueprint_json": json_text(exam),
                "scheduled_at": scheduled_at,
            },
        )

    hidden_by_variant = {item["examVariantId"]: item for item in hidden_tests}
    hidden_root = storage_root / "hidden-tests"
    hidden_root.mkdir(parents=True, exist_ok=True)

    for variant in exam_variants:
        hidden = hidden_by_variant[variant["id"]]
        hidden_payload = json_text(hidden)
        hidden_hash = hashlib.sha256(hidden_payload.encode("utf-8")).hexdigest()
        hidden_key = f"hidden-tests/{hidden['id']}.json"
        (storage_root / hidden_key).write_text(hidden_payload + "\n", encoding="utf-8")
        public_snapshot = {
            key: value
            for key, value in variant.items()
            if key not in {"hiddenTestSetId"}
        }
        public_snapshot["hiddenTestSetRef"] = hidden["id"]
        session.execute(
            text(
                """
                INSERT INTO exam_variants (
                    id, exam_id, stable_code, version, problem_snapshot_json,
                    hidden_test_s3_key, content_hash, active
                )
                VALUES (
                    :id, :exam_id, :stable_code, 1, CAST(:problem_snapshot_json AS jsonb),
                    :hidden_test_s3_key, :content_hash, true
                )
                ON CONFLICT (exam_id, stable_code, version) DO UPDATE
                SET problem_snapshot_json = EXCLUDED.problem_snapshot_json,
                    hidden_test_s3_key = EXCLUDED.hidden_test_s3_key,
                    content_hash = EXCLUDED.content_hash,
                    active = true
                """
            ),
            {
                "id": stable_uuid("exam-variant", variant["id"]),
                "exam_id": exam_ids[variant["examId"]],
                "stable_code": variant["id"],
                "problem_snapshot_json": json_text(public_snapshot),
                "hidden_test_s3_key": hidden_key,
                "content_hash": hidden_hash,
            },
        )

    admin_id = users["admin"]
    for key, enabled in {"runner.enabled": False, "exam.enabled": False}.items():
        session.execute(
            text(
                """
                INSERT INTO feature_flags (id, key, enabled, rules_json, updated_by)
                VALUES (:id, :key, :enabled, '{}'::jsonb, :updated_by)
                ON CONFLICT (key) DO UPDATE
                SET enabled = EXCLUDED.enabled,
                    updated_by = EXCLUDED.updated_by,
                    updated_at = now()
                """
            ),
            {
                "id": stable_uuid("feature-flag", key),
                "key": key,
                "enabled": enabled,
                "updated_by": admin_id,
            },
        )


def seed() -> None:
    settings = get_settings()
    source_dir = Path(settings.curriculum_source_dir).resolve()
    storage_root = Path(settings.local_storage_root).resolve()
    with SessionLocal.begin() as session:
        seed_curriculum(session, source_dir, storage_root)


if __name__ == "__main__":
    seed()
