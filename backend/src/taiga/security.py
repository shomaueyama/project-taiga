from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import MutableMapping
from dataclasses import dataclass, field

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from taiga.config import Settings

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'; base-uri 'self'",
    "Cache-Control": "no-store",
}

HIGH_RISK_PATH_PARTS = (
    "/uploads/",
    "/submissions/",
    "/exam-attempts/",
    "/admin/",
)


@dataclass
class LocalRateLimiter:
    buckets: MutableMapping[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def allow(self, key: str, *, now: float, window_seconds: int, max_requests: int) -> bool:
        bucket = self.buckets[key]
        cutoff = now - window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= max_requests:
            return False
        bucket.append(now)
        return True

    def clear(self) -> None:
        self.buckets.clear()


rate_limiter = LocalRateLimiter()


def add_security_headers(response: Response) -> Response:
    for key, value in SECURITY_HEADERS.items():
        response.headers.setdefault(key, value)
    return response


def rate_limit_key(request: Request) -> str:
    client_host = request.client.host if request.client else "unknown"
    return f"{client_host}:{request.method}:{request.url.path}"


def rate_limit_max_for_path(path: str, settings: Settings) -> int:
    if any(part in path for part in HIGH_RISK_PATH_PARTS):
        return min(settings.rate_limit_max_requests, 60)
    return settings.rate_limit_max_requests


def too_many_requests_response() -> JSONResponse:
    response = JSONResponse(
        status_code=429,
        content={"detail": "Too many requests", "code": "rate_limited"},
    )
    add_security_headers(response)
    return response


def rate_limit_allows(request: Request, settings: Settings) -> bool:
    if not settings.rate_limit_enabled or request.url.path in {"/health", "/ready"}:
        return True
    return rate_limiter.allow(
        rate_limit_key(request),
        now=time.monotonic(),
        window_seconds=settings.rate_limit_window_seconds,
        max_requests=rate_limit_max_for_path(request.url.path, settings),
    )
