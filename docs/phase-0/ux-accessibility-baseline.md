# UX and Accessibility Baseline

## Current UI

The frontend is a single Local MVP workspace with panels for login, dashboard, assignments, review, runner, exam, and admin.

Evidence: `frontend/src/routes/App.tsx`, `frontend/src/styles.css`.

## Baseline Findings

| Area | Finding | Target phase |
|---|---|---|
| Navigation | No multi-route navigation; all content on one page | Phase 6 |
| Login | Local user select exists; no password flow | Phase 1/6 |
| Loading | Mostly fallback counts/text; no consistent loading component | Phase 6 |
| Empty state | Basic fallback text exists | Phase 6 |
| Error state | Minimal, not per-panel | Phase 6 |
| Success feedback | Submission/review actions use aria-live text | Phase 6 |
| Disabled state | Runner and exam disabled buttons visible | Phase 6 |
| Mobile | CSS has one breakpoint; not deeply audited | Phase 6 |
| Keyboard | Native controls likely keyboard accessible; no formal test | Phase 6 |
| Labels | Local user select and feature flags have labels | Phase 6 |
| Focus | No explicit focus management | Phase 6 |
| Contrast | Not measured | Phase 6 |
| Screen reader | No axe or manual screen reader audit | Phase 6 |

## Screens Not Implemented

- Dedicated curriculum page.
- Dedicated assignment detail page.
- Dedicated submission history page.
- Dedicated review queue page.
- Dedicated admin user/curriculum/task management.
- Dedicated exam runtime.
- Dedicated runner result page.
- Error page / 404 page.

