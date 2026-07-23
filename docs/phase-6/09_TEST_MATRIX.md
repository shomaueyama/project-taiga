# Test Matrix

| Area | Tool | Scope | Result |
|---|---|---|---|
| Japanese labels | Vitest | role/status/date/id formatting | Passed |
| App states | Vitest + Testing Library | learner, runner, reviewer, admin, exam states | Passed |
| Existing E2E | Playwright | six Local MVP flows | Passed |
| Accessibility | `@axe-core/playwright` | dashboard, assignments, reviews, admin | Passed |
| Responsive | Playwright | 320, 375, 390, 768, 1024, 1440 widths | Passed |
| Keyboard | Playwright | skip link and nav activation | Passed |
| Performance guardrail | Playwright | duplicate initial dashboard API requests | Passed |

## Limitations

- Automated axe checks do not replace full assistive technology testing.
- Visual regression screenshots are not baselined in Phase 6.
- Enabled exam browser E2E remains limited by default `EXAM_ENABLED=false`.
