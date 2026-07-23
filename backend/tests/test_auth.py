import pytest
from fastapi import HTTPException

from taiga.auth import local_email_from_headers
from taiga.config import Settings


def test_local_auth_accepts_bearer_local_token() -> None:
    settings = Settings(APP_ENV="local", LOCAL_AUTH_ENABLED=True)
    assert (
        local_email_from_headers("Bearer local:taiga@example.local", None, settings)
        == "taiga@example.local"
    )


def test_local_auth_rejects_missing_header() -> None:
    settings = Settings(APP_ENV="local", LOCAL_AUTH_ENABLED=True)
    with pytest.raises(HTTPException):
        local_email_from_headers(None, None, settings)


def test_local_auth_fail_fast_outside_local() -> None:
    with pytest.raises(ValueError):
        Settings(APP_ENV="production", LOCAL_AUTH_ENABLED=True)
