# Phase 1 to 8 Execution Plan

## Phase 1 - Local MVP Completion

- Scope: API contract reconciliation, idempotency, seed/migration reliability, LocalAuth, core flows.
- Out of scope: production AWS deployment.
- Inputs: Phase 0 inventories, OpenAPI, DB contract.
- Deliverables: contract-aligned APIs, full local startup guide, migrations/seed green.
- Entry: Phase 0 docs approved.
- Exit: local fresh clone can migrate/seed/run core API flows.
- Quality gate: lint/typecheck/test/validate/E2E pass.
- Effort: L.
- Branch: `feat/phase-1-local-mvp-completion`.

## Phase 2 - Test and Quality Assurance

- Scope: unit/integration/component/E2E matrix, coverage thresholds, flake reduction.
- Deliverables: requirement test matrix, coverage gates, CI artifacts.
- Entry: Phase 1 contract stable.
- Exit: agreed coverage thresholds met; critical flows tested.
- Effort: L.
- Branch: `test/phase-2-quality-assurance`.

## Phase 3 - Staff Engineer Review

- Scope: architecture boundaries, SOLID, duplication, naming, maintainability.
- Deliverables: review findings and focused refactor PRs.
- Entry: tests sufficient to protect refactors.
- Exit: P1 architecture debt addressed or tracked.
- Effort: M.
- Branch: `refactor/phase-3-staff-review`.

## Phase 4 - Security Audit

- Scope: authz, runner isolation, upload security, Docker hardening, supply chain.
- Deliverables: security controls, hostile runner tests, secret scanning.
- Entry: core flows stable.
- Exit: Runner can be safely evaluated or remains disabled with accepted risk.
- Effort: L.
- Branch: `security/phase-4-audit`.

## Phase 5 - Performance

- Scope: API latency, DB queries, worker polling, bundle/image size.
- Deliverables: performance baseline and fixes.
- Entry: observability hooks sufficient for measurement.
- Exit: agreed local SLOs met.
- Effort: M.
- Branch: `perf/phase-5-baseline`.

## Phase 6 - UX and Accessibility

- Scope: multi-route UI, loading/empty/error states, mobile, keyboard, labels, WCAG.
- Deliverables: learner/admin/reviewer flows with accessible UX.
- Entry: backend APIs stable.
- Exit: Playwright and accessibility checks pass.
- Effort: L.
- Branch: `feat/phase-6-ux-accessibility`.

## Phase 7 - Release Readiness

- Scope: production config, AWS plan, observability, backup, rollback, runbooks.
- Deliverables: deployment plan, IaC skeleton, operations docs.
- Entry: local MVP accepted.
- Exit: production readiness checklist approved.
- Effort: L.
- Branch: `ops/phase-7-release-readiness`.

## Phase 8 - Portfolio Completion

- Scope: README, architecture diagrams, ERD, API docs, ADRs, screenshots, demo material.
- Deliverables: portfolio-ready documentation and demo.
- Entry: release readiness complete.
- Exit: third party can understand and run demo.
- Effort: M.
- Branch: `docs/phase-8-portfolio`.

