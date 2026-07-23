# Frontend Coverage Plan

## Baseline

- Statements: 53.71%.
- Branches: 72.63%.
- Functions: 18.6%.
- Lines: 53.71%.
- Tests: 1 component test.

## Final

- Statements: 96.69%.
- Branches: 94.73%.
- Functions: 95.34%.
- Lines: 96.69%.
- Tests: 8 Vitest tests across App and API client coverage.

## Targeted Additions

- API client tests for success, auth header, idempotency header, response parsing, and failure paths.
- App tests for learner, reviewer, admin, disabled Exam/Runner states, enabled Exam/Runner states,
  review action success/error, submission success/error, and role visibility.
- Query/provider test helper with isolated `QueryClient` per test.

Tests should use semantic queries and user-observable assertions.

## Added Coverage

- API client parsing, auth header, idempotency header, request body, and failure behavior.
- App learner shell, disabled runner/exam states, demo submission, enabled runner action, admin
  panels, review action, and enabled exam flow.
- Query cache isolation by creating a fresh `QueryClient` per test and clearing global mocks after
  each test.
