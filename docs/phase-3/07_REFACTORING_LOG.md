# Refactoring Log

## Step 1: Inventory

Read backend route, schema, service, auth, worker, runner, frontend client, and E2E surfaces.
Recorded duplicated role checks, embedded transition rules, and OpenAPI parameter-name drift.

## Step 2: Typed Errors

Added `taiga.errors` with `AppError`, `AuthorizationError`, `FeatureDisabledError`,
`NotFoundError`, `ConflictError`, and `InvalidTransitionError`.

## Step 3: Authorization Policy

Added `taiga.authorization` and migrated admin/reviewer role checks to shared functions.

## Step 4: State Transition Policy

Added `taiga.state_transitions` and moved review, runner result, exam start/submit, and oral review
transition decisions into pure functions.

## Step 5: Service Integration

Updated admin, submission, runner, and exam services to use typed errors and transition policies.
Preserved row locks for submission creation and review decisions.

## Step 6: OpenAPI Path Alignment

Updated active FastAPI path templates to use the contract's camelCase path parameter names while
keeping runtime URLs unchanged.

## Step 7: Tests

Added `backend/tests/test_phase3_architecture.py` for transition policies, typed error response
codes, rollback after invalid oral review, and active endpoint contract inventory.
