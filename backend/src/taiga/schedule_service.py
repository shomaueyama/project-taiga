from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, date, datetime
from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.orm import Session

from taiga.api_schemas import (
    CreateScheduleItemRequest,
    ScheduleDayResponse,
    ScheduleItemResponse,
    SchedulePage,
    ScheduleSummary,
    UpdateScheduleItemRequest,
)
from taiga.auth import Principal
from taiga.authorization import require_admin
from taiga.curriculum_seed import json_text, stable_uuid
from taiga.errors import NotFoundError
from taiga.schedule_domain import (
    ScheduleDisplayStatus,
    ScheduleStateInput,
    calculate_schedule_state,
    representative_status,
    today_jst,
)

PISCINE_START = date(2027, 3, 1)
SCHEDULE_ITEM_TYPES = {
    "assignment",
    "exam",
    "application",
    "orientation",
    "housing",
    "finance",
    "travel",
    "piscine",
    "milestone",
    "rest",
    "review",
}


def _learner_id_for_schedule(session: Session, principal: Principal) -> Any:
    if principal.role == "learner":
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


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _rows(
    session: Session,
    principal: Principal,
    from_date: date,
    to_date: date,
) -> list[Any]:
    learner_id = _learner_id_for_schedule(session, principal)
    rows = (
        session.execute(
            text(
                """
                WITH latest_submission AS (
                  SELECT DISTINCT ON (assignment_id)
                         assignment_id, status::text AS latest_submission_status
                  FROM submissions
                  WHERE learner_id = :learner_id
                  ORDER BY assignment_id, submission_version DESC
                )
                SELECT s.id, s.schedule_key, s.learner_id, s.scheduled_date, s.start_at,
                       s.end_at, s.title, s.description, s.item_type, s.assignment_id,
                       s.milestone_key, s.status_override, s.priority, s.due_at,
                       s.source_url, s.is_required, s.metadata_json,
                       a.status::text AS assignment_status,
                       latest_submission.latest_submission_status
                FROM schedule_items s
                LEFT JOIN task_assignments a ON a.id = s.assignment_id
                LEFT JOIN latest_submission ON latest_submission.assignment_id = s.assignment_id
                WHERE s.learner_id = :learner_id
                  AND s.scheduled_date BETWEEN :from_date AND :to_date
                ORDER BY s.scheduled_date, s.priority, s.title
                """
            ),
            {"learner_id": learner_id, "from_date": from_date, "to_date": to_date},
        )
        .mappings()
        .all()
    )
    return list(rows)


def _item(row: Any, now: datetime | None = None) -> ScheduleItemResponse:
    state = calculate_schedule_state(
        ScheduleStateInput(
            scheduled_date=row["scheduled_date"],
            item_type=row["item_type"],
            due_at=row["due_at"],
            status_override=row["status_override"],
            assignment_status=row["assignment_status"],
            latest_submission_status=row["latest_submission_status"],
        ),
        now=now,
    )
    assignment_id = row["assignment_id"]
    return ScheduleItemResponse(
        id=row["id"],
        scheduleKey=row["schedule_key"],
        date=row["scheduled_date"].isoformat(),
        startAt=row["start_at"].isoformat() if row["start_at"] else None,
        endAt=row["end_at"].isoformat() if row["end_at"] else None,
        title=row["title"],
        description=row["description"],
        itemType=row["item_type"],
        assignmentId=assignment_id,
        milestoneKey=row["milestone_key"],
        priority=row["priority"],
        dueAt=row["due_at"].isoformat() if row["due_at"] else None,
        sourceUrl=row["source_url"],
        isRequired=row["is_required"],
        displayStatus=state.display_status,
        isOverdue=state.is_overdue,
        overdueDays=state.overdue_days,
        isToday=state.is_today,
        assignmentUrl=f"/assignments/{assignment_id}" if assignment_id else None,
        metadata=dict(row["metadata_json"]),
    )


