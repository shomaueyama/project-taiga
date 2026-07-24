# E2E Coverage Plan

## Baseline

- Normal: 4 passed.
- Repeat: 12 passed.
- Retries: 4 passed.

## Final

- Normal: 6 passed.
- Added reviewer request-revision followed by learner resubmission setup and admin approval.
- Added disabled runner and disabled exam mutation API checks with no traceback exposure.
- Existing page monitoring still rejects page errors, console errors, failed browser requests, and
  HTTP 5xx responses.

## Strategy

- Keep API-based per-test setup for submissions.
- Do not rely on review queue position.
- Use semantic selectors and specific submission IDs where needed.
- Add critical-path coverage only for behavior implemented in Phase 1.
- Keep console error, page error, failed request, and HTTP 5xx monitoring active.

## Browser-Level Exception

Runner-enabled and exam-enabled browser flows require restarting the local stack with different
feature flags. Phase 2 covers those enabled paths in backend integration tests and frontend
component tests, while Docker E2E remains on the default local security posture:
`RUNNER_ENABLED=false` and `EXAM_ENABLED=false`.
