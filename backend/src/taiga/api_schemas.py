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


class LoginRequest(StrictRequest):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


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
    submissionNote: str | None = Field(default=None, max_length=5000)
    uploadIds: list[UUID] = Field(max_length=10)


class SubmissionArtifactLink(BaseModel):
    id: UUID
    originalName: str
    mediaType: str
    sizeBytes: int


class SubmissionResponse(BaseModel):
    id: UUID
    assignmentId: UUID
    version: int
    status: str
    createdAt: str
    repositoryUrl: str | None = None
    commitHash: str | None = None
    submissionNote: str | None = None
    artifactNames: list[str] = Field(default_factory=list)
    artifactLinks: list[SubmissionArtifactLink] = Field(default_factory=list)


class AssignmentMaterial(BaseModel):
    id: str
    title: str
    provider: str
    type: str
    url: str | None = None
    required: bool = False
    purpose: str | None = None
    learningObjective: str | None = None


class AssignmentArtifactRequirement(BaseModel):
    path: str
    kind: str


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
    goal: str | None = None
    instructions: list[str]
    approvalCriteria: list[str] = Field(default_factory=list)
    materials: list[AssignmentMaterial] = Field(default_factory=list)
    requiredArtifacts: list[AssignmentArtifactRequirement] = Field(default_factory=list)
    submissionGuide: list[str] = Field(default_factory=list)
    submissionSpec: dict[str, Any]
    submissions: list[SubmissionSnapshot]


class AssignmentPage(BaseModel):
    items: list[AssignmentSummary]
    nextCursor: str | None


class ScheduleItemResponse(BaseModel):
    id: UUID
    scheduleKey: str
    date: str
    startAt: str | None
    endAt: str | None
    title: str
    description: str
    itemType: str
    assignmentId: UUID | None
    milestoneKey: str | None
    priority: int
    dueAt: str | None
    sourceUrl: str | None
    isRequired: bool
    displayStatus: str
    isOverdue: bool
    overdueDays: int
    isToday: bool
    assignmentUrl: str | None
    metadata: dict[str, Any]


class ScheduleDayResponse(BaseModel):
    date: str
    representativeStatus: str
    isToday: bool
    items: list[ScheduleItemResponse]


class SchedulePage(BaseModel):
    fromDate: str
    toDate: str
    days: list[ScheduleDayResponse]


class ScheduleSummary(BaseModel):
    todayCount: int
    learnerOverdueCount: int
    reviewWaitingCount: int
    nextImportantDate: str | None
    nextImportantTitle: str | None
    daysUntilPiscine: int


class CreateScheduleItemRequest(StrictRequest):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=4000)
    itemType: Literal[
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
    ]
    assignmentId: UUID | None = None
    milestoneKey: str | None = Field(default=None, max_length=120)
    statusOverride: Literal[
        "not_started",
        "in_progress",
        "submitted",
        "revision_requested",
        "approved",
        "cancelled",
    ] | None = None
    priority: int = Field(default=50, ge=1, le=100)
    dueAt: str | None = Field(default=None, max_length=40)
    sourceUrl: str | None = Field(default=None, max_length=2048)
    isRequired: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class UpdateScheduleItemRequest(StrictRequest):
    date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    itemType: Literal[
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
    ] | None = None
    assignmentId: UUID | None = None
    milestoneKey: str | None = Field(default=None, max_length=120)
    statusOverride: Literal[
        "not_started",
        "in_progress",
        "submitted",
        "revision_requested",
        "approved",
        "cancelled",
    ] | None = None
    priority: int | None = Field(default=None, ge=1, le=100)
    dueAt: str | None = Field(default=None, max_length=40)
    sourceUrl: str | None = Field(default=None, max_length=2048)
    isRequired: bool | None = None
    metadata: dict[str, Any] | None = None


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
