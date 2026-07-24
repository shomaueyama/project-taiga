# Runner and Worker Security

## Current State

`RUNNER_ENABLED=false` remains the default. When disabled, runner queue requests are rejected safely and no learner code executes.

When enabled for local testing, the backend records a runner job and outbox event. The worker claims one unpublished `runner_job.queued` event at a time with `FOR UPDATE SKIP LOCKED`.

## Changes

- Runner request reasons reject shell metacharacters and control characters before job creation.
- Worker no longer depends on a nonexistent outbox retry column; it uses the contract `attempt_count`.
- Worker ignores future `next_attempt_at` values when claiming jobs.
- Poison runner events are marked with `last_error` and delayed when the retry limit is exceeded.
- Worker and runner-controller no longer mount `/var/run/docker.sock`.
- Runner-controller uses `read_only: true`, `no-new-privileges`, and drops all Linux capabilities.
- Runner image uses a non-root user.

## Verified Properties

- Unsafe runner payloads do not create runner jobs.
- Poison outbox rows do not publish trusted results.
- Existing submission state transitions remain centralized in domain policy functions.

## Residual Risks

- Full disposable untrusted-code execution is still not enabled by default.
- CPU, memory, process, timeout, network, stdout/stderr, and workspace containment controls for actual execution containers remain deferred until hostile runner fixtures are implemented.
- Local Docker Compose hardening is not equivalent to production sandboxing.
