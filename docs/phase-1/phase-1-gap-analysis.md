# Phase 1 Gap Analysis

| ID | Area | Current state | Required MVP state | Evidence | Priority | Target |
|---|---|---|---|---|---|---|
| P1-GAP-001 | Branch/base | Current branch includes PR #15 and Phase 0 docs | Phase 1 branch must include seed/E2E and Phase 0 evidence | `git log`, PR #15/#16 status | P0 | Phase 1 |
| P1-GAP-002 | Feature flags | Frontend disables Exam/Runner buttons, but backend Exam APIs and runner queue API remain callable | Disabled flags must produce safe, consistent backend behavior without 500s | `frontend/src/routes/App.tsx`, `exam_service.py`, `runner_jobs.py` | P0 | Phase 1 |
| P1-GAP-003 | Review state integrity | `create_review` updates any accessible submission, including already reviewed states | Only `manual_review_pending` submissions can be reviewed; duplicate review attempts fail safely | `submission_service.py` | P0 | Phase 1 |
| P1-GAP-004 | Auth tests | Header parser is tested, but seeded-user auth, unknown user rejection, anonymous rejection, and admin/reviewer/learner roles need API coverage | LocalAuth and protected APIs must be covered by integration tests | `backend/tests/test_auth.py` | P1 | Phase 1 |
| P1-GAP-005 | Role authorization tests | Some role checks exist in services, but direct object reference and wrong-role behavior have limited tests | Backend permission behavior must be verified | `main.py`, `submission_service.py`, `admin_service.py` | P1 | Phase 1 |
| P1-GAP-006 | Seed invariants | Seed idempotency test covers key counts, but reviewer user and exact stable count checks need strengthening | Seed twice must preserve expected users and counts | `test_local_demo_seed_integration.py` | P1 | Phase 1 |
| P1-GAP-007 | Docker clean-state evidence | Compose currently runs, but Phase 1 requires clean down/build/up/restart evidence | Clean Docker workflow must be executed and documented | `docker compose ps`, Phase 1 prompt | P1 | Phase 1 |
| P1-GAP-008 | README | README has core commands but lacks full clean-install/troubleshooting coverage | README must be usable by a new local developer | `README.md` | P1 | Phase 1 |
| P1-GAP-009 | OpenAPI parity | Implementation exposes `/api/v1` while contract paths omit it; several contract endpoints are absent | Major drift should be corrected or explicitly deferred/recorded | `docs/phase-0/api-inventory.md` | Deferred | Phase 3 |
| P1-GAP-010 | Isolated runner | Runner controller is placeholder; no disposable sandbox runner exists | Runner must remain disabled unless isolation is implemented and hostile tests pass | `runner/runner_controller.py`, `runner_jobs.py` | Deferred | Phase 4 |
| P1-GAP-011 | Full frontend routing | Frontend is a single wildcard shell | Dedicated routes/error boundaries are desirable but not required for Phase 1 if E2E core flows pass | `docs/phase-0/route-inventory.md` | Deferred | Phase 6 |
| P1-GAP-012 | CI design pack | GitHub checkout lacks read-only design pack; some seed/E2E checks skip there | CI strategy for design pack must be solved without exposing private artifacts | `.github/workflows/ci.yml` | Deferred | Phase 7 |
