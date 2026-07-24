from __future__ import annotations

from taiga.auth import Principal
from taiga.errors import AuthorizationError

REVIEW_ROLES = frozenset({"reviewer", "admin"})


def is_reviewer(principal: Principal) -> bool:
    return principal.role in REVIEW_ROLES


def require_admin(principal: Principal) -> None:
    if principal.role != "admin":
        raise AuthorizationError("Admin role required", code="admin_role_required")


def require_reviewer(principal: Principal) -> None:
    if not is_reviewer(principal):
        raise AuthorizationError("Reviewer role required", code="reviewer_role_required")
