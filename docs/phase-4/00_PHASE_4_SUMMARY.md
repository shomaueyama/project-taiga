# Phase 4 Summary

Phase 4 hardened the Local MVP security posture without changing the core product flow or adding production infrastructure.

## Scope

- Added backend-wide security headers and explicit CORS methods/headers.
- Added local in-process rate limiting with fail-closed boolean configuration parsing.
- Tightened Pydantic request schemas with unknown-field rejection, length limits, ranges, and bounded arrays.
- Hardened upload validation for unsafe filenames, path traversal, extension spoofing, MIME mismatch, empty files, oversized files, and invalid SHA-256 values.
- Removed Docker socket mounts from worker and runner-controller services.
- Added runner-controller container hardening and non-root runner image user.
- Added runner request payload rejection for shell metacharacters and control characters.
- Bounded poison outbox processing using the existing `attempt_count`, `next_attempt_at`, and `last_error` columns.
- Added Phase 4 security regression tests.

## Design References

- `../design/taiga-42-v4.0-implementation-pack/01_SOURCE_OF_TRUTH.md`
- `../design/taiga-42-v4.0-implementation-pack/02_LOCAL_MVP_IMPLEMENTATION.md`
- `../design/taiga-42-v4.0-implementation-pack/contracts/openapi/openapi.json`
- `../design/taiga-42-v4.0-implementation-pack/contracts/database/001_initial_schema.sql`
- `../design/taiga-42-v4.0-implementation-pack/contracts/security/`

## Primary Code Changes

- `backend/src/taiga/security.py`
- `backend/src/taiga/main.py`
- `backend/src/taiga/api_schemas.py`
- `backend/src/taiga/config.py`
- `backend/src/taiga/submission_service.py`
- `backend/src/taiga/runner_jobs.py`
- `backend/tests/test_phase4_security.py`
- `docker-compose.yml`
- `runner/Dockerfile`
- `.env.example`
- `README.md`

## Non-Goals

- No AWS resources were created.
- No production identity provider was added.
- No hidden tests were exposed.
- No application behavior was relaxed to satisfy tests.
