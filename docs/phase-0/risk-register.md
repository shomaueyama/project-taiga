# Risk Register

Score = Likelihood (1-5) x Impact (1-5).

| ID | Risk | Trigger | Likelihood | Impact | Score | Mitigation | Contingency | Owner phase |
|---|---|---|---:|---:|---:|---|---|---|
| R-001 | Runner enabled before isolation controls | `RUNNER_ENABLED=true` without hostile tests | 4 | 5 | 20 | Keep disabled; implement controls | Disable flag immediately | Phase 4 |
| R-002 | API contract drift blocks clients | Generated client or external consumer uses OpenAPI | 4 | 4 | 16 | Contract diff in CI | IDR and compatibility shim | Phase 1 |
| R-003 | Missing idempotency causes duplicate submissions/reviews | Double click/retry | 3 | 4 | 12 | Implement idempotency service | Manual cleanup | Phase 1 |
| R-004 | CI does not execute design-pack-dependent flows | GitHub checkout lacks design pack | 4 | 3 | 12 | Provide fixture or checkout strategy | Require local validation artifact | Phase 7 |
| R-005 | Coverage gaps hide regressions | Large service code untested | 4 | 3 | 12 | Add unit/integration matrix | Manual regression checklist | Phase 2 |
| R-006 | Production auth assumptions unclear | AWS/Cognito phase begins | 3 | 4 | 12 | Decide auth adapter boundary | Keep local-only deployment blocked | Phase 7 |
| R-007 | Docker socket exposure | Compromised worker/runner-controller | 3 | 5 | 15 | Isolate runner control plane | Remove socket mount | Phase 4 |
| R-008 | UX not enough for novice learner | User testing | 4 | 3 | 12 | Phase 6 UX/accessibility pass | Guided docs/manual workaround | Phase 6 |

