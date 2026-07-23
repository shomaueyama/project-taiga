from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from taiga.config import get_settings
from taiga.infrastructure.database import SessionLocal

NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "project-taiga.local-mvp")
CURRICULUM_VERSION = "v4.0-local-mvp"
DEMO_SUBMISSION_SHA = "b" * 64


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
        "taiga": ("taiga@example.local", "上山 虎雅", "learner"),
        "reviewer": ("reviewer@example.local", "Local Reviewer", "reviewer"),
        "admin": ("admin@example.local", "上山 捷馬", "admin"),
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


def _upsert_submission(
    session: Session,
    assignment_id: uuid.UUID,
    learner_id: uuid.UUID,
    version: int,
    status: str,
    original_name: str,
) -> uuid.UUID:
    submission_id = stable_uuid("demo-submission", f"{assignment_id}:{version}")
    artifact_key = f"accepted/{learner_id}/{submission_id}/{original_name}"
    session.execute(
        text(
            """
            INSERT INTO submissions (
                id, assignment_id, learner_id, submission_version, source_type,
                artifact_manifest_json, status
            )
            VALUES (
                :id, :assignment_id, :learner_id, :submission_version, 'file_upload',
                CAST(:artifact_manifest_json AS jsonb), :status
            )
            ON CONFLICT (assignment_id, submission_version) DO UPDATE
            SET status = EXCLUDED.status,
                artifact_manifest_json = EXCLUDED.artifact_manifest_json
            """
        ),
        {
            "id": submission_id,
            "assignment_id": assignment_id,
            "learner_id": learner_id,
            "submission_version": version,
            "status": status,
            "artifact_manifest_json": json_text(
                {"seed": "local-demo", "originalName": original_name}
            ),
        },
    )
    session.execute(
        text(
            """
            INSERT INTO submission_artifacts (
                id, submission_id, s3_key, sha256, media_type, size_bytes, original_name
            )
            VALUES (
                :id, :submission_id, :s3_key, :sha256, 'text/markdown', 128, :original_name
            )
            ON CONFLICT (s3_key) DO UPDATE
            SET sha256 = EXCLUDED.sha256,
                media_type = EXCLUDED.media_type,
                size_bytes = EXCLUDED.size_bytes,
                original_name = EXCLUDED.original_name
            """
        ),
        {
            "id": stable_uuid("demo-artifact", artifact_key),
            "submission_id": submission_id,
            "s3_key": artifact_key,
            "sha256": DEMO_SUBMISSION_SHA,
            "original_name": original_name,
        },
    )
    return submission_id


