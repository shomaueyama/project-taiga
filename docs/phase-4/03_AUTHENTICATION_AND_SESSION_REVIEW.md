# Authentication and Session Review

## Current Mechanism

Local MVP authentication accepts `Authorization: Bearer local:<email>` or `X-Local-User` only when `APP_ENV=local` and `LOCAL_AUTH_ENABLED=true`.

No browser cookies, passwords, refresh tokens, or third-party identity sessions are used in the Local MVP.

## Findings

- Protected routes depend on `get_current_principal`.
- Unknown users receive HTTP 401.
- Suspended or inactive users receive HTTP 403.
- LocalAuth outside local mode fails instead of silently enabling test identity.
- Mutating endpoints require an `Idempotency-Key` header.
- Frontend stores only local test identity selection and does not receive production credentials.

## Changes

- Added fail-closed parsing for security-sensitive boolean flags.
- Added regression coverage that protected mutation endpoints reject unauthenticated requests.
- Added browser/security headers to all responses, including error responses.

## Limitations

- LocalAuth is not a production session system.
- There is no token expiry, refresh, revocation list, or password handling in Local MVP.
- Production authentication remains an AWS/Cognito adapter concern and is intentionally out of scope.
