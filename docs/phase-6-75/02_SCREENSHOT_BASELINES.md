# Screenshot Baselines

Baselines live in:

```text
frontend/e2e/visual-regression.spec.ts-snapshots/
```

Captured states:

- `dashboard-desktop.png`
- `dashboard-mobile.png`
- `mission-ahead.png`
- `mission-on-schedule.png`
- `mission-behind.png`
- `mission-unknown.png`
- `assignments-desktop-long-content.png`
- `assignments-mobile-long-content.png`
- `reviews-desktop.png`
- `runner-disabled.png`
- `exam-disabled.png`
- `admin-users.png`
- `mobile-drawer-open.png`
- `drawer-focus-return.png`
- `keyboard-focus-skip-link.png`
- `off-orbit-404.png`

Screenshot comparison is Chromium-only. The Playwright snapshot path is OS-independent so the same baseline files are used locally and in CI.

Firefox and WebKit run interaction, accessibility, request, and responsive overflow checks without screenshot baselines.
