from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserProfile(BaseModel):
    id: UUID
    displayName: str
    role: Literal["learner", "reviewer", "admin"]
    status: str
    timezone: str


class AssignmentSummary(BaseModel):
    id: UUID
    stableCode: str
    title: str
    scheduledDate: str
    status: str


class SubmissionSnapshot(BaseModel):
    id: UUID
    version: int
    status: str
    createdAt: str
    model_config = ConfigDict(extra="allow")


class AssignmentDetail(BaseModel):
    assignment: AssignmentSummary
    instructions: list[str]
    submissionSpec: dict[str, Any]
    submissions: list[SubmissionSnapshot]


class AssignmentPage(BaseModel):
    items: list[AssignmentSummary]
    nextCursor: str | None


class ExamSummary(BaseModel):
    id: UUID
    stableCode: str
    scheduledAt: str
    status: str = "ready"


class Dashboard(BaseModel):
    today: list[AssignmentSummary]
    overdue: list[AssignmentSummary]
    nextExam: ExamSummary | None
    rank: str | None
    capabilityGaps: list[str]


class CapabilityProgress(BaseModel):
    code: str
    level: int


class Progress(BaseModel):
    completedWeeks: int
    capabilities: list[CapabilityProgress]
    rank: str | None
