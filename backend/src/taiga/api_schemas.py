from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


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


class CreateUploadRequest(StrictRequest):
    originalName: str = Field(min_length=1, max_length=255)
    mediaType: str = Field(min_length=1, max_length=100)
    sizeBytes: int = Field(ge=0, le=50 * 1024 * 1024 + 1)
    sha256: str = Field(min_length=1, max_length=128)


class CompleteUploadRequest(StrictRequest):
    sizeBytes: int = Field(ge=0, le=50 * 1024 * 1024 + 1)
    sha256: str = Field(min_length=1, max_length=128)


class UploadSessionResponse(BaseModel):
    id: UUID
    status: str
    uploadUrl: str | None = None
    expiresAt: str
    rejectionCode: str | None = None


class CreateSubmissionRequest(StrictRequest):
    sourceType: Literal["public_git", "zip_upload", "file_upload"]
    repositoryUrl: str | None = Field(default=None, max_length=2048)
    commitHash: str | None = Field(default=None, max_length=128)
    uploadIds: list[UUID] = Field(max_length=10)


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


class RunSubmissionRequest(StrictRequest):
    reason: str | None = Field(default=None, max_length=120)


class RunnerJobResponse(BaseModel):
    id: UUID
    submissionId: UUID
    status: str
    attempt: int
    sanitizedResult: dict[str, Any] | None


class CreateReviewRequest(StrictRequest):
    result: Literal["approved", "needs_revision"]
    rubric: dict[str, Any] = Field(default_factory=dict)
    comment: str = Field(min_length=1, max_length=2000)


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
    title: str = ""
    scheduledAt: str


class ExamPage(BaseModel):
    items: list[ExamSummary]
    nextCursor: str | None


class CreateExamAttemptRequest(StrictRequest):
    pass


class ExamAttemptResponse(BaseModel):
    id: UUID
    examId: UUID
    status: str
    attemptNumber: int


class ExamAttemptDetail(BaseModel):
    attempt: ExamAttemptResponse
    variantSnapshot: dict[str, Any]
    startsAt: str | None
    deadlineAt: str | None
    submittedAt: str | None
    result: dict[str, Any] | None


class StartExamRequest(StrictRequest):
    acknowledgeRules: bool = True


class SubmitExamRequest(StrictRequest):
    submissionId: UUID | None = None
    answers: dict[str, Any] = Field(default_factory=dict)


class OralAnswer(StrictRequest):
    question: str = Field(min_length=1, max_length=500)
    assessment: str = Field(min_length=1, max_length=500)
    note: str | None = Field(default=None, max_length=1000)


class OralReviewRequest(StrictRequest):
    passed: bool
    answers: list[OralAnswer] = Field(max_length=50)


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


class PageUserProfile(BaseModel):
    items: list[UserProfile]
    nextCursor: str | None


class InviteUserRequest(StrictRequest):
    email: str = Field(min_length=3, max_length=255)
    displayName: str = Field(min_length=1, max_length=120)
    role: Literal["learner", "reviewer", "admin"]


class FeatureFlag(BaseModel):
    key: str
    enabled: bool
    version: int


class FeatureFlagList(BaseModel):
    items: list[FeatureFlag]


class UpdateFeatureFlagRequest(StrictRequest):
    enabled: bool


class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    body: str
    readAt: str | None
    createdAt: str


class NotificationPage(BaseModel):
    items: list[NotificationResponse]
    nextCursor: str | None


class NotificationPreference(BaseModel):
    channel: str
    eventType: str
    enabled: bool


class NotificationPreferenceList(BaseModel):
    items: list[NotificationPreference]


class LearningAnalytics(BaseModel):
    learners: int
    submissions: int
    approvedSubmissions: int
    examAttempts: int
    passedExamAttempts: int


class CurriculumVersionSummary(BaseModel):
    id: UUID
    version: str
    status: str
    contentHash: str


class CurriculumVersionPage(BaseModel):
    items: list[CurriculumVersionSummary]
    nextCursor: str | None
