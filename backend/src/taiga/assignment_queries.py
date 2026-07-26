from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from taiga.api_schemas import (
    AssignmentDetail,
    AssignmentPage,
    AssignmentSummary,
    CapabilityProgress,
    Dashboard,
    ExamSummary,
    Progress,
    SubmissionSnapshot,
)
from taiga.auth import Principal
from taiga.material_catalog import materials_for_task


def _learner_id_for_learning(session: Session, principal: Principal) -> Any:
    if principal.role == "learner":
        return principal.id
    if principal.role != "admin":
        return principal.id
    learner_id = session.execute(
        text(
            """
            SELECT id
            FROM users
            WHERE role = 'learner'
              AND status = 'active'
              AND deleted_at IS NULL
            ORDER BY
              CASE
                WHEN cognito_sub = 'taiga@example.local' THEN 0
                WHEN cognito_sub = 'taiga-albatross@softbank.ne.jp' THEN 1
                ELSE 2
              END,
              created_at
            LIMIT 1
            """
        )
    ).scalar_one_or_none()
    return learner_id or principal.id


def _summary(row: Any) -> AssignmentSummary:
    return AssignmentSummary(
        id=row["id"],
        stableCode=row["stable_code"],
        title=row["title"],
        scheduledDate=row["scheduled_date"].isoformat(),
        status=row["status"],
    )


def list_assignments(session: Session, principal: Principal, limit: int = 20) -> AssignmentPage:
    learner_id = _learner_id_for_learning(session, principal)
    rows = (
        session.execute(
            text(
                """
                SELECT a.id, t.stable_code, t.title, a.scheduled_date, a.status::text
                FROM task_assignments a
                JOIN task_templates t ON t.id = a.task_template_id
                WHERE a.learner_id = :learner_id
                ORDER BY a.scheduled_date, t.stable_code
                LIMIT :limit
                """
            ),
            {"learner_id": learner_id, "limit": limit},
        )
        .mappings()
        .all()
    )
    return AssignmentPage(items=[_summary(row) for row in rows], nextCursor=None)


