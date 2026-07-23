from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AppError(Exception):
    message: str
    code: str
    status_code: int

    def payload(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message}


class AuthorizationError(AppError):
    def __init__(self, message: str = "Forbidden", code: str = "authorization_failed") -> None:
        super().__init__(message=message, code=code, status_code=403)


class FeatureDisabledError(AppError):
    def __init__(self, message: str, code: str) -> None:
        super().__init__(message=message, code=code, status_code=403)


class NotFoundError(AppError):
    def __init__(self, message: str, code: str = "not_found") -> None:
        super().__init__(message=message, code=code, status_code=404)


class ConflictError(AppError):
    def __init__(self, message: str, code: str = "conflict") -> None:
        super().__init__(message=message, code=code, status_code=409)


class InvalidTransitionError(ConflictError):
    def __init__(self, message: str, code: str = "invalid_state_transition") -> None:
        super().__init__(message=message, code=code)
