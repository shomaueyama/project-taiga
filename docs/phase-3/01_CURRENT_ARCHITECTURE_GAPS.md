# Current Architecture Gaps

## Backend Inventory

- Routes live in `backend/src/taiga/main.py`.
- Request and response schemas live in `backend/src/taiga/api_schemas.py`.
- Application logic and SQL are grouped by feature:
  - `assignment_queries.py`
  - `submission_service.py`
  - `exam_service.py`
  - `runner_jobs.py`
  - `admin_service.py`
- Authentication and local principal lookup live in `auth.py`.
- Session lifecycle and transaction commit/rollback live in `infrastructure/database.py`.
- Worker polling lives in `worker.py` and calls `runner_jobs.process_next_runner_job`.

## Gaps Found

- Role checks were duplicated as literal comparisons in admin, submission, and exam services.
- State transitions were embedded inside SQL update statements and were hard to test without a
  database.
- Domain/application errors used built-in exceptions (`PermissionError`, `LookupError`,
  `ValueError`) with repeated HTTP mapping in route handlers.
- Generated OpenAPI path parameter names used snake_case, while the design contract uses
  camelCase names such as `{assignmentId}` and `{submissionId}`.
- `main.py` still contains repetitive legacy exception mapping and remains larger than ideal.
- Persistence and application logic are still mixed inside feature services. This is acceptable for
  the Local MVP but should be revisited when the runner and exam engines mature.
- Worker retry behavior is intentionally simple and uses fixed sleep-based polling.

## Frontend Inventory

- API calls live in `frontend/src/shared/api/client.ts`.
- Components do not call `fetch` directly.
- `App.tsx` owns the Local MVP shell, role-gated rendering, feature flag display, and mutation
  wiring.
- Frontend tests cover API client behavior and App actions.

## Cross-Cutting Findings

- Backend remains authoritative for authorization and feature flags.
- Frontend uses feature flags to guide the UI but does not own mutation rules.
- Error responses are now moving toward `detail` plus `code`, but FastAPI validation/auth errors
  still use their native shapes.
