from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="local", validation_alias="APP_ENV")
    local_auth_enabled: bool = Field(default=True, validation_alias="LOCAL_AUTH_ENABLED")
    database_url: str = Field(
        default="postgresql+psycopg://taiga:taiga@postgres:5432/taiga",
        validation_alias="DATABASE_URL",
    )
    local_storage_root: str = Field(
        default="/workspace/local-storage",
        validation_alias="LOCAL_STORAGE_ROOT",
    )
    curriculum_source_dir: str = Field(
        default="../../design/taiga-42-v4.0-implementation-pack/curriculum",
        validation_alias="CURRICULUM_SOURCE_DIR",
    )
    runner_enabled: bool = Field(default=False, validation_alias="RUNNER_ENABLED")
    exam_enabled: bool = Field(default=False, validation_alias="EXAM_ENABLED")
    rate_limit_enabled: bool = Field(default=True, validation_alias="RATE_LIMIT_ENABLED")
    rate_limit_window_seconds: int = Field(default=60, validation_alias="RATE_LIMIT_WINDOW_SECONDS")
    rate_limit_max_requests: int = Field(default=120, validation_alias="RATE_LIMIT_MAX_REQUESTS")
    worker_idle_poll_seconds: float = Field(
        default=5.0,
        validation_alias="WORKER_IDLE_POLL_SECONDS",
    )
    worker_error_retry_seconds: float = Field(
        default=30.0,
        validation_alias="WORKER_ERROR_RETRY_SECONDS",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("local_auth_enabled")
    @classmethod
    def local_auth_requires_local_env(cls, value: bool, info: object) -> bool:
        data = getattr(info, "data", {})
        if value and data.get("app_env") != "local":
            raise ValueError("LOCAL_AUTH_ENABLED can only be true when APP_ENV=local")
        return value

    @field_validator("runner_enabled", "exam_enabled", "rate_limit_enabled", mode="before")
    @classmethod
    def security_flags_are_strict_bool(cls, value: object) -> object:
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.lower() in {"true", "false"}:
            return value
        raise ValueError("Security-sensitive boolean flags must be true or false")


@lru_cache
def get_settings() -> Settings:
    return Settings()
