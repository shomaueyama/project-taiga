# Accessibility Visual Checks

Verified:

- axe violations: 0 on major pages in Chromium, Firefox, and WebKit.
- Skip link remains first keyboard target in Chromium and Firefox.
- WebKit skip link focus and activation remain verified with direct focus due local browser behavior.
- Route focus continues to move to `#main-content` after navigation.
- Mobile drawer returns focus to the trigger on Escape.
- Mobile drawer traps Tab focus while open.
- Closed mobile drawer is `aria-hidden` and `inert` on narrow viewports.
- Unknown Mission Progress state omits `aria-valuenow` and uses `aria-valuetext="進捗は未判定です"`.
- TAIGA status text is always visible and is not conveyed by color alone.
- Reduced motion disables transitions through the existing media query.

No accessibility blocker or major issue remains.