def seed_realistic_local_state(session: Session, users: dict[str, uuid.UUID]) -> None:
    settings = get_settings()
    if settings.app_env != "local":
        raise RuntimeError("Realistic local demo seed can only run when APP_ENV=local")

    learner_id = users["taiga"]
    admin_id = users["admin"]
    today = date.today()
    assignments = (
        session.execute(
            text(
                """
                SELECT a.id
                FROM task_assignments a
                JOIN task_templates t ON t.id = a.task_template_id
                WHERE a.learner_id = :learner_id
                ORDER BY t.stable_code
                LIMIT 12
                """
            ),
            {"learner_id": learner_id},
        )
        .scalars()
        .all()
    )
    if len(assignments) < 8:
        return

    assignment_states = [
        ("not_started", today + timedelta(days=3), True),
        ("in_progress", today, True),
        ("awaiting_submission", today - timedelta(days=1), True),
        ("available", today + timedelta(days=1), False),
        ("completed", today - timedelta(days=7), True),
        ("missed", today - timedelta(days=10), True),
        ("available", today + timedelta(days=14), True),
        ("completed", today - timedelta(days=14), False),
    ]
    for assignment_id, (status, scheduled_date, required) in zip(
        assignments, assignment_states, strict=False
    ):
        session.execute(
            text(
                """
                UPDATE task_assignments
                SET status = :status,
                    scheduled_date = :scheduled_date,
                    required = :required,
                    updated_at = now(),
                    version = version + 1
                WHERE id = :id
                """
            ),
            {
                "id": assignment_id,
                "status": status,
                "scheduled_date": scheduled_date,
                "required": required,
            },
        )

    pending_submission = _upsert_submission(
        session, assignments[2], learner_id, 1, "manual_review_pending", "python-print.md"
    )
    revision_submission_v1 = _upsert_submission(
        session, assignments[1], learner_id, 1, "needs_revision", "typing-practice-v1.md"
    )
    revision_submission_v2 = _upsert_submission(
        session, assignments[1], learner_id, 2, "manual_review_pending", "typing-practice-v2.md"
    )
    approved_submission = _upsert_submission(
        session, assignments[4], learner_id, 1, "approved", "linux-basics.md"
    )

    reviews = [
        (revision_submission_v1, "needs_revision", "Good effort. Add the requested edge cases."),
        (approved_submission, "approved", "Approved. Clear explanation and reproducible output."),
    ]
    for submission_id, review_result, comment in reviews:
        review_id = stable_uuid("demo-review", f"{submission_id}:{review_result}")
        session.execute(
            text(
                """
                INSERT INTO reviews (id, submission_id, reviewer_id, result, rubric_json, comment)
                VALUES (
                    :id, :submission_id, :reviewer_id, :result,
                    CAST(:rubric_json AS jsonb), :comment
                )
                ON CONFLICT (id) DO UPDATE
                SET result = EXCLUDED.result,
                    rubric_json = EXCLUDED.rubric_json,
                    comment = EXCLUDED.comment
                """
            ),
            {
                "id": review_id,
                "submission_id": submission_id,
                "reviewer_id": admin_id,
                "result": review_result,
                "rubric_json": json_text({"correctness": "ok", "readability": "ok"}),
                "comment": comment,
            },
        )

    runner_fixtures: list[tuple[uuid.UUID, int, str, dict[str, object] | None]] = [
        (pending_submission, 1, "queued", None),
        (revision_submission_v2, 1, "claimed", None),
        (
            approved_submission,
            1,
            "succeeded",
            {"summary": "Public tests passed.", "hiddenTests": "redacted"},
        ),
        (
            revision_submission_v1,
            1,
            "failed",
            {"summary": "Public test failed.", "hiddenTests": "redacted"},
        ),
    ]
    for submission_id, attempt, status, sanitized_result in runner_fixtures:
        now = datetime.now(UTC)
        started_at = now if status in {"claimed", "succeeded", "failed", "timed_out"} else None
        finished_at = now if status in {"succeeded", "failed", "timed_out"} else None
        session.execute(
            text(
                """
                INSERT INTO runner_jobs (
                    id, submission_id, status, attempt, image_digest,
                    security_profile_version, started_at, finished_at, sanitized_result_json
                )
                VALUES (
                    :id, :submission_id, CAST(:status AS runner_status), :attempt, 'local-demo',
                    'RUNNER_SECURITY_V1', :started_at, :finished_at,
                    CAST(:sanitized_result AS jsonb)
                )
                ON CONFLICT (submission_id, attempt) DO UPDATE
                SET status = EXCLUDED.status,
                    sanitized_result_json = EXCLUDED.sanitized_result_json,
                    version = runner_jobs.version + 1
                """
            ),
            {
                "id": stable_uuid("demo-runner-job", f"{submission_id}:{attempt}"),
                "submission_id": submission_id,
                "status": status,
                "attempt": attempt,
                "started_at": started_at,
                "finished_at": finished_at,
                "sanitized_result": json_text(sanitized_result) if sanitized_result else None,
            },
        )

    exam_rows = (
        session.execute(
            text(
                """
                SELECT e.id AS exam_id, v.id AS variant_id, v.problem_snapshot_json
                FROM exams e
                JOIN exam_variants v ON v.exam_id = e.id
                ORDER BY e.stable_code, v.stable_code
                LIMIT 7
                """
            )
        )
        .mappings()
        .all()
    )
    exam_statuses = ["ready", "in_progress", "oral_pending", "passed", "failed", "expired"]
    for index, (row, status) in enumerate(zip(exam_rows, exam_statuses, strict=False), start=1):
        now = datetime.now(UTC)
        starts_at = (
            now if status in {"in_progress", "oral_pending", "passed", "failed", "expired"} else None
        )
        deadline_at = None
        if starts_at is not None:
            if status == "expired":
                starts_at = now - timedelta(minutes=90)
                deadline_at = now - timedelta(minutes=30)
            else:
                deadline_at = now + timedelta(minutes=60)
        submitted_at = now if status in {"oral_pending", "passed", "failed"} else None
        session.execute(
            text(
                """
                INSERT INTO exam_attempts (
                    id, exam_id, exam_variant_id, learner_id, attempt_number, status,
                    variant_snapshot_json, starts_at, deadline_at, submitted_at,
                    oral_result_json, result_json
                )
                VALUES (
                    :id, :exam_id, :exam_variant_id, :learner_id, :attempt_number, :status,
                    CAST(:variant_snapshot_json AS jsonb), :starts_at, :deadline_at,
                    :submitted_at, CAST(:oral_result_json AS jsonb), CAST(:result_json AS jsonb)
                )
                ON CONFLICT (exam_id, learner_id, attempt_number) DO UPDATE
                SET status = EXCLUDED.status,
                    variant_snapshot_json = EXCLUDED.variant_snapshot_json,
                    starts_at = EXCLUDED.starts_at,
                    deadline_at = EXCLUDED.deadline_at,
                    submitted_at = EXCLUDED.submitted_at,
                    oral_result_json = EXCLUDED.oral_result_json,
                    result_json = EXCLUDED.result_json,
                    version = exam_attempts.version + 1
                """
            ),
            {
                "id": stable_uuid("demo-exam-attempt", f"{row['exam_id']}:{index}"),
                "exam_id": row["exam_id"],
                "exam_variant_id": row["variant_id"],
                "learner_id": learner_id,
                "attempt_number": index,
                "status": status,
                "variant_snapshot_json": json_text(row["problem_snapshot_json"]),
                "starts_at": starts_at,
                "deadline_at": deadline_at,
                "submitted_at": submitted_at,
                "oral_result_json": json_text({"passed": status == "passed"})
                if status in {"passed", "failed"}
                else None,
                "result_json": json_text({"seed": "local-demo", "status": status}),
            },
        )

    for capability, level in {
        "pc_basics": 2,
        "typing": 3,
        "python_basics": 2,
        "linux_basics": 1,
        "git_github": 1,
    }.items():
        session.execute(
            text(
                """
                INSERT INTO capability_achievements (
                    id, learner_id, capability_code, level, evidence_json, achieved_at
                )
                VALUES (
                    :id, :learner_id, :capability_code, :level,
                    CAST(:evidence_json AS jsonb), now()
                )
                ON CONFLICT (learner_id, capability_code, level) DO UPDATE
                SET evidence_json = EXCLUDED.evidence_json,
                    achieved_at = EXCLUDED.achieved_at
                """
            ),
            {
                "id": stable_uuid("demo-capability", f"{learner_id}:{capability}:{level}"),
                "learner_id": learner_id,
                "capability_code": capability,
                "level": level,
                "evidence_json": json_text([{"source": "local-demo-seed"}]),
            },
        )

    session.execute(
        text(
            """
            INSERT INTO rank_history (id, learner_id, rank_code, evidence_snapshot_json, achieved_at)
            VALUES (:id, :learner_id, 'local-foundation', CAST(:evidence AS jsonb), now())
            ON CONFLICT (id) DO UPDATE
            SET rank_code = EXCLUDED.rank_code,
                evidence_snapshot_json = EXCLUDED.evidence_snapshot_json,
                achieved_at = EXCLUDED.achieved_at
            """
        ),
        {
            "id": stable_uuid("demo-rank", str(learner_id)),
            "learner_id": learner_id,
            "evidence": json_text({"source": "local-demo-seed"}),
        },
    )


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
    seed_realistic_local_state(session, users)


def seed() -> None:
    settings = get_settings()
    source_dir = Path(settings.curriculum_source_dir).resolve()
    storage_root = Path(settings.local_storage_root).resolve()
    with SessionLocal.begin() as session:
        seed_curriculum(session, source_dir, storage_root)


if __name__ == "__main__":
    seed()