def get_assignment(session: Session, principal: Principal, assignment_id: UUID) -> AssignmentDetail:
    learner_id = _learner_id_for_learning(session, principal)
    row = (
        session.execute(
            text(
                """
                SELECT a.id, t.stable_code, t.title, a.scheduled_date, a.status::text,
                       t.goal, t.instructions_json, t.submission_spec_json
                FROM task_assignments a
                JOIN task_templates t ON t.id = a.task_template_id
                WHERE a.id = :assignment_id AND a.learner_id = :learner_id
                """
            ),
            {"assignment_id": assignment_id, "learner_id": learner_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise LookupError("Assignment not found")
    submissions = (
        session.execute(
            text(
                """
                SELECT s.id, s.submission_version, s.status::text, s.created_at,
                       s.repository_url, s.commit_hash, s.artifact_manifest_json,
                       r.result::text AS review_result, r.comment AS review_comment,
                       r.created_at AS reviewed_at,
                       COALESCE(
                           (
                               SELECT array_agg(sa.original_name ORDER BY sa.original_name)
                               FROM submission_artifacts sa
                               WHERE sa.submission_id = s.id
                           ),
                           ARRAY[]::text[]
                       ) AS artifact_names,
                       COALESCE(
                           (
                               SELECT jsonb_agg(
                                   jsonb_build_object(
                                       'id', sa.id,
                                       'originalName', sa.original_name,
                                       'mediaType', sa.media_type,
                                       'sizeBytes', sa.size_bytes
                                   )
                                   ORDER BY sa.original_name
                               )
                               FROM submission_artifacts sa
                               WHERE sa.submission_id = s.id
                           ),
                           '[]'::jsonb
                       ) AS artifact_links
                FROM submissions s
                LEFT JOIN LATERAL (
                    SELECT result, comment, created_at
                    FROM reviews
                    WHERE submission_id = s.id
                    ORDER BY created_at DESC
                    LIMIT 1
                ) r ON true
                WHERE s.assignment_id = :assignment_id AND s.learner_id = :learner_id
                ORDER BY s.submission_version DESC
                """
            ),
            {"assignment_id": assignment_id, "learner_id": learner_id},
        )
        .mappings()
        .all()
    )
    instructions_json = row["instructions_json"]
    submission_spec = dict(row["submission_spec_json"])
    requirements = instructions_json.get("requirements") or []
    approval_criteria = instructions_json.get("approvalCriteria") or []
    material_ids = instructions_json.get("materials") or []
    artifacts = submission_spec.get("artifacts") or []
    return AssignmentDetail(
        assignment=_summary(row),
        goal=row["goal"],
        instructions=[str(item) for item in requirements],
        approvalCriteria=[str(item) for item in approval_criteria],
        materials=materials_for_task(material_ids, row["goal"]),
        requiredArtifacts=[
            {
                "path": str(item.get("path", "")),
                "kind": str(item.get("kind", "file")),
            }
            for item in artifacts
            if isinstance(item, dict) and item.get("path")
        ],
        submissionGuide=[
            "教材を開いて、課題の要件を上から順に実行します。",
            "提出物に書く内容、スクリーンショット、GitHub URLのいずれかを用意します。",
            "回答メモに何をしたか、結果、詰まった点を書いて提出します。",
            "提出後はレビュー待ちになります。修正依頼が出たら同じ画面から再提出します。",
        ],
        submissionSpec=submission_spec,
        submissions=[
            SubmissionSnapshot(
                id=item["id"],
                version=item["submission_version"],
                status=item["status"],
                createdAt=item["created_at"].isoformat(),
                repositoryUrl=item["repository_url"],
                commitHash=item["commit_hash"],
                submissionNote=(item["artifact_manifest_json"] or {}).get("submissionNote"),
                artifactNames=[str(name) for name in item["artifact_names"]],
                artifactLinks=list(item["artifact_links"] or []),
                reviewResult=item["review_result"],
                reviewComment=item["review_comment"],
                reviewedAt=item["reviewed_at"].isoformat() if item["reviewed_at"] else None,
            )
            for item in submissions
        ],
    )


def get_dashboard(session: Session, principal: Principal) -> Dashboard:
    page = list_assignments(session, principal, limit=7)
    next_exam_row = (
        session.execute(
            text(
                """
                SELECT id, stable_code, scheduled_at
                FROM exams
                WHERE scheduled_at >= now()
                ORDER BY scheduled_at
                LIMIT 1
                """
            )
        )
        .mappings()
        .first()
    )
    next_exam = None
    if next_exam_row is not None:
        next_exam = ExamSummary(
            id=next_exam_row["id"],
            stableCode=next_exam_row["stable_code"],
            scheduledAt=next_exam_row["scheduled_at"].isoformat(),
        )
    return Dashboard(
        today=page.items[:3],
        overdue=[],
        nextExam=next_exam,
        rank=None,
        capabilityGaps=["first_submission", "review_response", "exam_readiness"],
    )


def get_progress(session: Session, principal: Principal) -> Progress:
    learner_id = _learner_id_for_learning(session, principal)
    completed_weeks = int(
        session.execute(
            text(
                """
                SELECT count(DISTINCT w.id)
                FROM weeks w
                JOIN task_templates t ON t.week_id = w.id
                JOIN task_assignments a ON a.task_template_id = t.id
                WHERE a.learner_id = :learner_id AND a.status = 'completed'
                """
            ),
            {"learner_id": learner_id},
        ).scalar_one()
    )
    capability_rows = (
        session.execute(
            text(
                """
                SELECT capability_code, max(level) AS level
                FROM capability_achievements
                WHERE learner_id = :learner_id
                GROUP BY capability_code
                ORDER BY capability_code
                """
            ),
            {"learner_id": learner_id},
        )
        .mappings()
        .all()
    )
    rank = session.execute(
        text(
            """
            SELECT rank_code
            FROM rank_history
            WHERE learner_id = :learner_id
            ORDER BY achieved_at DESC
            LIMIT 1
            """
        ),
        {"learner_id": learner_id},
    ).scalar_one_or_none()
    return Progress(
        completedWeeks=completed_weeks,
        capabilities=[
            CapabilityProgress(code=row["capability_code"], level=row["level"])
            for row in capability_rows
        ],
        rank=rank,
    )
