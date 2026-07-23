# API Contract Alignment

## Summary

The Phase 3 refactor aligned active FastAPI path parameter names with the design OpenAPI contract.
The generated OpenAPI now exposes camelCase parameter names such as `{assignmentId}`,
`{submissionId}`, `{attemptId}`, and `{userId}` for active routes.

Typed application errors now include:

```json
{"detail":"Runner is disabled","code":"runner_disabled"}
```

The existing `detail` string is preserved for compatibility, while `code` gives clients a stable
machine-readable value.

## Active Endpoint Matrix

| Endpoint | Method | Actor | Request model | Success response | Error responses | Flag dependency | Test coverage |
|---|---|---|---|---|---|---|---|
| `/me` | GET | authenticated | none | `UserProfile` | 401/403 | none | auth tests |
| `/dashboard` | GET | learner | none | `Dashboard` | 401 | none | Phase 2 |
| `/assignments` | GET | learner | query | `AssignmentPage` | 401 | none | Phase 2/E2E |
| `/assignments/{assignmentId}` | GET | learner owner | path | `AssignmentDetail` | 404 | none | Phase 2 |
| `/uploads/presign` | POST | learner | `CreateUploadRequest` | `UploadSessionResponse` | 422 | none | Phase 2 |
| `/uploads/{uploadId}/complete` | POST | upload owner | `CompleteUploadRequest` | `UploadSessionResponse` | 404 | none | Phase 2 |
| `/uploads/{uploadId}` | GET | upload owner | path | `UploadSessionResponse` | 404 | none | Phase 3 |
| `/assignments/{assignmentId}/submissions` | POST | learner owner | `CreateSubmissionRequest` | `SubmissionResponse` | 404/409 | none | Phase 2/3 |
| `/submissions/{submissionId}` | GET | owner/reviewer/admin | path | `SubmissionDetail` | 404 | none | Phase 2 |
| `/submissions/{submissionId}/run` | POST | accessible submission | `RunSubmissionRequest` | `RunnerJobResponse` | 403/404 | `RUNNER_ENABLED` | Phase 2/3/E2E |
| `/submissions/{submissionId}/reviews` | POST | reviewer/admin | `CreateReviewRequest` | `ReviewResponse` | 403/404/409 | none | Phase 2/E2E |
| `/reviews/queue` | GET | reviewer/admin | query | `ReviewQueuePage` | 403 | none | Phase 2/E2E |
| `/exams` | GET | learner | query | `ExamPage` | 401 | none | Phase 2 |
| `/exams/{examId}/attempts` | POST | learner | `CreateExamAttemptRequest` | `ExamAttemptResponse` | 403/409 | `EXAM_ENABLED` | Phase 2/3 |
| `/exam-attempts/{attemptId}` | GET | owner/reviewer/admin | path | `ExamAttemptDetail` | 404 | none | Phase 2 |
| `/exam-attempts/{attemptId}/start` | POST | owner | `StartExamRequest` | `ExamAttemptDetail` | 403/409 | `EXAM_ENABLED` | Phase 2 |
| `/exam-attempts/{attemptId}/submit` | POST | owner | `SubmitExamRequest` | `ExamAttemptDetail` | 403/404 | `EXAM_ENABLED` | Phase 2 |
| `/exam-attempts/{attemptId}/oral-review` | POST | reviewer/admin | `OralReviewRequest` | `ExamAttemptDetail` | 403/404/409 | `EXAM_ENABLED` | Phase 2/3 |
| `/progress` | GET | learner | none | `Progress` | 401 | none | Phase 2 |
| `/notifications` | GET | authenticated | query | `NotificationPage` | 401 | none | Phase 2 |
| `/notification-preferences` | GET | authenticated | none | `NotificationPreferenceList` | 401 | none | Phase 2 |
| `/admin/users` | GET | admin | query | `PageUserProfile` | 403 | none | Phase 2 |
| `/admin/users/invitations` | POST | admin | `InviteUserRequest` | `UserProfile` | 403 | none | Phase 2 |
| `/admin/users/{userId}/suspend` | POST | admin | path | `UserProfile` | 403/404 | none | Phase 2 |
| `/admin/users/{userId}/restore` | POST | admin | path | `UserProfile` | 403/404 | none | Phase 2 |
| `/admin/curriculum/versions` | GET | admin | query | `CurriculumVersionPage` | 403 | none | Phase 2 |
| `/admin/feature-flags` | GET | admin | none | `FeatureFlagList` | 403 | none | Phase 2 |
| `/admin/feature-flags/{key}` | PATCH | admin | `UpdateFeatureFlagRequest` | `FeatureFlag` | 403/404 | none | Phase 2 |
| `/admin/analytics/learning` | GET | admin | none | `LearningAnalytics` | 403 | none | Phase 2 |
| `/health/live` | GET | anonymous | none | health | 200 | none | validation |
| `/health/ready` | GET | anonymous | none | readiness | 200 | none | validation |

## Known Contract Gaps

- AI usage endpoints are present in the design OpenAPI contract but not implemented in the Local
  MVP.
- Notification read/update and curriculum import endpoints are present in the design contract but
  not implemented in the Local MVP.
- Native FastAPI validation errors still use the FastAPI 422 shape.
