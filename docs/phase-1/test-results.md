# Phase 1 Test Results

| Command | Duration | Result | Notes |
|---|---:|---|---|
| Startup inspection | <1m | PASS | Repo clean, PR #15/#16 checks passing, Compose services running |
| `make validate` baseline | 1s | PASS | Compose config and backend validation passed |
| `make lint` | 1s | PASS | ruff and ESLint passed |
| `make typecheck` | 2s | PASS | mypy and TypeScript passed |
| `make test` | 4s | PASS | Backend 26 passed; frontend 1 passed |
| `backend/tests/test_phase1_api.py` | 2s | PASS | 12 passed with enabled Exam/Runner checks |
| `make test-coverage` | 4s | PASS | Backend 72%; frontend statements 53.71% |
| `make validate` final | 1s | PASS | Compose config and `taiga.validation` passed |
| `git diff --check` | <1s | PASS | No whitespace errors |
| `docker compose down -v` | <1m | PASS | Fresh DB volume removed |
| `docker compose build --no-cache` | <1m | PASS | Backend, worker, frontend, runner-controller built |
| `docker compose up -d` | <1m | PASS | All services started |
| `make migrate` | <1m | PASS | Alembic upgraded fresh database to head |
| `make seed` first run | <1m | PASS | Seed import completed |
| `make seed` second run | <1m | PASS | Seed import completed without duplicates |
| Seed count query | <1s | PASS | 3 users, 28 weeks, 196 templates, 196 assignments, 28 exams, 56 variants |
| `docker compose restart` | <1m | PASS | Services restarted |
| `docker compose down && docker compose up -d` | <1m | PASS | Shutdown and restart passed |
| `npx playwright test` | 2s | PASS | 4 passed sequentially |
| `npx playwright test --repeat-each=3` | 4s | PASS | 12 passed sequentially |
| `npx playwright test --retries=2` | 2s | PASS | 4 passed sequentially |

## Failure and Correction Log

| Failure | Root cause | Correction | Final result |
|---|---|---|---|
| E2E admin review action flaked with a 409 | Multiple parallel tests reviewed the same first queue item | Review UI now renders per-submission actions; E2E creates and approves a specific submission | PASS |
| E2E submission creation returned 500 under parallel workers | Concurrent submissions used `max(version)+1` for the same assignment without locking | Submission creation locks the assignment row with `FOR UPDATE` before version allocation | PASS |
| E2E could not find the created submission in the review panel | Review queue returned oldest pending items and UI showed only the first five | Review queue now returns newest pending submissions first | PASS |
| Initial parallel execution of normal/repeat/retry Playwright commands interfered across separate Playwright processes | Three separate Playwright commands were launched concurrently against one shared DB | Phase gate commands were rerun sequentially | PASS |

## Console, Page Error, and 5xx Findings

The final sequential Playwright runs reported no `console.error`, `pageerror`, failed request, or HTTP
5xx findings. The earlier HTTP 500 was explained by the submission version race and fixed.
