# Validation Results

Final Phase 6 gate results were run on 2026-07-23.

| Command | Result | Notes |
|---|---|---|
| `make lint` | Passed | Backend ruff and frontend ESLint passed |
| `make typecheck` | Passed | Backend mypy and frontend TypeScript passed |
| `make test` | Passed | Backend 55 passed; frontend 12 passed |
| `make test-coverage` | Passed | Backend 90%; frontend statements 96.17%, branches 86.07%, functions 94.91%, lines 96.12% |
| `make validate` | Passed | Compose config and backend validation passed |
| `git diff --check` | Passed | No whitespace errors |
| `docker compose config --quiet` | Passed | Compose file valid |
| `docker compose build` | Passed | backend, worker, frontend, runner-controller built |
| `docker compose up -d` | Passed | Services started |
| `docker compose ps` | Passed | backend healthy, postgres healthy, frontend/worker/runner-controller running |
| `docker compose logs --tail=80` | Passed | No crash logs observed |
| `cd frontend && npm run build` | Passed | JS 394.78KB, gzip 119.01KB |
| `cd frontend && npm run test:e2e` | Passed | 10 Playwright tests passed in 5.9s after backend restart |
| `python3 scripts/perf_load.py --scenario baseline` | Passed | 200 requests, p95 34.94ms, 0% errors, 444.72 rps |
| Accessibility checks | Passed | axe violations: 0 on tested major pages |
| Responsive checks | Passed | No horizontal overflow at required widths |
| Duplicate API requests | Passed | Dashboard initial load issued one request each for health, me, dashboard, assignments, and progress |

## Docker Service State

- backend: running healthy
- frontend: running
- postgres: running healthy
- worker: running
- runner-controller: running
