# Secrets, Configuration, and Logging

## Configuration

Local defaults are explicit:

- `APP_ENV=local`
- `LOCAL_AUTH_ENABLED=true`
- `RUNNER_ENABLED=false`
- `EXAM_ENABLED=false`
- `RATE_LIMIT_ENABLED=true`
- `RATE_LIMIT_WINDOW_SECONDS=60`
- `RATE_LIMIT_MAX_REQUESTS=120`

Security-sensitive booleans fail closed when set to anything other than true or false.

## Secrets

- No AWS credentials are required.
- No production secrets are committed.
- `.env` and `.env.*` remain ignored except `.env.example`.
- The Docker Compose database password is a local-only development credential.

## Logging

Application error responses expose stable client-safe messages and codes. Phase 4 tests verify malformed JSON does not expose tracebacks.

## Residual Work

- Add structured request IDs and audit logging for every mutation.
- Add automated secret scanning beyond regex-based local validation if the CI environment allows it.
