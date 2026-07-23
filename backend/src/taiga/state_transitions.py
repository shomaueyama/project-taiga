from __future__ import annotations

from typing import Literal, cast

from taiga.errors import InvalidTransitionError

SubmissionStatus = Literal[
    "draft",
    "submitted",
    "queued",
    "running",
    "automated_passed",
    "automated_failed",
    "runner_failed",
    "timed_out",
    "manual_review_pending",
    "needs_revision",
    "approved",
    "cancelled",
]
ReviewResult = Literal["approved", "needs_revision"]
AssignmentStatus = Literal[
    "not_started",
    "in_progress",
    "awaiting_submission",
    "available",
    "completed",
    "missed",
]
RunnerJobStatus = Literal[
    "queued",
    "claimed",
    "succeeded",
    "failed",
    "timed_out",
    "cancelled",
    "security_rejected",
]
ExamAttemptStatus = Literal[
    "scheduled",
    "ready",
    "in_progress",
    "submitted",
    "evaluating",
    "oral_pending",
    "passed",
    "failed",
    "expired",
    "cancelled",
]


def submission_status_after_creation() -> SubmissionStatus:
    return "manual_review_pending"


def review_submission_transition(
    current: str,
    result: ReviewResult,
) -> tuple[ReviewResult, AssignmentStatus]:
    if current != "manual_review_pending":
        raise InvalidTransitionError(
            "Submission is not awaiting review",
            code="submission_not_reviewable",
        )
    assignment_status: AssignmentStatus = "completed" if result == "approved" else "in_progress"
    return result, assignment_status


def runner_request_submission_status() -> SubmissionStatus:
    return "queued"


def runner_result_transition(runner_enabled: bool) -> tuple[RunnerJobStatus, SubmissionStatus]:
    if runner_enabled:
        return "security_rejected", "needs_revision"
    return "succeeded", "manual_review_pending"


def start_exam_transition(current: str) -> ExamAttemptStatus:
    if current == "ready":
        return "in_progress"
    return cast(ExamAttemptStatus, current)


def submit_exam_transition(current: str, *, late: bool) -> ExamAttemptStatus:
    if current != "in_progress":
        return cast(ExamAttemptStatus, current)
    if late:
        return "expired"
    return "oral_pending"


def oral_review_transition(current: str, *, passed: bool) -> ExamAttemptStatus:
    if current != "oral_pending":
        raise InvalidTransitionError(
            "Exam attempt is not awaiting oral review",
            code="exam_not_oral_pending",
        )
    return "passed" if passed else "failed"
