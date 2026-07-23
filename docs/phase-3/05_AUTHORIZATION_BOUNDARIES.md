# Authorization Boundaries

## Policy Boundary

Reusable policy functions live in `taiga.authorization`:

- `is_reviewer`
- `require_reviewer`
- `require_admin`

These raise typed `AuthorizationError` values that the transport layer maps to HTTP 403.

## Current Checks

| Area | Rule |
|---|---|
| Local auth | `auth.get_current_principal` maps missing/unknown users to 401 and inactive users to 403 |
| Assignment list/detail | learner-owned records only |
| Uploads | owner-only access |
| Submission detail | learner owner or reviewer/admin |
| Review queue | reviewer/admin |
| Review decision | reviewer/admin |
| Runner request | submission access plus feature flag |
| Exam attempt detail | learner owner or reviewer/admin |
| Oral review | reviewer/admin plus feature flag |
| Admin APIs | admin only |

## Not Found vs Forbidden

- Unknown or inactive principals are handled before application services.
- Learner access to another learner's direct resource generally returns 404 where the resource is
  owner-scoped.
- Role-gated feature surfaces return 403.

## Remaining Work

- Move all remaining legacy `PermissionError` catches out of routes after the entire service layer
  has switched to typed errors.
- Add ownership-specific helper functions if resource access rules become more complex.
