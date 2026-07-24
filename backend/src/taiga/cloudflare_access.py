from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import jwt
from jwt import PyJWK

from taiga.config import Settings

ACCESS_JWT_HEADER = "Cf-Access-Jwt-Assertion"
ALLOWED_ALGORITHMS = ["RS256"]
DEFAULT_JWKS_CACHE_SECONDS = 300


class AccessVerificationError(Exception):
    pass


@dataclass(frozen=True)
class AccessIdentity:
    email: str


class CloudflareAccessVerifier:
    def __init__(
        self,
        settings: Settings,
        *,
        jwks_loader: Callable[[str], dict[str, Any]] | None = None,
        now: Callable[[], float] = time.time,
        cache_seconds: int = DEFAULT_JWKS_CACHE_SECONDS,
    ) -> None:
        self._settings = settings
        self._jwks_loader = jwks_loader or load_jwks
        self._now = now
        self._cache_seconds = cache_seconds
        self._cached_jwks: dict[str, Any] | None = None
        self._cached_until = 0.0

    def verify(self, token: str | None) -> AccessIdentity:
        if not token:
            raise AccessVerificationError("missing_access_jwt")
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise AccessVerificationError("malformed_access_jwt") from exc
        if header.get("alg") not in ALLOWED_ALGORITHMS:
            raise AccessVerificationError("unsupported_access_jwt_algorithm")
        kid = header.get("kid")
        if not isinstance(kid, str) or not kid:
            raise AccessVerificationError("missing_access_jwt_key_id")
        signing_key = self._signing_key(kid)
        payload = self._decode(token, signing_key)
        email = payload.get("email")
        if not isinstance(email, str) or not email:
            raise AccessVerificationError("missing_access_email")
        normalized_email = email.lower()
        if normalized_email not in self._settings.authorized_email_set:
            raise AccessVerificationError("unauthorized_access_email")
        return AccessIdentity(email=normalized_email)

    def _decode(self, token: str, signing_key: Any) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                key=signing_key,
                algorithms=ALLOWED_ALGORITHMS,
                audience=self._settings.cloudflare_access_aud,
                issuer=self._settings.cloudflare_access_team_domain,
                options={"require": ["exp", "iss", "aud"]},
            )
        except jwt.PyJWTError as exc:
            raise AccessVerificationError("invalid_access_jwt") from exc
        if not isinstance(payload, dict):
            raise AccessVerificationError("invalid_access_payload")
        return payload

    def _signing_key(self, kid: str) -> object:
        jwk = self._find_jwk(kid)
        if jwk is None:
            self._refresh_jwks(force=True)
            jwk = self._find_jwk(kid)
        if jwk is None:
            raise AccessVerificationError("unknown_access_jwt_key")
        return PyJWK.from_dict(jwk).key

    def _find_jwk(self, kid: str) -> dict[str, Any] | None:
        jwks = self._refresh_jwks()
        for key in jwks.get("keys", []):
            if isinstance(key, dict) and key.get("kid") == kid:
                return key
        return None

    def _refresh_jwks(self, *, force: bool = False) -> dict[str, Any]:
        now = self._now()
        if not force and self._cached_jwks is not None and now < self._cached_until:
            return self._cached_jwks
        team_domain = self._settings.cloudflare_access_team_domain
        if not team_domain:
            raise AccessVerificationError("missing_access_team_domain")
        jwks = self._jwks_loader(f"{team_domain}/cdn-cgi/access/certs")
        if not isinstance(jwks.get("keys"), list):
            raise AccessVerificationError("invalid_access_jwks")
        self._cached_jwks = jwks
        self._cached_until = now + self._cache_seconds
        return jwks


def load_jwks(url: str) -> dict[str, Any]:
    try:
        # The Cloudflare team domain is validated as an HTTPS origin before this URL is built.
        with urlopen(url, timeout=5) as response:  # noqa: S310
            payload = response.read()
    except (OSError, URLError) as exc:
        raise AccessVerificationError("access_jwks_fetch_failed") from exc
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise AccessVerificationError("access_jwks_parse_failed") from exc
    if not isinstance(parsed, dict):
        raise AccessVerificationError("invalid_access_jwks")
    return parsed


def verify_cloudflare_access(token: str | None, settings: Settings) -> AccessIdentity:
    return CloudflareAccessVerifier(settings).verify(token)
