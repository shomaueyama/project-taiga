# Technical Debt Register

| ID | Category | Debt | Evidence | Impact | Effort | Risk | Priority | Target phase |
|---|---|---|---|---|---|---|---|---|
| TD-001 | API | OpenAPI and FastAPI route surface mismatch | `api-inventory.md` | Contract drift | M | High | P1 | Phase 1 |
| TD-002 | Backend | Idempotency table unused | migration vs services | Duplicate side effects | M | Medium | P1 | Phase 1 |
| TD-003 | Runner | Isolated runner not implemented | `runner_controller.py` | Cannot safely enable runner | L | High | P1 | Phase 4 |
| TD-004 | Frontend | Single wildcard route | `main.tsx` | Poor navigation and test coverage | M | Medium | P2 | Phase 6 |
| TD-005 | Test | Coverage below target | `test-baseline.md` | Quality gate weak | L | Medium | P1 | Phase 2 |
| TD-006 | CI | E2E skipped without design pack | `ci.yml` | CI may miss local regressions | M | Medium | P2 | Phase 7 |
| TD-007 | Docker | Containers run as root, no resource limits | Dockerfiles/Compose | Security hardening gap | M | High | P1 | Phase 4 |
| TD-008 | Observability | No structured logging/metrics/tracing | code review | Hard to operate production | M | Medium | P2 | Phase 7 |
| TD-009 | Database | No ORM model or migration drift automation | `database.py`, migrations | Harder schema governance | M | Medium | P2 | Phase 1 |
| TD-010 | UX | No dedicated error/loading/empty components | frontend inventory | UX inconsistency | M | Low | P2 | Phase 6 |

