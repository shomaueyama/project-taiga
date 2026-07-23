from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Path, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from taiga.admin_service import (
    analytics,
    curriculum_versions,
    invite_user,
    list_flags,
    list_notifications,
    list_users,
    notification_preferences,
    set_user_status,
    update_flag,
)
from taiga.api_schemas import (
    AssignmentDetail,
    AssignmentPage,
    CompleteUploadRequest,
    CreateExamAttemptRequest,
    CreateReviewRequest,
    CreateSubmissionRequest,
    CreateUploadRequest,
    CurriculumVersionPage,
    Dashboard,
    ExamAttemptDetail,
    ExamAttemptResponse,
    ExamPage,
    FeatureFlag,
    FeatureFlagList,
    InviteUserRequest,
    LearningAnalytics,
    NotificationPage,
    NotificationPreferenceList,
    OralReviewRequest,
    PageUserProfile,
    Progress,
    ReviewQueuePage,
    ReviewResponse,
    RunnerJobResponse,
    RunSubmissionRequest,
    StartExamRequest,
    SubmissionDetail,
    SubmissionResponse,
    SubmitExamRequest,
    UpdateFeatureFlagRequest,
    UploadSessionResponse,
    UserProfile,
)
from taiga.assignment_queries import (
    get_assignment,
    get_dashboard,
    get_progress,
    list_assignments,
)
from taiga.auth import Principal, get_current_principal
from taiga.config import Settings, get_settings
from taiga.errors import AppError
from taiga.exam_service import (
    get_attempt_detail,
    list_exams,
    oral_review,
    reserve_attempt,
    start_attempt,
    submit_attempt,
)
from taiga.infrastructure.database import database_ready, get_session
from taiga.runner_jobs import queue_runner_job
from taiga.security import add_security_headers, rate_limit_allows, too_many_requests_response
from taiga.submission_service import (
    complete_upload,
    create_review,
    create_submission,
    create_upload,
    get_submission_detail,
    get_upload,
    review_queue,
)

app = FastAPI(title="Project Taiga Local MVP", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Local-User"],
)
settings_dependency = Depends(get_settings)
session_dependency = Depends(get_session)
principal_dependency = Depends(get_current_principal)
assignment_id_path = Path(alias="assignmentId")
upload_id_path = Path(alias="uploadId")
submission_id_path = Path(alias="submissionId")
exam_id_path = Path(alias="examId")
attempt_id_path = Path(alias="attemptId")
user_id_path = Path(alias="userId")


@app.exception_handler(AppError)
def app_error_handler(_request: object, exc: AppError) -> Response:
    return add_security_headers(
        JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code},
        )
    )


@app.middleware("http")
async def security_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    settings = get_settings()
    if not rate_limit_allows(request, settings):
        return too_many_requests_response()
    response = await call_next(request)
    return add_security_headers(response)


@app.get("/health", tags=["system"])
def health(settings: Settings = settings_dependency) -> dict[str, object]:
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "runner_enabled": settings.runner_enabled,
        "exam_enabled": settings.exam_enabled,
    }


@app.get("/ready", tags=["system"])
def ready(_session: Session = session_dependency) -> dict[str, object]:
    return {"status": "ok", "database": database_ready()}


@app.get("/api/v1/health/live", tags=["system"])
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/health/ready", tags=["system"])
def api_ready(_session: Session = session_dependency) -> dict[str, object]:
    return {"status": "ok", "database": database_ready()}


@app.get("/api/v1/me", response_model=UserProfile, tags=["identity"])
def me(principal: Principal = principal_dependency) -> UserProfile:
    return UserProfile(
        id=principal.id,
        displayName=principal.display_name,
        role=principal.role,
        status=principal.status,
        timezone=principal.timezone,
    )


