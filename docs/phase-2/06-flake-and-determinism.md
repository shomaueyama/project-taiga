# Flake and Determinism

## Baseline Controls

- Playwright is fully parallel.
- E2E setup creates test-specific submissions by API.
- Review actions target a specific submission by ID prefix.
- Final Phase 1 Playwright normal/repeat/retry passed sequentially.

## Phase 2 Controls

- Avoid queue order dependence.
- Avoid arbitrary sleeps.
- Use bounded polling only when waiting for worker-side state.
- Restore feature flag environment overrides after tests.
- Avoid global mocks leaking between frontend tests.
- Keep database concurrency tests bounded and close all sessions.

## Final Notes

- Playwright E2E remains parallel and targets review buttons by submission ID prefix.
- Frontend tests use fresh `QueryClient` instances and `vi.unstubAllGlobals()` after each test.
- Backend concurrency tests use bounded `ThreadPoolExecutor` workers and database row locks where
  the product behavior requires a single winning transition.
