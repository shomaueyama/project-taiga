# Attack Surface Inventory

| Method | Path | Auth | Roles | Ownership | Inputs | Side Effects | Flag | Risk | Tests |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/health`, `/ready`, `/api/v1/health/*` | No | Public | None | None | None | None | Rate probing | Phase 4 headers/rate limit |
| GET | `/api/v1/me` | Yes | All active | Self | Local auth header | None | LocalAuth | Spoofing in local mode | Existing auth tests |
| GET | `/api/v1/dashboard` | Yes | Learner/admin | Principal-scoped | None | None | None | IDOR | Existing learning tests |
| GET | `/api/v1/assignments` | Yes | Learner/admin | Principal-scoped | `limit` capped at 100 | None | None | Enumeration | Existing and Phase 4 |
| GET | `/api/v1/assignments/{assignmentId}` | Yes | Learner/admin | Assignment owner | UUID path | None | None | IDOR | Phase 4 cross-user |
| GET | `/api/v1/progress` | Yes | Learner/admin | Principal-scoped | None | None | None | Sensitive progress data | Existing tests |
| POST | `/api/v1/uploads/presign` | Yes | Learner/admin | Principal-owned upload | filename, media type, size, sha | Creates upload record | None | Path traversal, spoofing, mass assignment | Phase 4 |
| POST | `/api/v1/uploads/{uploadId}/complete` | Yes | Learner/admin | Upload owner | UUID path, size, sha | Completes upload | None | Cross-user upload completion | Existing tests |
| GET | `/api/v1/uploads/{uploadId}` | Yes | Learner/admin | Upload owner | UUID path | None | None | Cross-user upload read | Existing tests |
| POST | `/api/v1/assignments/{assignmentId}/submissions` | Yes | Learner/admin | Assignment owner | UUID path, source, URLs, upload IDs | Creates immutable submission version | None | Nested resource mismatch | Existing tests |
| GET | `/api/v1/submissions/{submissionId}` | Yes | Learner/reviewer/admin | Owner or reviewer policy | UUID path | None | None | IDOR, hidden result exposure | Phase 4 |
| GET | `/api/v1/reviews/queue` | Yes | Reviewer/admin | Reviewer queue | `limit` capped at 100 | None | None | Unauthorized queue access | Existing tests |
| POST | `/api/v1/submissions/{submissionId}/reviews` | Yes | Reviewer/admin | Reviewer policy | result, rubric, comment | Creates review and state transition | None | Role escalation | Phase 4 |
| POST | `/api/v1/submissions/{submissionId}/run` | Yes | Learner/admin | Submission owner | reason | Queues runner job/outbox | `RUNNER_ENABLED` | Command injection, replay | Phase 4 |
| GET | `/api/v1/exams` | Yes | Learner/admin | Principal-scoped | `limit` capped at 100 | None | None | Exam metadata disclosure | Existing tests |
| POST | `/api/v1/exams/{examId}/attempts` | Yes | Learner/admin | Principal exam | UUID path, request body | Reserves variant snapshot | `EXAM_ENABLED` | Variant leak, replay | Existing tests |
| GET | `/api/v1/exam-attempts/{attemptId}` | Yes | Learner/reviewer/admin | Attempt owner or reviewer policy | UUID path | None | None | IDOR | Existing tests |
| POST | `/api/v1/exam-attempts/{attemptId}/start` | Yes | Learner/admin | Attempt owner | UUID path | Starts server deadline | `EXAM_ENABLED` | Deadline bypass | Existing tests |
| POST | `/api/v1/exam-attempts/{attemptId}/submit` | Yes | Learner/admin | Attempt owner | answers | Persists first valid submission | `EXAM_ENABLED` | Replay, hidden test leak | Existing tests |
| POST | `/api/v1/exam-attempts/{attemptId}/oral-review` | Yes | Reviewer/admin | Reviewer policy | result, notes, score | Oral review transition | `EXAM_ENABLED` | Role escalation | Existing and Phase 4 auth |
| GET | `/api/v1/notifications` | Yes | All active | Principal-scoped | `limit` capped at 100 | None | None | Cross-user disclosure | Existing tests |
| GET | `/api/v1/notification-preferences` | Yes | All active | Principal-scoped | None | None | None | Preference disclosure | Existing tests |
| GET | `/api/v1/admin/users` | Yes | Admin | Admin scope | `limit` capped at 100 | None | None | User enumeration | Existing tests |
| POST | `/api/v1/admin/users/invitations` | Yes | Admin | Admin scope | email, name, role | Creates local user | None | Privilege escalation | Phase 4 |
| POST | `/api/v1/admin/users/{userId}/suspend` | Yes | Admin | Admin scope | UUID path | Status mutation | None | Account takeover/DoS | Existing tests |
| POST | `/api/v1/admin/users/{userId}/restore` | Yes | Admin | Admin scope | UUID path | Status mutation | None | Account takeover | Existing tests |
| GET | `/api/v1/admin/feature-flags` | Yes | Admin | Admin scope | None | None | None | Flag disclosure | Existing tests |
| PATCH | `/api/v1/admin/feature-flags/{key}` | Yes | Admin | Admin scope | key, enabled | Flag mutation | None | Feature bypass | Existing tests |
| GET | `/api/v1/admin/analytics/learning` | Yes | Admin | Admin scope | None | None | None | Aggregate disclosure | Existing tests |
| GET | `/api/v1/admin/curriculum/versions` | Yes | Admin | Admin scope | `limit` capped at 100 | None | None | Curriculum metadata disclosure | Existing tests |

Worker processing is not HTTP-exposed. It reads unpublished `runner_job.queued` outbox events and updates runner job, submission, and outbox state in one database transaction.
