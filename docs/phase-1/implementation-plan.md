# Phase 1 Implementation Plan

## Base Decision

Use `docs/phase-0-baseline-and-planning` as the base for `feat/phase-1-local-mvp-completion`.
This base includes PR #15 seed/Playwright work and PR #16 Phase 0 documentation.

## Execution Order

1. Record Phase 1 gap analysis.
2. Run baseline validation.
3. Align Exam and Runner disabled behavior in backend and frontend.
4. Enforce review state integrity.
5. Add focused backend tests for LocalAuth, roles, feature flags, review immutability, and seed invariants.
6. Update README and Phase 1 documents.
7. Run clean Docker, migration, seed, E2E, repeat, retry, and CI checks.

## Deferred Scope

- OpenAPI path/prefix reconciliation belongs to Phase 3 unless Product approves an API compatibility break.
- Isolated disposable runner belongs to Phase 4 and must remain disabled by default before hostile tests pass.
- Dedicated frontend route architecture belongs to Phase 6.
- GitHub design pack availability belongs to Phase 7.
