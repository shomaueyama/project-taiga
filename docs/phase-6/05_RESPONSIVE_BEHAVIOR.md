# Responsive Behavior

## Width Results

| Width | Result | Notes |
|---|---|---|
| 320px | Passed | Sidebar stacks above content; rows and actions wrap |
| 375px | Passed | Buttons remain reachable; no horizontal overflow |
| 390px | Passed | Japanese copy wraps without clipping |
| 768px | Passed | Two-column layout collapses intentionally |
| 1024px | Passed | Sidebar and main content fit with stable spacing |
| 1440px | Passed | Content remains constrained to 1180px |

## Screen Strategy

- Dashboard metrics use responsive cards.
- Assignment and review lists use stacked row cards instead of mobile tables.
- Admin metrics and flags wrap within the main content column.
- Navigation remains visible and keyboard reachable on all tested widths.
- Long identifiers are shortened in action labels through `shortId`.

## Deferred

- Screenshot-based visual regression is deferred to Phase 6.75.