def get_schedule(
    session: Session,
    principal: Principal,
    from_date: date,
    to_date: date,
    *,
    now: datetime | None = None,
) -> SchedulePage:
    if to_date < from_date:
        raise ValueError("to date must be on or after from date")
    grouped: dict[date, list[ScheduleItemResponse]] = defaultdict(list)
    for row in _rows(session, principal, from_date, to_date):
        grouped[row["scheduled_date"]].append(_item(row, now))
    days: list[ScheduleDayResponse] = []
    current_today = today_jst(now)
    cursor = from_date
    while cursor <= to_date:
        items = grouped[cursor]
        days.append(
            ScheduleDayResponse(
                date=cursor.isoformat(),
                representativeStatus=representative_status(
                    [cast(ScheduleDisplayStatus, item.displayStatus) for item in items]
                ),
                isToday=cursor == current_today,
                items=items,
            )
        )
        cursor = date.fromordinal(cursor.toordinal() + 1)
    return SchedulePage(
        fromDate=from_date.isoformat(),
        toDate=to_date.isoformat(),
        days=days,
    )


def get_schedule_day(
    session: Session,
    principal: Principal,
    selected_date: date,
    *,
    now: datetime | None = None,
) -> ScheduleDayResponse:
    return get_schedule(session, principal, selected_date, selected_date, now=now).days[0]


def get_schedule_summary(
    session: Session,
    principal: Principal,
    *,
    now: datetime | None = None,
) -> ScheduleSummary:
    current_today = today_jst(now)
    page = get_schedule(
        session,
        principal,
        current_today,
        date(2027, 4, 14),
        now=now,
    )
    today_items = page.days[0].items if page.days else []
    all_items = [item for day in page.days for item in day.items]
    next_important = next(
        (
            item
            for item in all_items
            if item.isRequired
            and item.itemType
            in {"exam", "application", "orientation", "housing", "finance", "travel", "piscine"}
            and item.displayStatus != "cancelled"
        ),
        None,
    )
    days_until_piscine = (PISCINE_START - current_today).days
    return ScheduleSummary(
        todayCount=len(today_items),
        learnerOverdueCount=sum(1 for item in all_items if item.displayStatus == "learner_overdue"),
        reviewWaitingCount=sum(1 for item in all_items if item.displayStatus == "review_waiting"),
        nextImportantDate=next_important.date if next_important else None,
        nextImportantTitle=next_important.title if next_important else None,
        daysUntilPiscine=days_until_piscine,
    )


def seed_schedule_for_local(session: Session) -> int:
    from taiga.schedule_seed import seed_schedule_items

    return seed_schedule_items(session)


