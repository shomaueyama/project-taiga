# Unknowns and Decisions

## Unknowns

| ID | Question | Why it matters | Evidence checked | Blocking phase | Recommended owner |
|---|---|---|---|---|---|
| U-001 | Should API paths include `/api/v1` or exactly match OpenAPI paths? | Client generation and contract compliance | OpenAPI, `main.py`, frontend client | Phase 1 | Product/Backend |
| U-002 | How should design pack be available in CI? | Seed/E2E completeness | CI workflow and logs | Phase 7 | DevOps |
| U-003 | Should `EXAM_ENABLED=false` block backend exam APIs? | Security and feature rollout | `health`, `exam_service.py`, UI | Phase 1 | Product/Security |
| U-004 | Should reviewer/admin start learner exam attempts? | Permission correctness | `exam_service._attempt_row` | Phase 4 | Product/Security |
| U-005 | Required production auth adapter boundary | AWS migration | design contracts, local auth code | Phase 7 | Architecture |

## Assumptions

| ID | Assumption | Confidence | Risk if wrong | Validation method |
|---|---|---|---|---|
| A-001 | Current base branch for this Phase 0 is PR #15 local seed/E2E branch | HIGH | Baseline differs from main | Confirm with user/PR strategy |
| A-002 | Design pack remains outside app repo and read-only | HIGH | CI strategy changes | Repo layout review |
| A-003 | Local MVP can keep Runner and Exam disabled until Phase 4/5 hardening | MEDIUM | MVP acceptance gap | Product acceptance review |

## Decisions Needed

| ID | Decision | Options | Trade-off | Recommendation | Approver |
|---|---|---|---|---|---|
| D-001 | API path contract | Keep `/api/v1`; remove prefix; update OpenAPI | Compatibility vs contract purity | Decide in Phase 1 before client generation | Product/Backend |
| D-002 | CI design pack handling | Vendor fixture; checkout design repo; skip | Completeness vs repo size/secrets | Use explicit fixture or submodule-like private checkout | DevOps |
| D-003 | Runner implementation timing | Phase 1 minimal; Phase 4 security-first | MVP demo vs safety | Security-first, keep disabled | Security/Product |

