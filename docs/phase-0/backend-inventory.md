# Backend Inventory

## Structure

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI app and route handlers |
| `api_schemas.py` | Pydantic request/response schemas |
| `auth.py` | LocalAuth header parsing and current principal |
| `assignment_queries.py` | Dashboard, assignment list/detail, progress |
| `submission_service.py` | Upload, submission, review queue, review creation |
| `runner_jobs.py` | Runner job queueing and disabled local processing |
| `exam_service.py` | Exam reserve/start/submit/oral review |
| `admin_service.py` | Users, flags, analytics, notifications, curriculum versions |
| `curriculum_seed.py` | Canonical and local realistic seed |
| `worker.py` | Polling loop for transactional outbox |
| `infrastructure/database.py` | Engine/session/readiness |
| `validation.py` | Local config and expected table validation |

No SQLAlchemy ORM entity models are implemented beyond `Base`; service modules use SQL text.

## Endpoint Inventory

| Method | Path | Handler | Auth | Role | Request | Response | Errors | DB tables | Test |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/health` | `health` | No | Any | none | dict | none explicit | none | health |
| GET | `/ready` | `ready` | DB dependency | Any | none | dict | DB errors | none | none |
| GET | `/api/v1/me` | `me` | LocalAuth | active user | none | `UserProfile` | 401/403 | users | auth/e2e |
| GET | `/api/v1/dashboard` | `dashboard` | LocalAuth | active user | none | `Dashboard` | auth errors | assignments/exams | e2e |
| GET | `/api/v1/assignments` | `assignments` | LocalAuth | learner-scoped | limit | `AssignmentPage` | auth errors | task_assignments | e2e |
| GET | `/api/v1/assignments/{assignment_id}` | `assignment_detail` | LocalAuth | owner only | UUID | `AssignmentDetail` | 404 | task_assignments, submissions | e2e |
| POST | `/api/v1/uploads/presign` | `upload_presign` | LocalAuth | active user | `CreateUploadRequest` | `UploadSessionResponse` | 422 | upload_sessions | upload tests/e2e |
| POST | `/api/v1/uploads/{upload_id}/complete` | `upload_complete` | LocalAuth | owner | `CompleteUploadRequest` | upload response | 404 | upload_sessions | e2e |
| POST | `/api/v1/assignments/{assignment_id}/submissions` | `submit_assignment` | LocalAuth | owner | `CreateSubmissionRequest` | `SubmissionResponse` | 404/409 | submissions/artifacts/outbox/audit | e2e |
| GET | `/api/v1/reviews/queue` | `queue` | LocalAuth | reviewer/admin | limit | `ReviewQueuePage` | 403 | submissions | e2e |
| POST | `/api/v1/submissions/{submission_id}/reviews` | `review_submission` | LocalAuth | reviewer/admin | `CreateReviewRequest` | `ReviewResponse` | 403/404 | reviews/submissions/notifications | e2e |
| POST | `/api/v1/submissions/{submission_id}/run` | `run_submission` | LocalAuth | owner/reviewer/admin via lookup | `RunSubmissionRequest` | `RunnerJobResponse` | 404 | runner_jobs/outbox | runner unit |
| Exam/admin/notifications | Multiple | `main.py` | LocalAuth | varies | Pydantic | Pydantic | 403/404/409 | exams/admin tables | partial |

## Domain Rules

- Assignments are learner-scoped; status values are DB enum-defined.
- Submissions are immutable by version via unique `(assignment_id, submission_version)`.
- Upload validation checks filename, traversal, extension, size, SHA-256.
- Review creation updates submission status to approved or needs_revision.
- Runner job local processing redacts hidden tests and does not execute learner code when disabled.
- Exam start sets server-side `starts_at` and `deadline_at`; submit after deadline expires attempt; oral review required for pass.

## Error Handling

- FastAPI maps selected `LookupError`, `ValueError`, `PermissionError`.
- Pydantic validation maps to 422.
- DB failures generally propagate as 500 except worker retry handling.
- Transaction boundary is per request dependency in `get_session`.

## Gaps

- Missing OpenAPI endpoints listed in `api-inventory.md`.
- Idempotency-Key is required at route level but not persisted in `idempotency_keys`.
- No repository abstraction; raw SQL in services.
- No production auth adapter.
- Runner isolation not implemented.

