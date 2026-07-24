# Known Limitations

## Minor: source image fidelity

- Severity: minor
- Route: `/dashboard`
- Viewport: all
- Reproduction: inspect Mission Progress status images at 2x.
- Impact: edges and lower-body details are limited by the supplied bitmap crops.
- Proposed phase: Phase 6.9 owner review can decide whether to commission final production-grade art.

## Preference: schedule authority

- Severity: preference
- Route: `/dashboard`
- Viewport: all
- Reproduction: Mission schedule status is derived client-side from completed week count.
- Impact: not a visual blocker; it remains a product/data-contract decision.
- Proposed phase: backend schedule semantics after owner testing.

No blocker or major issue remains.
