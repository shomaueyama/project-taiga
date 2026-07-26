from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
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
    frontend_origins: str = Field(
        default="http://localhost:5173",
        validation_alias="FRONTEND_ORIGINS",
    )
    cloudflare_access_team_domain: str | None = Field(
        default=None,
        validation_alias="CLOUDFLARE_ACCESS_TEAM_DOMAIN",
    )
    cloudflare_access_aud: str | None = Field(
        default=None,
        validation_alias="CLOUDFLARE_ACCESS_AUD",
    )
    authorized_user_emails: str | None = Field(
        default=None,
        validation_alias="AUTHORIZED_USER_EMAILS",
    )
    app_login_credentials: str | None = Field(
        default=None,
        validation_alias="APP_LOGIN_CREDENTIALS",
    )
    app_session_secret: str | None = Field(default=None, validation_alias="APP_SESSION_SECRET")
    app_session_ttl_seconds: int = Field(
        default=60 * 60 * 24 * 14,
        validation_alias="APP_SESSION_TTL_SECONDS",
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

    @field_validator("database_url")
    @classmethod
    def database_url_uses_psycopg_driver(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @field_validator("runner_enabled", "exam_enabled", "rate_limit_enabled", mode="before")
    @classmethod
    def security_flags_are_strict_bool(cls, value: object) -> object:
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.lower() in {"true", "false"}:
            return value
        raise ValueError("Security-sensitive boolean flags must be true or false")

    @field_validator("frontend_origins")
    @classmethod
    def frontend_origins_are_explicit(cls, value: str, info: object) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if not origins:
            raise ValueError("FRONTEND_ORIGINS must contain at least one origin")
        if "*" in origins:
            raise ValueError("Wildcard FRONTEND_ORIGINS is not allowed")
        data = getattr(info, "data", {})
        app_env = data.get("app_env")
        if app_env != "local":
            insecure = [
                origin
                for origin in origins
                if origin.startswith("http://") and not origin.startswith("http://localhost")
            ]
            if insecure:
                raise ValueError("Production FRONTEND_ORIGINS must use HTTPS")
        return ",".join(origins)

    @field_validator("cloudflare_access_team_domain")
    @classmethod
    def cloudflare_team_domain_has_origin_shape(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        normalized = value.rstrip("/")
        parsed = urlparse(normalized)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("CLOUDFLARE_ACCESS_TEAM_DOMAIN must be an HTTPS origin")
        return normalized

    @model_validator(mode="after")
    def production_configuration_is_safe(self) -> "Settings":
        if self.app_env != "production":
            return self
        if self.local_auth_enabled:
            raise ValueError("LOCAL_AUTH_ENABLED must be false in production")
        if self.runner_enabled:
            raise ValueError("RUNNER_ENABLED must be false in production")
        database_host = urlparse(self.database_url).hostname
        if database_host in {None, "", "localhost", "127.0.0.1", "::1", "postgres"}:
            raise ValueError("Production DATABASE_URL must not target a local database")
        if not self.cloudflare_access_team_domain:
            raise ValueError("CLOUDFLARE_ACCESS_TEAM_DOMAIN is required in production")
        if not self.cloudflare_access_aud:
            raise ValueError("CLOUDFLARE_ACCESS_AUD is required in production")
        if len(self.authorized_email_set) != 2:
            raise ValueError("AUTHORIZED_USER_EMAILS must contain exactly two production users")
        return self

    @property
    def allowed_frontend_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def authorized_email_set(self) -> set[str]:
        if not self.authorized_user_emails:
            return set()
        return {
            email.strip().lower()
            for email in self.authorized_user_emails.split(",")
            if email.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
