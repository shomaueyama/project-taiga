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


class CreateUploadRequest(BaseModel):
    originalName: str
    mediaType: str
    sizeBytes: int
    sha256: str


class CompleteUploadRequest(BaseModel):
    sizeBytes: int
    sha256: str


class UploadSessionResponse(BaseModel):
    id: UUID
    status: str
    uploadUrl: str | None = None
    expiresAt: str
    rejectionCode: str | None = None


class CreateSubmissionRequest(BaseModel):
    sourceType: Literal["public_git", "zip_upload", "file_upload"]
    repositoryUrl: str | None = None
    commitHash: str | None = None
    uploadIds: list[UUID]


class SubmissionResponse(BaseModel):
    id: UUID
    assignmentId: UUID
    version: int
    status: str
    createdAt: str


class SubmissionDetail(BaseModel):
    submission: SubmissionResponse
    artifacts: list[dict[str, Any]]
    sanitizedResult: dict[str, Any] | None = None


class CreateReviewRequest(BaseModel):
    result: Literal["approved", "needs_revision"]
    rubric: dict[str, Any]
    comment: str


class ReviewResponse(BaseModel):
    id: UUID
    result: str
    comment: str
    createdAt: str


class ReviewQueuePage(BaseModel):
    items: list[SubmissionResponse]
    nextCursor: str | None


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
