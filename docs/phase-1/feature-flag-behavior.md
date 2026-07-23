# Feature Flag Behavior

| Flag | Default | Disabled behavior | Enabled behavior in Phase 1 |
|---|---|---|---|
| `RUNNER_ENABLED` | `false` | Backend rejects runner queue requests with a safe disabled response; frontend disables the action | DEFERRED until Phase 4 isolated runner |
| `EXAM_ENABLED` | `false` | Backend permits read-only exam listing but rejects exam mutations with a safe disabled response; frontend disables the action | Partial server-authoritative flow remains available only when explicitly enabled |

Database feature flags `runner.enabled` and `exam.enabled` mirror local defaults for admin visibility.

## Phase 1 Verification

- `RUNNER_ENABLED=false`: `POST /api/v1/submissions/{id}/run` returns `403` with `Runner is disabled`.
- `RUNNER_ENABLED=true`: API queues a job, and local processing safely marks it `security_rejected`
  with hidden tests redacted.
- `EXAM_ENABLED=false`: exam mutation returns `403` with `Exam is disabled`.
- `EXAM_ENABLED=true`: reserve, start, submit, oral review, and pass transitions are covered by
  backend integration tests.
- Frontend does not request exam data when the health endpoint reports exams disabled.
