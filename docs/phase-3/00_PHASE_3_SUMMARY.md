# Phase 3 Summary

Branch: `refactor/phase-3-domain-architecture`

Base: `quality/phase-2-test-coverage-reliability` at `0c62ef1`.

## Goal

Phase 3 keeps the Phase 2 Local MVP behavior intact while making backend domain rules,
authorization checks, state transitions, and error mapping easier to reason about and test.

## Implemented

- Added typed application errors in `taiga.errors`.
- Added reusable authorization policy functions in `taiga.authorization`.
- Added pure state transition policy functions in `taiga.state_transitions`.
- Refactored admin, submission, exam, and runner services to use the shared policy boundaries.
- Added FastAPI-level `AppError` mapping with stable `detail` plus machine-readable `code`.
- Aligned generated OpenAPI path parameter names with the design contract for active endpoints.
- Added Phase 3 architecture regression tests.

## Behavior

Existing Phase 2 behavior is preserved except one documented correction: oral review now rejects
non-`oral_pending` attempts with HTTP 409 instead of silently doing no state update.

## Validation Snapshot

- Backend: 43 tests passed, 89% coverage.
- Frontend: 8 tests passed, statements/lines 96.69%, branches 94.73%, functions 95.34%.
