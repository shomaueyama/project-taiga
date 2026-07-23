# Security Baseline

| ID | Finding | Evidence | Severity | Likelihood | Impact | Owner phase | Recommendation |
|---|---|---|---|---|---|---|---|
| SEC-001 | LocalAuth is correctly restricted to local env by settings validation | `config.py`, `auth.py`, tests | INFO | Low | Prevents accidental prod LocalAuth | Phase 1 | Keep fail-fast and add startup test in Docker |
| SEC-002 | Docker socket mounted into worker and runner-controller | `docker-compose.yml` | HIGH | Medium | Container breakout risk if compromised | Phase 4 | Minimize socket use; isolate runner controller |
| SEC-003 | Runner isolation controls are not implemented | `runner_controller.py`, `runner_jobs.py` | HIGH | High | Learner code execution would be unsafe if enabled | Phase 4 | Keep `RUNNER_ENABLED=false` until hostile tests pass |
| SEC-004 | Upload validation is partial | `submission_service.py` | MEDIUM | Medium | MIME/symlink/archive risks remain | Phase 4 | Implement full upload policy from design |
| SEC-005 | Idempotency table exists but route idempotency is not enforced | migration, `main.py` | MEDIUM | Medium | Duplicate actions possible | Phase 1 | Implement idempotency service |
| SEC-006 | CORS allows only localhost frontend | `main.py` | INFO | Low | Appropriate for local MVP | Phase 7 | Revisit production origins |
| SEC-007 | No rate limiting or CSRF controls | No middleware observed | MEDIUM | Medium | Abuse risk in production | Phase 4 | Add production security plan |
| SEC-008 | Secret scan is grep-based | CI workflow | LOW | Medium | Limited detection | Phase 4 | Add dedicated secret scanning |

No secret values were recorded in Phase 0.