@app.get("/api/v1/dashboard", response_model=Dashboard, tags=["learning"])
def dashboard(
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> Dashboard:
    return get_dashboard(session, principal)


@app.get("/api/v1/assignments", response_model=AssignmentPage, tags=["learning"])
def assignments(
    limit: int = 20,
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> AssignmentPage:
    return list_assignments(session, principal, min(limit, 100))


@app.get("/api/v1/assignments/{assignmentId}", response_model=AssignmentDetail, tags=["learning"])
def assignment_detail(
    assignment_id: UUID = assignment_id_path,
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> AssignmentDetail:
    try:
        return get_assignment(session, principal, assignment_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Assignment not found") from exc


@app.get("/api/v1/progress", response_model=Progress, tags=["learning"])
def progress(
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> Progress:
    return get_progress(session, principal)


@app.post(
    "/api/v1/uploads/presign",
    response_model=UploadSessionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["submissions"],
)
def upload_presign(
    request: CreateUploadRequest,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> UploadSessionResponse:
    return create_upload(session, principal, request)


@app.post(
    "/api/v1/uploads/{uploadId}/complete",
    response_model=UploadSessionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["submissions"],
)
def upload_complete(
    request: CompleteUploadRequest,
    upload_id: UUID = upload_id_path,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> UploadSessionResponse:
    try:
        return complete_upload(session, principal, upload_id, request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Upload not found") from exc


@app.get("/api/v1/uploads/{uploadId}", response_model=UploadSessionResponse, tags=["submissions"])
def upload_state(
    upload_id: UUID = upload_id_path,
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> UploadSessionResponse:
    try:
        return get_upload(session, principal, upload_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Upload not found") from exc


@app.post(
    "/api/v1/assignments/{assignmentId}/submissions",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["submissions"],
)
def submit_assignment(
    request: CreateSubmissionRequest,
    assignment_id: UUID = assignment_id_path,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> SubmissionResponse:
    try:
        return create_submission(session, principal, assignment_id, request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Assignment not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get(
    "/api/v1/submissions/{submissionId}",
    response_model=SubmissionDetail,
    tags=["submissions"],
)
def submission_detail(
    submission_id: UUID = submission_id_path,
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> SubmissionDetail:
    try:
        return get_submission_detail(session, principal, submission_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Submission not found") from exc


@app.get("/api/v1/reviews/queue", response_model=ReviewQueuePage, tags=["reviews"])
def queue(
    response: Response,
    limit: int = 20,
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> ReviewQueuePage:
    try:
        return review_queue(session, principal, min(limit, 100))
    except PermissionError as exc:
        response.status_code = status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.post(
    "/api/v1/submissions/{submissionId}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["reviews"],
)
def review_submission(
    request: CreateReviewRequest,
    submission_id: UUID = submission_id_path,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> ReviewResponse:
    try:
        return create_review(session, principal, submission_id, request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Submission not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post(
    "/api/v1/submissions/{submissionId}/run",
    response_model=RunnerJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["runner"],
)
def run_submission(
    request: RunSubmissionRequest,
    submission_id: UUID = submission_id_path,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> RunnerJobResponse:
    try:
        return queue_runner_job(session, principal, submission_id, request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Submission not found") from exc


@app.get("/api/v1/exams", response_model=ExamPage, tags=["exams"])
def exams(
    limit: int = 20,
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> ExamPage:
    return list_exams(session, principal, min(limit, 100))


@app.post(
    "/api/v1/exams/{examId}/attempts",
    response_model=ExamAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["exams"],
)
def create_exam_attempt(
    request: CreateExamAttemptRequest,
    exam_id: UUID = exam_id_path,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> ExamAttemptResponse:
    try:
        return reserve_attempt(session, principal, exam_id, request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/v1/exam-attempts/{attemptId}", response_model=ExamAttemptDetail, tags=["exams"])
def exam_attempt(
    attempt_id: UUID = attempt_id_path,
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> ExamAttemptDetail:
    try:
        return get_attempt_detail(session, principal, attempt_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Exam attempt not found") from exc


@app.post(
    "/api/v1/exam-attempts/{attemptId}/start",
    response_model=ExamAttemptDetail,
    tags=["exams"],
)
def start_exam_attempt(
    request: StartExamRequest,
    attempt_id: UUID = attempt_id_path,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> ExamAttemptDetail:
    try:
        return start_attempt(session, principal, attempt_id, request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (LookupError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post(
    "/api/v1/exam-attempts/{attemptId}/submit",
    response_model=ExamAttemptDetail,
    tags=["exams"],
)
def submit_exam_attempt(
    request: SubmitExamRequest,
    attempt_id: UUID = attempt_id_path,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> ExamAttemptDetail:
    try:
        return submit_attempt(session, principal, attempt_id, request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Exam attempt not found") from exc


@app.post(
    "/api/v1/exam-attempts/{attemptId}/oral-review",
    response_model=ExamAttemptDetail,
    tags=["exams"],
)
def oral_review_attempt(
    request: OralReviewRequest,
    attempt_id: UUID = attempt_id_path,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> ExamAttemptDetail:
    try:
        return oral_review(session, principal, attempt_id, request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Exam attempt not found") from exc


@app.get("/api/v1/notifications", response_model=NotificationPage, tags=["notifications"])
def notifications(
    limit: int = 20,
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> NotificationPage:
    return list_notifications(session, principal, min(limit, 100))


@app.get(
    "/api/v1/notification-preferences",
    response_model=NotificationPreferenceList,
    tags=["notifications"],
)
def preferences(
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> NotificationPreferenceList:
    return notification_preferences(session, principal)


@app.get("/api/v1/admin/users", response_model=PageUserProfile, tags=["admin"])
def admin_users(
    limit: int = 20,
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> PageUserProfile:
    try:
        return list_users(session, principal, min(limit, 100))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.post(
    "/api/v1/admin/users/invitations",
    response_model=UserProfile,
    status_code=status.HTTP_201_CREATED,
    tags=["admin"],
)
def admin_invite_user(
    request: InviteUserRequest,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> UserProfile:
    try:
        return invite_user(session, principal, request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.post("/api/v1/admin/users/{userId}/suspend", response_model=UserProfile, tags=["admin"])
def admin_suspend_user(
    user_id: UUID = user_id_path,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> UserProfile:
    try:
        return set_user_status(session, principal, user_id, "suspended")
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc


@app.post("/api/v1/admin/users/{userId}/restore", response_model=UserProfile, tags=["admin"])
def admin_restore_user(
    user_id: UUID = user_id_path,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> UserProfile:
    try:
        return set_user_status(session, principal, user_id, "active")
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc


@app.get("/api/v1/admin/feature-flags", response_model=FeatureFlagList, tags=["admin"])
def admin_feature_flags(
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> FeatureFlagList:
    try:
        return list_flags(session, principal)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.patch("/api/v1/admin/feature-flags/{key}", response_model=FeatureFlag, tags=["admin"])
def admin_update_feature_flag(
    key: str,
    request: UpdateFeatureFlagRequest,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> FeatureFlag:
    try:
        return update_flag(session, principal, key, request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Feature flag not found") from exc


@app.get("/api/v1/admin/analytics/learning", response_model=LearningAnalytics, tags=["admin"])
def admin_learning_analytics(
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> LearningAnalytics:
    try:
        return analytics(session, principal)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.get(
    "/api/v1/admin/curriculum/versions",
    response_model=CurriculumVersionPage,
    tags=["admin"],
)
def admin_curriculum_versions(
    limit: int = 20,
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> CurriculumVersionPage:
    try:
        return curriculum_versions(session, principal, min(limit, 100))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
