# API Inventory

## Implemented FastAPI Endpoints

The implemented endpoints are extracted from `backend/src/taiga/main.py`.

| Method | Path | Implemented | OpenAPI contract match |
|---|---|---|---|
| GET | `/health` | yes | local non-contract endpoint |
| GET | `/ready` | yes | local non-contract endpoint |
| GET | `/api/v1/health/live` | yes | path differs from contract `/health/live` |
| GET | `/api/v1/health/ready` | yes | path differs from contract `/health/ready` |
| GET | `/api/v1/me` | yes | contract has `/me` without prefix |
| GET | `/api/v1/dashboard` | yes | contract has `/dashboard` without prefix |
| GET | `/api/v1/assignments` | yes | contract has `/assignments` without prefix |
| GET | `/api/v1/assignments/{assignment_id}` | yes | parameter casing differs from `assignmentId` |
| POST | `/api/v1/uploads/presign` | yes | prefix difference |
| POST | `/api/v1/uploads/{upload_id}/complete` | yes | parameter casing differs |
| GET | `/api/v1/uploads/{upload_id}` | yes | parameter casing differs |
| POST | `/api/v1/assignments/{assignment_id}/submissions` | yes | parameter casing differs |
| GET | `/api/v1/submissions/{submission_id}` | yes | parameter casing differs |
| POST | `/api/v1/submissions/{submission_id}/run` | yes | parameter casing differs |
| POST | `/api/v1/submissions/{submission_id}/reviews` | yes | parameter casing differs |
| GET | `/api/v1/reviews/queue` | yes | prefix difference |
| GET | `/api/v1/exams` | yes | prefix difference |
| POST | `/api/v1/exams/{exam_id}/attempts` | yes | parameter casing differs |
| GET | `/api/v1/exam-attempts/{attempt_id}` | yes | parameter casing differs |
| POST | `/api/v1/exam-attempts/{attempt_id}/start` | yes | parameter casing differs |
| POST | `/api/v1/exam-attempts/{attempt_id}/submit` | yes | parameter casing differs |
| POST | `/api/v1/exam-attempts/{attempt_id}/oral-review` | yes | parameter casing differs |
| GET | `/api/v1/progress` | yes | prefix difference |
| GET | `/api/v1/notifications` | yes | prefix difference |
| GET | `/api/v1/notification-preferences` | yes | prefix difference |
| GET | `/api/v1/admin/users` | yes | prefix difference |
| POST | `/api/v1/admin/users/invitations` | yes | prefix difference |
| POST | `/api/v1/admin/users/{user_id}/suspend` | yes | parameter casing differs |
| POST | `/api/v1/admin/users/{user_id}/restore` | yes | parameter casing differs |
| GET | `/api/v1/admin/feature-flags` | yes | prefix difference |
| PATCH | `/api/v1/admin/feature-flags/{key}` | yes | prefix difference |
| GET | `/api/v1/admin/analytics/learning` | yes | prefix difference |
| GET | `/api/v1/admin/curriculum/versions` | yes | prefix difference |

## Contract Endpoints Not Implemented

- `/submissions/{submissionId}/ai-usage` POST/GET.
- `/notifications/{notificationId}/read` POST.
- `/notification-preferences` PUT.
- `/admin/curriculum/imports/dry-run` POST.
- `/admin/curriculum/imports/{importId}` GET.
- `/admin/curriculum/imports/{importId}/diff` GET.
- `/admin/curriculum/imports/{importId}/publish` POST.

## API Risks

- API prefix mismatch with design contract should be resolved or recorded as an IDR.
- Idempotency-Key headers are validated by FastAPI but not persisted.
- Error catalog mapping is incomplete.

