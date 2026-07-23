from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from taiga.config import Settings, get_settings
from taiga.infrastructure.database import database_ready, get_session

app = FastAPI(title="Project Taiga Local MVP", version="0.1.0")
settings_dependency = Depends(get_settings)
session_dependency = Depends(get_session)


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
