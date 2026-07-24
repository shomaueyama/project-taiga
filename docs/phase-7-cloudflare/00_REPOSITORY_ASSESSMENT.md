# Repository Assessment

## Application Architecture

- Frontend framework: React 19 with TypeScript and Vite.
- Frontend data access: centralized API client in `frontend/src/shared/api/client.ts`; components do
  not directly own raw `fetch` calls.
- Backend language/framework: Python 3.13, FastAPI, Pydantic 2.
- API routing model: route handlers in `backend/src/taiga/main.py`, service functions in sibling
  modules.
- Repository layout: multi-project repository with `frontend/`, `backend/`, `runner/`, `infra/`,
  and docs.
- Package managers: npm for frontend, Python packaging with setuptools for backend.
- Worker process: `backend/src/taiga/worker.py` runs an infinite SQLAlchemy polling loop.
- Runner controller: `runner/runner_controller.py` is a disabled placeholder loop.
- Scheduled jobs: no separate scheduler found; worker uses polling and sleep intervals.
- WebSocket/SSE/streaming: no WebSocket or SSE usage found.
- File persistence: local filesystem under `local-storage/` for uploads and hidden tests.
- Authentication: LocalAuth only, using `Authorization: Bearer local:<email>` or `X-Local-User`.
- Authorization: role checks in Python services.
- Email/external APIs: no production email or third-party API integration found.
- Runtime env dependencies: `APP_ENV`, `LOCAL_AUTH_ENABLED`, `DATABASE_URL`,
  `LOCAL_STORAGE_ROOT`, `CURRICULUM_SOURCE_DIR`, `RUNNER_ENABLED`, `EXAM_ENABLED`,
  `RATE_LIMIT_ENABLED`, `RATE_LIMIT_WINDOW_SECONDS`, `RATE_LIMIT_MAX_REQUESTS`,
  `WORKER_IDLE_POLL_SECONDS`, `WORKER_ERROR_RETRY_SECONDS`, `VITE_API_BASE_URL`.

## Runtime Compatibility

The current backend cannot run unchanged in Cloudflare Workers because it depends on:

- Python interpreter and Uvicorn/FastAPI server process.
- SQLAlchemy and `psycopg` direct PostgreSQL TCP connections.
- Long-running worker process with `while True`.
- Local filesystem persistence through `pathlib.Path`.
- Docker Compose service topology.

The frontend can be preserved substantially. The API and persistence layers need a rewrite or a
parallel Worker implementation.

## Background Processing Classification

| Current job/process | Current behavior | Cloudflare classification | Notes |
|---|---|---|---|
| Submission created outbox | Inserts `submission.created` event | Queue producer candidate | No current consumer behavior beyond local state. |
| Runner job outbox | Inserts and polls `runner_job.queued` | Queue producer/consumer candidate | Runner execution must remain disabled. |
| Worker loop | Polls outbox with `FOR UPDATE SKIP LOCKED` | Replace with Queue consumer or Cron | Infinite loop is not Worker-compatible. |
| Runner controller | Sleeps forever, prints enabled flag | Unsupported on Workers | Future isolated execution service required. |
| Exam deadline checks | Request-time server timestamp checks | Synchronous Worker request | Must preserve server-authoritative time. |

## Storage Mapping

| Current storage | Evidence | Cloudflare target | Notes |
|---|---|---|---|
| Frontend static assets | `frontend/src/assets/` | Worker assets or Pages | Compatible. |
| Upload metadata | `upload_sessions` table | D1 | Store metadata rows. |
| Upload files/manifests | `local-storage/uploads`, `submission_service.py` | R2 | Replace `file://` flow with R2 object keys and signed access. |
| Submission artifact keys | `submission_artifacts.s3_key` | D1 metadata plus R2 object | Existing naming concept maps well. |
| Hidden tests | `local-storage/hidden-tests`, `exam_variants.hidden_test_s3_key` | Private R2 | Must never expose hidden test contents. |
| Runner internal results | `runner_jobs.internal_result_s3_key` | R2 or external runner store | Runner remains disabled initially. |

## Authentication And Security

Production Cloudflare migration cannot use current LocalAuth. Required security decisions:

- Select Cloudflare Access, external OIDC, or Worker-managed sessions.
- Preserve learner/reviewer/admin roles.
- Replace in-memory rate limiting with Cloudflare-native or distributed controls.
- Keep current response security headers.
- Keep hidden test redaction.
- Preserve upload validation and object key containment.
- Keep `RUNNER_ENABLED=false` until a separate isolated execution architecture is approved.

## Frontend Delivery Options

Option A: Single Worker with static assets and API.

- Lowest operational surface after migration.
- Best fit for one Cloudflare account and Wrangler workflow.
- Requires API rewrite first.

Option B: Cloudflare Pages frontend plus Worker API.

- Easier frontend deployment earlier.
- Separates static hosting from API migration.
- Slightly more operational surface.

Recommendation: start with Option B or a local-only Worker skeleton, then consolidate later if the
Worker API migration succeeds.

