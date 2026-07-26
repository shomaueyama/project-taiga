from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm

from taiga.cloudflare_access import AccessVerificationError, CloudflareAccessVerifier
from taiga.config import Settings, get_settings
from taiga.main import app

TEAM_DOMAIN = "https://team.cloudflareaccess.com"
AUDIENCE = "test-aud"
APP_ORIGIN = "https://app.example.com"
DB_URL = "postgresql+psycopg://user:pass@db.example.com/taiga?sslmode=require"


def production_settings() -> Settings:
    return Settings(
        APP_ENV="production",
        LOCAL_AUTH_ENABLED=False,
        DATABASE_URL=DB_URL,
        FRONTEND_ORIGINS=APP_ORIGIN,
        RUNNER_ENABLED=False,
        CLOUDFLARE_ACCESS_TEAM_DOMAIN=TEAM_DOMAIN,
        CLOUDFLARE_ACCESS_AUD=AUDIENCE,
        AUTHORIZED_USER_EMAILS="shoma@example.com,taiga@example.com",
    )


def key_pair(kid: str = "kid-1") -> tuple[Any, dict[str, Any]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update({"kid": kid, "alg": "RS256", "use": "sig"})
    return private_key, jwk


def access_token(
    private_key: Any,
    *,
    kid: str = "kid-1",
    email: str = "shoma@example.com",
    audience: str = AUDIENCE,
    issuer: str = TEAM_DOMAIN,
    expires_at: int | None = None,
) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "iss": issuer,
            "aud": audience,
            "email": email,
            "iat": now,
            "exp": expires_at if expires_at is not None else now + 300,
        },
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )


def verifier_for(jwks_loader: Callable[[str], dict[str, Any]]) -> CloudflareAccessVerifier:
    return CloudflareAccessVerifier(production_settings(), jwks_loader=jwks_loader)


def test_valid_access_token_for_approved_email() -> None:
    private_key, jwk = key_pair()
    token = access_token(private_key)
    identity = verifier_for(lambda _url: {"keys": [jwk]}).verify(token)
    assert identity.email == "shoma@example.com"


def test_valid_access_token_for_unapproved_email_is_rejected() -> None:
    private_key, jwk = key_pair()
    token = access_token(private_key, email="other@example.com")
    with pytest.raises(AccessVerificationError, match="unauthorized_access_email"):
        verifier_for(lambda _url: {"keys": [jwk]}).verify(token)


def test_missing_token_is_rejected() -> None:
    with pytest.raises(AccessVerificationError, match="missing_access_jwt"):
        verifier_for(lambda _url: {"keys": []}).verify(None)


def test_invalid_signature_is_rejected() -> None:
    private_key, _jwk = key_pair()
    _other_private_key, other_jwk = key_pair()
    token = access_token(private_key)
    with pytest.raises(AccessVerificationError, match="invalid_access_jwt"):
        verifier_for(lambda _url: {"keys": [other_jwk]}).verify(token)


def test_expired_token_is_rejected() -> None:
    private_key, jwk = key_pair()
    token = access_token(private_key, expires_at=int(time.time()) - 60)
    with pytest.raises(AccessVerificationError, match="invalid_access_jwt"):
        verifier_for(lambda _url: {"keys": [jwk]}).verify(token)


def test_wrong_audience_is_rejected() -> None:
    private_key, jwk = key_pair()
    token = access_token(private_key, audience="wrong-aud")
    with pytest.raises(AccessVerificationError, match="invalid_access_jwt"):
        verifier_for(lambda _url: {"keys": [jwk]}).verify(token)


def test_wrong_issuer_is_rejected() -> None:
    private_key, jwk = key_pair()
    token = access_token(private_key, issuer="https://other.cloudflareaccess.com")
    with pytest.raises(AccessVerificationError, match="invalid_access_jwt"):
        verifier_for(lambda _url: {"keys": [jwk]}).verify(token)


def test_signing_key_refreshes_when_kid_is_not_in_cached_jwks() -> None:
    private_key, jwk = key_pair(kid="fresh-kid")
    token = access_token(private_key, kid="fresh-kid")
    calls = 0

    def loader(_url: str) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return {"keys": []}
        return {"keys": [jwk]}

    assert verifier_for(loader).verify(token).email == "shoma@example.com"
    assert calls == 2


def test_production_config_rejects_unsafe_values() -> None:
    with pytest.raises(ValueError, match="RUNNER_ENABLED"):
        Settings(
            APP_ENV="production",
            LOCAL_AUTH_ENABLED=False,
            DATABASE_URL=DB_URL,
            FRONTEND_ORIGINS=APP_ORIGIN,
            RUNNER_ENABLED=True,
            CLOUDFLARE_ACCESS_TEAM_DOMAIN=TEAM_DOMAIN,
            CLOUDFLARE_ACCESS_AUD=AUDIENCE,
            AUTHORIZED_USER_EMAILS="shoma@example.com,taiga@example.com",
        )
    with pytest.raises(ValueError, match="exactly two"):
        Settings(
            APP_ENV="production",
            LOCAL_AUTH_ENABLED=False,
            DATABASE_URL=DB_URL,
            FRONTEND_ORIGINS=APP_ORIGIN,
            CLOUDFLARE_ACCESS_TEAM_DOMAIN=TEAM_DOMAIN,
            CLOUDFLARE_ACCESS_AUD=AUDIENCE,
            AUTHORIZED_USER_EMAILS="shoma@example.com",
        )
    with pytest.raises(ValueError, match="local database"):
        Settings(
            APP_ENV="production",
            LOCAL_AUTH_ENABLED=False,
            DATABASE_URL="postgresql+psycopg://taiga:taiga@localhost/taiga",
            FRONTEND_ORIGINS=APP_ORIGIN,
            CLOUDFLARE_ACCESS_TEAM_DOMAIN=TEAM_DOMAIN,
            CLOUDFLARE_ACCESS_AUD=AUDIENCE,
            AUTHORIZED_USER_EMAILS="shoma@example.com,taiga@example.com",
        )


def test_public_health_is_limited_and_protected_paths_require_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LOCAL_AUTH_ENABLED", "false")
    monkeypatch.setenv("DATABASE_URL", DB_URL)
    monkeypatch.setenv("FRONTEND_ORIGINS", APP_ORIGIN)
    monkeypatch.setenv("RUNNER_ENABLED", "false")
    monkeypatch.setenv("CLOUDFLARE_ACCESS_TEAM_DOMAIN", TEAM_DOMAIN)
    monkeypatch.setenv("CLOUDFLARE_ACCESS_AUD", AUDIENCE)
    monkeypatch.setenv("AUTHORIZED_USER_EMAILS", "shoma@example.com,taiga@example.com")
    get_settings.cache_clear()
    try:
        client = TestClient(app)

        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}

        assert client.post("/api/health").status_code == 404
        assert client.get("/health").status_code == 404
        assert client.get("/ready").status_code == 404

        protected = client.get("/api/v1/me")
        assert protected.status_code == 401
        assert "Cf-Access-Jwt-Assertion" not in protected.text
        assert "token" not in protected.text.lower()
    finally:
        get_settings.cache_clear()
