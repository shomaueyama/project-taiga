# Architecture Baseline

## System Overview

Project Taiga is a local-first learning platform MVP implemented as a modular-monolith FastAPI backend, React frontend, PostgreSQL data store, worker process, and runner-controller placeholder.

Evidence:

- `backend/src/taiga/main.py`
- `frontend/src/routes/App.tsx`
- `docker-compose.yml`
- `backend/alembic/versions/0001_initial_schema.py`
- `runner/runner_controller.py`

## Context Diagram

```mermaid
flowchart LR
  Learner[Learner / 上山 虎雅]
  Admin[Admin / 上山 捷馬]
  Browser[Browser]
  App[Project Taiga Local MVP]
  Design[Read-only Design Pack]
  Docker[Docker Engine]

  Learner --> Browser
  Admin --> Browser
  Browser --> App
  App --> Design
  App --> Docker
```

## Container Diagram

```mermaid
flowchart TD
  Browser --> Frontend[Vite React frontend]
  Frontend --> Backend[FastAPI backend]
  Backend --> Postgres[(PostgreSQL 17)]
  Backend --> Storage[local-storage]
  Backend --> Outbox[outbox_events]
  Worker[Worker process] --> Postgres
  Worker --> Outbox
  RunnerController[runner-controller placeholder] --> DockerSock[Docker socket]
  Worker --> Storage
```

## Data Flows

### Authentication

```mermaid
sequenceDiagram
  participant UI as Frontend
  participant API as FastAPI
  participant DB as PostgreSQL
  UI->>API: Authorization: Bearer local:<email>
  API->>API: Settings require APP_ENV=local and LOCAL_AUTH_ENABLED=true
  API->>DB: SELECT users WHERE cognito_sub=:email
  DB-->>API: active user row
  API-->>UI: UserProfile
```

Evidence: `auth.py`, `config.py`, `users` table.

### Submission and Review

```mermaid
sequenceDiagram
  participant UI
  participant API
  participant DB
  UI->>API: POST /uploads/presign
  API->>DB: INSERT upload_sessions
  UI->>API: POST /uploads/{id}/complete
  API->>DB: UPDATE upload_sessions accepted/rejected
  UI->>API: POST /assignments/{id}/submissions
  API->>DB: INSERT submissions, submission_artifacts, outbox_events, audit_events
  UI->>API: POST /submissions/{id}/reviews
  API->>DB: INSERT reviews, UPDATE submissions, INSERT notifications
```

Evidence: `submission_service.py`.

### Runner and Worker

```mermaid
sequenceDiagram
  participant API
  participant DB
  participant Worker
  API->>DB: INSERT runner_jobs and outbox_events
  Worker->>DB: poll outbox_events if table exists
  Worker->>DB: mark runner_jobs succeeded/security_rejected
  Worker->>DB: store sanitized_result_json
```

UNKNOWN: Disposable isolated Docker runner is not implemented. Current behavior is disabled/local sanitized job processing.

### Exam

```mermaid
stateDiagram-v2
  [*] --> ready: reserve_attempt
  ready --> in_progress: start_attempt
  in_progress --> oral_pending: submit_attempt before deadline
  in_progress --> expired: submit_attempt after deadline
  oral_pending --> passed: oral_review passed
  oral_pending --> failed: oral_review failed
```

Evidence: `exam_service.py`, `exam_attempt_status` enum.

## Failure Behavior

- Database readiness: `/ready` calls `database_ready`.
- Worker: catches `SQLAlchemyError`, sleeps, retries.
- Missing `outbox_events`: worker checks `to_regclass` before querying.
- Runner controller: logs startup and sleeps; no runner orchestration yet.
- LocalAuth outside local: `Settings` validation raises `ValueError`.

