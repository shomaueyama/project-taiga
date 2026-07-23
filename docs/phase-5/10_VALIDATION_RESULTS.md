# Validation Results

Final Phase 5 gate results were run on 2026-07-23.

| Command | Result | Notes |
|---|---|---|
| `make lint` | Passed | Backend ruff and frontend ESLint passed. |
| `make typecheck` | Passed | Backend mypy and frontend TypeScript passed. |
| `make test` | Passed | Backend 55 passed; frontend 8 passed. |
| `make test-coverage` | Passed | Backend 90%; frontend statements/lines 96.69%, branches 94.73%, functions 95.34%. |
| `make validate` | Passed | Compose config and backend validation passed. |
| `git diff --check` | Passed | No whitespace errors. |
| `docker compose config --quiet` | Passed | Compose file valid. |
| `cd frontend && npm run test:e2e` | Passed | 6 Playwright tests passed in 2.9s. |
| `docker compose build` | Passed | backend, worker, frontend, runner-controller built. |
| `docker compose up -d` | Passed | Services started with rebuilt backend/worker/frontend images. |
| `docker compose ps` | Passed | backend healthy, postgres healthy, frontend/worker/runner-controller running. |
| `cd frontend && npm run build` | Passed | JS 389.08KB, gzip 116.47KB. |
| `python3 scripts/perf_load.py --scenario baseline` | Passed | Final run: 200 requests, p95 41.01ms, 0% 5xx, 374.52 rps. |
| Query plan review | Passed | Outbox claim uses `outbox_unpublished_type_due_idx`. |
| Docker logs | Passed | No service crash logs; expected E2E traffic observed. |

## Manual Checks

- Learner dashboard: passed through Playwright.
- Assignment detail: passed through Playwright.
- Submission: passed through Playwright.
- Reviewer queue and review mutation: passed through Playwright.
- Disabled runner and exam behavior: passed through Playwright.
