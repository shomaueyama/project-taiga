from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from taiga.api_schemas import AssignmentDetail, AssignmentPage, Dashboard, Progress, UserProfile
from taiga.assignment_queries import (
    get_assignment,
    get_dashboard,
    get_progress,
    list_assignments,
)
from taiga.auth import Principal, get_current_principal
from taiga.config import Settings, get_settings
from taiga.infrastructure.database import database_ready, get_session

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
