from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Literal
from zoneinfo import ZoneInfo

ScheduleDisplayStatus = Literal[
    "learner_overdue",
    "review_overdue",
    "revision_requested",
    "not_submitted",
    "in_progress",
    "review_waiting",
    "not_started",
    "approved",
    "cancelled",
    "event",
]

JST = ZoneInfo("Asia/Tokyo")


@dataclass(frozen=True)
class ScheduleStateInput:
    scheduled_date: date
    item_type: str
    due_at: datetime | None
    status_override: str | None
    assignment_status: str | None
    latest_submission_status: str | None


@dataclass(frozen=True)
class ScheduleState:
    display_status: ScheduleDisplayStatus
    is_overdue: bool
    overdue_days: int
    is_today: bool


STATUS_SEVERITY: dict[str, int] = {
    "learner_overdue": 1,
    "revision_requested": 2,
    "not_submitted": 3,
    "in_progress": 4,
    "review_waiting": 5,
    "not_started": 6,
    "review_overdue": 6,
    "approved": 7,
    "cancelled": 8,
    "event": 9,
}


def today_jst(now: datetime | None = None) -> date:
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current.astimezone(JST).date()


def _effective_status(item: ScheduleStateInput) -> str:
    if item.status_override:
        return item.status_override
    if item.assignment_status == "completed" or item.latest_submission_status == "approved":
        return "approved"
    if item.assignment_status == "cancelled":
        return "cancelled"
    if item.latest_submission_status == "needs_revision":
        return "revision_requested"
    if item.latest_submission_status in {
        "submitted",
        "queued",
        "running",
        "automated_passed",
        "manual_review_pending",
    }:
        return "submitted"
    if item.assignment_status in {"in_progress", "awaiting_submission", "missed"}:
        return "in_progress"
    if item.assignment_status == "available":
        return "not_started"
    if item.assignment_status == "not_started":
        return "not_started"
    if item.item_type == "assignment":
        return "not_started"
    return "event"


def calculate_schedule_state(
    item: ScheduleStateInput,
    *,
    now: datetime | None = None,
) -> ScheduleState:
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    current_jst_date = today_jst(current)
    effective = _effective_status(item)
    due_at = item.due_at
    if due_at is not None and due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=UTC)

    completed = effective in {"approved", "cancelled"}
    is_past_due = due_at is not None and current > due_at
    overdue_days = 0
    if due_at is not None:
        due_date = due_at.astimezone(JST).date()
        overdue_days = max(0, (current_jst_date - due_date).days)
    is_overdue = is_past_due and not completed

    if effective == "cancelled":
        display_status: ScheduleDisplayStatus = "cancelled"
    elif effective == "approved":
        display_status = "approved"
    elif is_overdue and effective == "submitted":
        display_status = "review_overdue"
    elif is_overdue:
        display_status = "learner_overdue"
    elif effective == "revision_requested":
        display_status = "revision_requested"
    elif effective == "submitted":
        display_status = "review_waiting"
    elif effective == "in_progress":
        display_status = "in_progress"
    elif effective == "not_started":
        display_status = "not_started"
    else:
        display_status = "event"

    return ScheduleState(
        display_status=display_status,
        is_overdue=is_overdue,
        overdue_days=overdue_days,
        is_today=item.scheduled_date == current_jst_date,
    )


def representative_status(statuses: list[ScheduleDisplayStatus]) -> ScheduleDisplayStatus:
    if not statuses:
        return "event"
    return min(statuses, key=lambda status: STATUS_SEVERITY[status])
