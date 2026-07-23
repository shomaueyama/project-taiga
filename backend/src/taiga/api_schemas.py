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


class RunSubmissionRequest(BaseModel):
    reason: str | None = None


class RunnerJobResponse(BaseModel):
    id: UUID
    submissionId: UUID
    status: str
    attempt: int
    sanitizedResult: dict[str, Any] | None


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
    title: str = ""
    scheduledAt: str


class ExamPage(BaseModel):
    items: list[ExamSummary]
    nextCursor: str | None


class CreateExamAttemptRequest(BaseModel):
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


class StartExamRequest(BaseModel):
    acknowledgeRules: bool = True


class SubmitExamRequest(BaseModel):
    submissionId: UUID | None = None
    answers: dict[str, Any] = {}


class OralAnswer(BaseModel):
    question: str
    assessment: str
    note: str | None = None


class OralReviewRequest(BaseModel):
    passed: bool
    answers: list[OralAnswer]


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


class InviteUserRequest(BaseModel):
    email: str
    displayName: str
    role: Literal["learner", "reviewer", "admin"]


class FeatureFlag(BaseModel):
    key: str
    enabled: bool
    version: int


class FeatureFlagList(BaseModel):
    items: list[FeatureFlag]


class UpdateFeatureFlagRequest(BaseModel):
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
