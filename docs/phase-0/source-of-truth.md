# Source of Truth Baseline

## Confirmed Authority Order

The project already declares a canonical priority in `../design/taiga-42-v4.0-implementation-pack/01_SOURCE_OF_TRUTH.md`. Phase 0 adopts that order because it is explicit and current:

1. `01_SOURCE_OF_TRUTH.md`
2. `contracts/openapi/openapi.json`
3. `contracts/database/001_initial_schema.sql`
4. `contracts/platform/system_architecture.json`
5. `contracts/state-machines/`
6. `contracts/security/`
7. `curriculum/canonical_source_registry.json`
8. `02_LOCAL_MVP_IMPLEMENTATION.md`
9. `reference/design-docs/`
10. `reference/diagrams/`
11. `reference/adrs/`
12. `reference/historical/`

Implementation files are evidence of the current baseline but are not higher authority than contracts.

## Authority Matrix

| ID | Topic | Candidate source | Current authority | Evidence | Conflicts | Confidence |
|---|---|---|---|---|---|---|
| SOT-001 | Source priority | Design pack | `01_SOURCE_OF_TRUTH.md` | File explicitly defines conflict policy | None found | HIGH |
| SOT-002 | HTTP API | OpenAPI and FastAPI | `contracts/openapi/openapi.json` | OpenAPI lists additional endpoints beyond `backend/src/taiga/main.py` | Implementation missing ai-usage, notification read, preference update, curriculum import APIs | HIGH |
| SOT-003 | Physical DB | DDL and Alembic | `contracts/database/001_initial_schema.sql` then `backend/alembic/versions/0001_initial_schema.py` | Alembic creates 24 expected tables | Need full DDL drift diff in Phase 1 | MEDIUM |
| SOT-004 | Runtime topology | Local MVP contract and Compose | `02_LOCAL_MVP_IMPLEMENTATION.md`; runtime evidence from `docker-compose.yml` | Services match required names | Runner is placeholder, not isolated container runner | HIGH |
| SOT-005 | State machines | Design contracts and enums | `contracts/state-machines/` | DB enums reflect assignment/submission/runner/exam statuses | Enforcement incomplete in service code | MEDIUM |
| SOT-006 | Security controls | Security contracts and implementation | `contracts/security/` | LocalAuth fail-fast exists in `config.py`; upload checks exist | Runner isolation controls not implemented | MEDIUM |
| SOT-007 | Curriculum seed | Curriculum files | `curriculum/canonical_source_registry.json` and JSON files | Seed imports 28/196/28/56 canonical counts when design pack present | GitHub checkout lacks design pack, CI skips local seed test | HIGH |
| SOT-008 | Frontend behavior | React implementation | `frontend/src/routes/App.tsx` for current UI | Single wildcard route renders Local MVP shell | Design references imply more routes than implemented | HIGH |
| SOT-009 | Tests | Test files and CI | Current tests | Backend 14 tests, frontend 1 unit, Playwright 4 E2E | Coverage below 100%; broad API gaps | HIGH |
| SOT-010 | Operations | README/Makefile/CI | Makefile and `.github/workflows/ci.yml` | Commands executed successfully locally; PR checks passing | CI skips design-pack-dependent E2E when design pack absent | HIGH |

## Conflicts and Phase Assignment

| ID | Conflict | Evidence | Target phase |
|---|---|---|---|
| C-001 | OpenAPI has endpoints not implemented in FastAPI | OpenAPI includes `/submissions/{submissionId}/ai-usage`, `/notifications/{notificationId}/read`, preference `put`, curriculum import APIs; `main.py` lacks them | Phase 1 |
| C-002 | Local MVP contract requires isolated Docker runner; implementation records disabled/sanitized jobs only | `02_LOCAL_MVP_IMPLEMENTATION.md`; `runner/runner_controller.py`; `runner_jobs.py` | Phase 1 or Phase 4 |
| C-003 | Frontend design implies multiple pages; implementation has one wildcard route | `frontend/src/main.tsx`; `App.tsx` | Phase 6 |
| C-004 | Coverage goal in previous testing prompt was 100%; measured coverage is lower | `make test-coverage`: Backend 53%, Frontend statements 53.27% | Phase 2 |
| C-005 | Design pack unavailable in normal GitHub checkout, so seed/E2E paths are conditional | CI logs and `.github/workflows/ci.yml` | Phase 7 |

