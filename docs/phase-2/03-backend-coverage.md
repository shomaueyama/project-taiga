# Backend Coverage Plan

## Baseline

- Total: 72%.
- Tests: 26 backend tests.

## Final

- Total: 88%.
- Tests: 39 backend tests.
- Critical module coverage:
  - `admin_service.py`: 96%.
  - `assignment_queries.py`: 100%.
  - `exam_service.py`: 94%.
  - `runner_jobs.py`: 95%.
  - `submission_service.py`: 92%.

## Targeted Additions

- Admin endpoint and service tests for users, invitations, status updates, flags, analytics,
  notifications, and preferences.
- Assignment query tests for dashboard, assignment list/detail, progress, not found, and ownership.
- Submission lifecycle tests for invalid upload, metadata mismatch, accepted upload, first submission,
  version increment, and concurrent version allocation.
- Review lifecycle tests for approve, reject, duplicate review, and simultaneous review attempts.
- Exam and runner edge tests for disabled side effects, invalid order, duplicate calls, and safe
  repeated processing.
- Validation tests for expected local schema checks.

## Product-Code Change Policy

Any product-code change must be tied to a failing or newly added test and recorded in the final
report.

## Product Defects Found

- Invalid upload requests with filenames over 120 characters attempted to persist the original
  filename and failed with a database length error instead of returning a rejected upload session.
- Invalid upload requests with sizes over 50 MiB attempted to persist a value outside the database
  check constraint instead of returning a rejected upload session.
- Invalid upload requests with malformed SHA-256 values attempted to persist the malformed digest
  and failed the database check constraint instead of returning a rejected upload session.
- Review creation did not lock the submission row and did not update the related assignment status
  after approve or needs-revision decisions.
