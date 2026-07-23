# Accessibility Audit

## Implemented

- One clear `h1` per active page via `PageHeader`.
- Semantic `header`, `aside`, `nav`, and `main` landmarks.
- Skip link targets `#main-content`.
- Route changes focus the main content container.
- Navigation exposes `aria-current="page"`.
- Action controls are buttons; route changes are links.
- Mutation feedback uses `aria-live="polite"`.
- Loading states use `role="status"`.
- Status is conveyed with text labels, not color alone.
- Focus outlines are visible and high contrast.
- Touch targets are at least 44px for buttons, links, and select controls.
- Reduced motion media query disables smooth scrolling.
- Automated axe checks pass for dashboard, assignments, reviews, and admin pages.

## Manual Checks

- Keyboard-only skip link and navigation activation passed in Playwright.
- Required responsive widths were checked for overflow by Playwright.
- Screen-reader-oriented structure was reviewed through headings, landmarks, labels, and live
  regions.

## Limitations

- There are no modal dialogs in the current Local MVP UI.
- Full screen-reader session testing with VoiceOver remains deferred.
- Complex form validation is limited because current active forms are mostly button/select driven.
