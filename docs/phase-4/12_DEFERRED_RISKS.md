# Deferred Risks

## Runner Isolation

Actual hostile-code execution remains disabled by default. Full disposable runner hardening still needs CPU, memory, PID, timeout, network, stdout/stderr, workspace, symlink, cleanup, and hidden-test isolation coverage before `RUNNER_ENABLED=true` becomes a normal default.

## Production Authentication

LocalAuth is explicitly local-only. Production authentication, token lifecycle, key rotation, and identity-provider integration remain deferred to the AWS adapter phase.

## Distributed Rate Limiting

The current rate limiter is in-process and local-only. Production needs a distributed limiter or edge/API gateway control.

## Upload Content Inspection

Phase 4 validates upload metadata and storage keys. It does not scan file contents, detect malware, or inspect archives.

## Audit Logging

The database schema supports audit events, but mutation-by-mutation audit coverage is not complete.

## Dependency Scanning

Frontend `npm audit` is available locally. Backend dependency scanning depends on whether a Python audit tool is installed in the environment.

## Browser E2E Coverage

Exam browser E2E remains gated by `EXAM_ENABLED=false` default behavior and should be expanded once exam flow hardening reaches the next phase.
