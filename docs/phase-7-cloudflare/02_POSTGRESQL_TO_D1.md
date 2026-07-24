# PostgreSQL To D1 Report

## 1. Current Database Architecture

The backend uses SQLAlchemy sessions over a PostgreSQL URL:

- `backend/src/taiga/infrastructure/database.py`
- `DATABASE_URL=postgresql+psycopg://...`
- Alembic migrations under `backend/alembic/versions/`

The application mostly uses raw SQL through `sqlalchemy.text()` rather than ORM models.

## 2. ORM Compatibility

Current SQLAlchemy + `psycopg` is not directly compatible with Cloudflare D1. Workers access D1
through bindings from JavaScript/TypeScript, not through Python TCP connections.

Recommendation: introduce a repository/service boundary and implement a D1 adapter in TypeScript.
Do not try to run the current Python backend inside Workers.

## 3. Schema Compatibility

PostgreSQL-specific schema dependencies:

| Dependency | Evidence | Why PostgreSQL-specific | D1 compatibility | Replacement | Risk |
|---|---|---|---|---|---|
| `CREATE EXTENSION pgcrypto` | `backend/alembic/versions/0001_initial_schema.py:19` | PostgreSQL extension for UUID defaults | Not compatible | Generate UUIDs in application with Web Crypto | Medium |
| PostgreSQL enum types | `0001_initial_schema.py:21-29` | `CREATE TYPE ... AS ENUM` | Not compatible | `TEXT CHECK(value IN (...))` | Medium |
| `uuid` columns and `gen_random_uuid()` | `0001_initial_schema.py:31-32` and many tables | PostgreSQL UUID type/default | Store UUID as `TEXT`; generate in app | Medium |
| `jsonb` and `jsonb_typeof` | `0001_initial_schema.py:54-55`, `83`, `101`, `168` | PostgreSQL binary JSON and functions | Store JSON text; optional SQLite JSON functions | High |
| `timestamptz` and `now()` | `0001_initial_schema.py:35`, service SQL | PostgreSQL timezone-aware timestamp type/function | Store UTC ISO text or epoch integer | Medium |
| Regex CHECK `~` | `0001_initial_schema.py:41`, `72`, `82`, `92` | PostgreSQL regex operator | Not compatible | Validate in application plus simple checks | Medium |
| `inet` | `0001_initial_schema.py:161` | PostgreSQL network address type | Not compatible | Store IP as text | Low |
| Partial indexes | `0001_initial_schema.py:172`, `184`; `0002_phase5_performance_indexes.py` | PostgreSQL partial index syntax in Alembic | SQLite supports partial indexes, but migration syntax differs | D1 SQL partial index where supported; verify locally | Medium |

## 4. Migration Compatibility

Alembic migrations cannot be reused as-is for D1. A parallel D1 migration set is required. Keep
Alembic unchanged for local Docker and future AWS.

## 5. Query Compatibility

PostgreSQL-specific query dependencies:

| Dependency | Evidence | D1 compatibility | Proposed replacement | Risk |
|---|---|---|---|---|
| Enum casts `status::text`, `role::text` | `backend/src/taiga/auth.py`, `assignment_queries.py`, `submission_service.py` | Not compatible | Store enum values as text; remove casts | Low |
| `CAST(:payload AS jsonb)` | `backend/src/taiga/runner_jobs.py:95`, `submission_service.py:344`, `exam_service.py:131` | Not compatible | Store canonical JSON string | Medium |
| JSON operator `->>` | `backend/src/taiga/exam_service.py:50` | Different syntax | Parse in application or use SQLite JSON extraction | Medium |
| `id = ANY(:upload_ids)` | `backend/src/taiga/submission_service.py:260` | Not compatible | Build parameterized `IN (?, ?, ...)` | Medium |
| `FOR UPDATE` | `submission_service.py:243`, `exam_service.py:99` | Not compatible | Optimistic update with version columns or Durable Object serialization | High |
| `FOR UPDATE SKIP LOCKED` | `runner_jobs.py:140` | Not compatible | Cloudflare Queue delivery/visibility timeout semantics | High |
| `to_regclass('public.outbox_events')` | `runner_jobs.py:126` | Not compatible | Remove table-existence runtime check | Low |
| Intervals `now() + interval '1 minute'` | `runner_jobs.py:173`, `exam_service.py:216` | Not compatible | Compute ISO timestamps in Worker code | Medium |
| `RETURNING` | `backend/src/taiga/admin_service.py` | SQLite supports `RETURNING` in modern versions, but verify D1 | Use follow-up select if needed | Low |

## 6. Transaction Compatibility

Critical atomic flows:

- Submission creation: assignment lock, accepted upload check, version calculation, submission insert,
  artifact inserts, outbox, audit event.
- Exam reservation: variant selection and attempt creation.
- Review: review insert, submission update, assignment update, notification insert.
- Runner outbox claim: row-lock claim and retry update.

D1 migration must preserve these with explicit transactions, unique constraints, idempotency, or
Durable Objects. The runner claim flow should become Queue-based rather than an outbox polling loop.

## 7. Concurrency Risks

Main risks:

- Duplicate submission versions if `max(version)+1` is raced.
- Duplicate exam variant reservation without `FOR UPDATE`.
- Runner job double-processing without `SKIP LOCKED`.
- In-memory rate limiter losing global consistency across Worker isolates.

Use unique constraints, retry-on-conflict, D1 transactions, and Queue delivery semantics.

## 8. Timestamp And Timezone Behavior

Current schema uses `timestamptz` and `now()`. D1 should store UTC ISO 8601 strings or epoch
milliseconds generated by the Worker. Browser time must not be authoritative for exams.

## 9. Data Migration Strategy

1. Freeze writes during migration rehearsal.
2. Export PostgreSQL rows to normalized JSON or CSV.
3. Transform UUID/timestamp/jsonb/enum fields into D1-compatible text.
4. Import to local D1 first.
5. Run contract and E2E tests.
6. Repeat against preview D1 after owner approval.

## 10. Rollback Strategy

Before cutover, keep PostgreSQL as the source of truth. During a short cutover window, either block
writes or dual-write only after tests exist. Rollback means returning DNS/API traffic to the
PostgreSQL backend and discarding preview D1 writes.

## 11. Local Development Strategy

Keep Docker Compose as the current MVP path. Add a separate Wrangler local path only after CF-1:

- Worker dev server.
- Local D1 database.
- R2 local bindings or mocked object storage.
- Contract tests comparing Worker API responses to current FastAPI responses.

## 12. Test Strategy

- Preserve current backend tests for PostgreSQL.
- Add route-level contract fixtures.
- Add D1 migration validation.
- Add concurrency tests for submission versioning and exam variant reservation.
- Add R2 upload flow tests.
- Add Cloudflare Worker unit tests.

## 13. Complete PostgreSQL-Specific Dependencies

Complete enough for migration planning:

- PostgreSQL DDL: extension, enum, UUID, `jsonb`, `timestamptz`, regex checks, `inet`, partial indexes.
- Raw SQL casts: `::text`, `CAST(... AS jsonb)`.
- JSON operator `->>`.
- `ANY(:upload_ids)`.
- `FOR UPDATE` and `FOR UPDATE SKIP LOCKED`.
- `to_regclass`.
- `now()`, `interval`.
- SQLAlchemy session/transaction lifecycle and `psycopg` driver.

## 14. Recommendation

Replace the runtime persistence implementation for Cloudflare rather than adapting the current
SQLAlchemy implementation. Retain PostgreSQL/Alembic for Docker local MVP and AWS future path until
Cloudflare migration is proven.

