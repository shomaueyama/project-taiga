from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from taiga.api_schemas import (
    AssignmentDetail,
    AssignmentPage,
    CompleteUploadRequest,
    CreateExamAttemptRequest,
    CreateReviewRequest,
    CreateSubmissionRequest,
    CreateUploadRequest,
    Dashboard,
    ExamAttemptDetail,
    ExamAttemptResponse,
    ExamPage,
    OralReviewRequest,
    Progress,
    ReviewQueuePage,
    ReviewResponse,
    RunnerJobResponse,
    RunSubmissionRequest,
    StartExamRequest,
    SubmissionDetail,
    SubmissionResponse,
    SubmitExamRequest,
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
    allow_methods=["*"],
    allow_headers=["*"],
)
settings_dependency = Depends(get_settings)
session_dependency = Depends(get_session)
principal_dependency = Depends(get_current_principal)


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


@app.get("/api/v1/assignments/{assignment_id}", response_model=AssignmentDetail, tags=["learning"])
def assignment_detail(
    assignment_id: UUID,
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
    "/api/v1/uploads/{upload_id}/complete",
    response_model=UploadSessionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["submissions"],
)
def upload_complete(
    upload_id: UUID,
    request: CompleteUploadRequest,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> UploadSessionResponse:
    try:
        return complete_upload(session, principal, upload_id, request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Upload not found") from exc


@app.get("/api/v1/uploads/{upload_id}", response_model=UploadSessionResponse, tags=["submissions"])
def upload_state(
    upload_id: UUID,
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> UploadSessionResponse:
    try:
        return get_upload(session, principal, upload_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Upload not found") from exc


@app.post(
    "/api/v1/assignments/{assignment_id}/submissions",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["submissions"],
)
def submit_assignment(
    assignment_id: UUID,
    request: CreateSubmissionRequest,
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
    "/api/v1/submissions/{submission_id}",
    response_model=SubmissionDetail,
    tags=["submissions"],
)
def submission_detail(
    submission_id: UUID,
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
    "/api/v1/submissions/{submission_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["reviews"],
)
def review_submission(
    submission_id: UUID,
    request: CreateReviewRequest,
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


@app.post(
    "/api/v1/submissions/{submission_id}/run",
    response_model=RunnerJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["runner"],
)
def run_submission(
    submission_id: UUID,
    request: RunSubmissionRequest,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> RunnerJobResponse:
    try:
        return queue_runner_job(session, principal, submission_id, request)
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
    "/api/v1/exams/{exam_id}/attempts",
    response_model=ExamAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["exams"],
)
def create_exam_attempt(
    exam_id: UUID,
    request: CreateExamAttemptRequest,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> ExamAttemptResponse:
    try:
        return reserve_attempt(session, principal, exam_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/v1/exam-attempts/{attempt_id}", response_model=ExamAttemptDetail, tags=["exams"])
def exam_attempt(
    attempt_id: UUID,
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> ExamAttemptDetail:
    try:
        return get_attempt_detail(session, principal, attempt_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Exam attempt not found") from exc


@app.post(
    "/api/v1/exam-attempts/{attempt_id}/start",
    response_model=ExamAttemptDetail,
    tags=["exams"],
)
def start_exam_attempt(
    attempt_id: UUID,
    request: StartExamRequest,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> ExamAttemptDetail:
    try:
        return start_attempt(session, principal, attempt_id, request)
    except (LookupError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post(
    "/api/v1/exam-attempts/{attempt_id}/submit",
    response_model=ExamAttemptDetail,
    tags=["exams"],
)
def submit_exam_attempt(
    attempt_id: UUID,
    request: SubmitExamRequest,
    _idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    principal: Principal = principal_dependency,
    session: Session = session_dependency,
) -> ExamAttemptDetail:
    try:
        return submit_attempt(session, principal, attempt_id, request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Exam attempt not found") from exc


@app.post(
    "/api/v1/exam-attempts/{attempt_id}/oral-review",
    response_model=ExamAttemptDetail,
    tags=["exams"],
)
def oral_review_attempt(
    attempt_id: UUID,
    request: OralReviewRequest,
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