def _created_or_updated_item(
    session: Session,
    principal: Principal,
    item_id: uuid.UUID,
) -> ScheduleItemResponse:
    row = (
        session.execute(
            text(
                """
                WITH latest_submission AS (
                  SELECT DISTINCT ON (assignment_id)
                         assignment_id, status::text AS latest_submission_status
                  FROM submissions
                  WHERE learner_id = :learner_id
                  ORDER BY assignment_id, submission_version DESC
                )
                SELECT s.id, s.schedule_key, s.learner_id, s.scheduled_date, s.start_at,
                       s.end_at, s.title, s.description, s.item_type, s.assignment_id,
                       s.milestone_key, s.status_override, s.priority, s.due_at,
                       s.source_url, s.is_required, s.metadata_json,
                       a.status::text AS assignment_status,
                       latest_submission.latest_submission_status
                FROM schedule_items s
                LEFT JOIN task_assignments a ON a.id = s.assignment_id
                LEFT JOIN latest_submission ON latest_submission.assignment_id = s.assignment_id
                WHERE s.id = :id AND s.learner_id = :learner_id
                """
            ),
            {"id": item_id, "learner_id": _learner_id_for_schedule(session, principal)},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise NotFoundError("Schedule item not found", code="schedule_item_not_found")
    return _item(row)


def create_schedule_item(
    session: Session,
    principal: Principal,
    request: CreateScheduleItemRequest,
) -> ScheduleItemResponse:
    require_admin(principal)
    learner_id = _learner_id_for_schedule(session, principal)
    scheduled_date = date.fromisoformat(request.date)
    schedule_key = f"admin-{scheduled_date.isoformat()}-{uuid.uuid4()}"
    item_id = stable_uuid("schedule-item", schedule_key)
    session.execute(
        text(
            """
            INSERT INTO schedule_items (
                id, schedule_key, learner_id, scheduled_date, title, description,
                item_type, assignment_id, milestone_key, status_override, priority,
                due_at, source_url, is_required, metadata_json
            )
            VALUES (
                :id, :schedule_key, :learner_id, :scheduled_date, :title, :description,
                :item_type, :assignment_id, :milestone_key, :status_override, :priority,
                :due_at, :source_url, :is_required, CAST(:metadata_json AS jsonb)
            )
            """
        ),
        {
            "id": item_id,
            "schedule_key": schedule_key,
            "learner_id": learner_id,
            "scheduled_date": scheduled_date,
            "title": request.title,
            "description": request.description,
            "item_type": request.itemType,
            "assignment_id": request.assignmentId,
            "milestone_key": request.milestoneKey,
            "status_override": request.statusOverride,
            "priority": request.priority,
            "due_at": _parse_datetime(request.dueAt),
            "source_url": request.sourceUrl,
            "is_required": request.isRequired,
            "metadata_json": json_text(request.metadata),
        },
    )
    return _created_or_updated_item(session, principal, item_id)


def update_schedule_item(
    session: Session,
    principal: Principal,
    item_id: uuid.UUID,
    request: UpdateScheduleItemRequest,
) -> ScheduleItemResponse:
    require_admin(principal)
    current = (
        session.execute(
            text(
                """
                SELECT scheduled_date, title, description, item_type, assignment_id,
                       milestone_key, status_override, priority, due_at, source_url,
                       is_required, metadata_json
                FROM schedule_items
                WHERE id = :id AND learner_id = :learner_id
                """
            ),
            {"id": item_id, "learner_id": _learner_id_for_schedule(session, principal)},
        )
        .mappings()
        .first()
    )
    if current is None:
        raise NotFoundError("Schedule item not found", code="schedule_item_not_found")
    fields = request.model_fields_set
    values = {
        "scheduled_date": date.fromisoformat(request.date)
        if "date" in fields and request.date is not None
        else current["scheduled_date"],
        "title": request.title if "title" in fields else current["title"],
        "description": request.description
        if "description" in fields
        else current["description"],
        "item_type": request.itemType if "itemType" in fields else current["item_type"],
        "assignment_id": request.assignmentId
        if "assignmentId" in fields
        else current["assignment_id"],
        "milestone_key": request.milestoneKey
        if "milestoneKey" in fields
        else current["milestone_key"],
        "status_override": request.statusOverride
        if "statusOverride" in fields
        else current["status_override"],
        "priority": request.priority if "priority" in fields else current["priority"],
        "due_at": _parse_datetime(request.dueAt) if "dueAt" in fields else current["due_at"],
        "source_url": request.sourceUrl if "sourceUrl" in fields else current["source_url"],
        "is_required": request.isRequired
        if "isRequired" in fields
        else current["is_required"],
        "metadata_json": json_text(request.metadata)
        if "metadata" in fields and request.metadata is not None
        else json_text(current["metadata_json"]),
    }
    row = (
        session.execute(
            text(
                """
                UPDATE schedule_items
                SET scheduled_date = :scheduled_date,
                    title = :title,
                    description = :description,
                    item_type = :item_type,
                    assignment_id = :assignment_id,
                    milestone_key = :milestone_key,
                    status_override = :status_override,
                    priority = :priority,
                    due_at = :due_at,
                    source_url = :source_url,
                    is_required = :is_required,
                    metadata_json = CAST(:metadata_json AS jsonb),
                    updated_at = now()
                WHERE id = :id AND learner_id = :learner_id
                RETURNING id
                """
            ),
            {
                "id": item_id,
                "learner_id": _learner_id_for_schedule(session, principal),
                **values,
            },
        )
        .mappings()
        .first()
    )
    if row is None:
        raise NotFoundError("Schedule item not found", code="schedule_item_not_found")
    return _created_or_updated_item(session, principal, item_id)


def delete_schedule_item(session: Session, principal: Principal, item_id: uuid.UUID) -> None:
    require_admin(principal)
    row = (
        session.execute(
            text(
                """
                DELETE FROM schedule_items
                WHERE id = :id AND learner_id = :learner_id
                RETURNING id
                """
            ),
            {"id": item_id, "learner_id": _learner_id_for_schedule(session, principal)},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise NotFoundError("Schedule item not found", code="schedule_item_not_found")
