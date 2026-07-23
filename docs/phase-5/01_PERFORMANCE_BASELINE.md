# Performance Baseline

Environment: macOS local Docker Desktop, PostgreSQL 17 Compose service, backend on `localhost:8000`, frontend on `localhost:5173`, measured on 2026-07-23.

## Backend Latency and Response Size

Command: local Python `urllib.request`, 10 sequential requests per endpoint.

| Endpoint | p50 ms | p95 ms | Avg ms | Bytes | Status |
|---|---:|---:|---:|---:|---:|
| `/health` | 3.58 | 6.38 | 5.50 | 77 | 200 |
| `/api/v1/dashboard` | 6.73 | 8.62 | 8.40 | 726 | 200 |
| `/api/v1/assignments` | 4.13 | 4.43 | 4.29 | 3191 | 200 |
| `/api/v1/progress` | 4.28 | 5.00 | 4.35 | 223 | 200 |
| `/api/v1/exams` | 3.70 | 4.78 | 3.85 | 3250 | 200 |

## Query Counts

Command: SQLAlchemy `before_cursor_execute` event around FastAPI `TestClient` requests.

| Endpoint | Queries | Bytes | Notes |
|---|---:|---:|---|
| `/api/v1/me` | 1 | 134 | Auth lookup only. |
| `/api/v1/dashboard` | 3 | 726 | Auth, assignment list, next exam. |
| `/api/v1/assignments?limit=20` | 2 | 3191 | Auth and assignment list. |
| `/api/v1/progress` | 4 | 223 | Auth, completed weeks, capabilities, rank. |
| `/api/v1/exams` | 2 | 3250 | Auth and exam list. |

## Seed, Migration, Startup

| Operation | Time |
|---|---:|
| `make seed` idempotent run | 2.36s |
| no-op Docker migration before Phase 5 rebuild | 1.80s |
| Phase 5 migration applied locally | 1.96s |

Backend startup was observed as healthy through Docker Compose healthcheck after `docker compose up -d`.

## Database Table Sizes

Largest seeded local tables:

| Table | Rows |
|---|---:|
| `task_templates` | 196 |
| `task_assignments` | 196 |
| `exam_variants` | 56 |
| `upload_sessions` | 53 |
| `outbox_events` | 41 |
| `submission_artifacts` | 37 |
| `submissions` | 37 |
| `audit_events` | 35 |
| `exams` | 28 |
| `weeks` | 28 |

## Frontend Bundle

Command: `cd frontend && /usr/bin/time -p npm run build`.

| Asset | Size | Gzip |
|---|---:|---:|
| `dist/index.html` | 0.39 kB | 0.26 kB |
| `dist/assets/index-DmlgYL6X.css` | 2.17 kB | 0.88 kB |
| `dist/assets/index-C5waEhjT.js` | 389.08 kB | 116.47 kB |

Build time: 2.53s wall clock. Vite build time: 438ms.

## Docker Resources

Image sizes:

| Image | Size |
|---|---:|
| `app-backend` | 373MB |
| `app-worker` | 373MB |
| `app-frontend` | 688MB |
| `app-runner-controller` | 143MB |
| `postgres:17` | 476MB |

Idle-ish container memory snapshot:

| Container | CPU | Memory |
|---|---:|---:|
| frontend | 0.00% | 336.2MiB |
| worker | 0.00% | 57.44MiB |
| backend | 17.57% | 66.3MiB |
| runner-controller | 0.00% | 4.387MiB |
| postgres | 1.13% | 67.32MiB |

Under local stress load, backend memory was 76.5MiB and CPU sample was 141.89%.
