# Validation Results

Final results from the Phase 6.5 gate run on 2026-07-24.

| Command | Result | Notes |
|---|---|---|
| `make lint` | Passed | Backend ruff and frontend ESLint passed |
| `make typecheck` | Passed | Backend mypy and frontend TypeScript passed |
| `make test` | Passed | Backend 55 pytest tests and frontend 16 Vitest tests passed |
| `make test-coverage` | Passed | Backend 90%; frontend branch coverage 88.61% |
| `make validate` | Passed | Docker Compose config and application validation passed |
| `git diff --check` | Passed | No whitespace errors in interim check |
| `docker compose config --quiet` | Passed | Compose file is valid |
| `cd frontend && npm run build` | Passed | JS 405.50KB, gzip 122.92KB |
| `docker compose build` | Passed | backend, worker, runner-controller, frontend images built |
| `docker compose up -d` | Passed | backend, worker, frontend, postgres, runner-controller started |
| `cd frontend && npm run test:e2e` | Passed | 10 Playwright tests passed in 7.9s |
| Accessibility | Passed | axe violations: 0 |
| Responsive | Passed | Required widths had no horizontal overflow |

## Performance

- Phase 6 reference bundle: JS 394.78KB, gzip 119.01KB.
- Phase 6.5 bundle: JS 405.50KB, gzip 122.92KB.
- Gzip delta: +3.91KB, within the +15KB target.
- Baseline API load smoke: 200 requests, 0.0% error rate, p95 36.83ms, throughput 420.69 RPS.
