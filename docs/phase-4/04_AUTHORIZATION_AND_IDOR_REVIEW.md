# Authorization and IDOR Review

## Matrix

| Endpoint | Actor | Own resource | Other user resource | Reviewer scope | Admin scope | Expected status |
|---|---|---:|---:|---:|---:|---|
| `GET /api/v1/assignments/{assignmentId}` | learner | Allowed | Denied | Denied for unrelated resources | Allowed by policy | 200 or 404 |
| `GET /api/v1/submissions/{submissionId}` | learner | Allowed | Denied | Review-scoped only | Allowed by policy | 200 or 404 |
| `POST /api/v1/submissions/{submissionId}/reviews` | learner | Denied | Denied | N/A | N/A | 403 |
| `POST /api/v1/submissions/{submissionId}/reviews` | reviewer | Review-scoped | Denied outside queue/policy | Allowed when scoped | Allowed | 201/403/404 |
| `POST /api/v1/submissions/{submissionId}/run` | learner | Allowed if flag enabled | Denied | N/A | Allowed by policy | 202/404 |
| `GET /api/v1/exam-attempts/{attemptId}` | learner | Allowed | Denied | Review-scoped only | Allowed by policy | 200/404 |
| `POST /api/v1/exam-attempts/{attemptId}/oral-review` | learner | Denied | Denied | N/A | N/A | 403 |
| `POST /api/v1/admin/users/invitations` | learner/reviewer | N/A | N/A | Denied | Allowed | 403/201 |
| `POST /api/v1/admin/users/{userId}/suspend` | learner/reviewer | N/A | N/A | Denied | Allowed | 403/200 |
| `PATCH /api/v1/admin/feature-flags/{key}` | learner/reviewer | N/A | N/A | Denied | Allowed | 403/200 |

## Phase 4 Tests

- Learner access to another learner's assignment is denied.
- Learner access to another learner's submission is denied.
- Learner reviewer mutation is denied.
- Reviewer access to unrelated learner assignment is denied.
- Reviewer admin mutation is denied.
- Missing authentication on protected mutations is denied.

## Residual Work

Inactive or less-used nested-resource mismatch tests should be expanded for curriculum, notification preference mutation endpoints when those mutation APIs are introduced.
