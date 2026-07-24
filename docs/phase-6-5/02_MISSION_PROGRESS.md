# Mission Progress and TAIGA Status Images

## Data Source

Mission Progress uses existing authoritative `/api/v1/progress` data:

- `completedWeeks`
- total weeks fixed to the canonical 28-week curriculum

The frontend does not invent completed counts. If progress data is missing, the component renders an
unknown state instead of fabricating 0%.

## Temporary Schedule Calculation

The current client-side schedule status is intentionally simple until backend schedule policy exists:

- `completedWeeks >= 20`: `ahead`
- `completedWeeks >= 1`: `on_schedule`
- otherwise: `behind`
- missing progress data: `unknown`

This is documented as a presentation rule, not a domain policy. Backend authority should replace it
when schedule rules become business-sensitive.

## Status Mapping

| Status | Label | Message | Asset |
|---|---|---|---|
| `ahead` | 予定より先行 | 予定より先行しています | `taiga-status-ahead.png` |
| `on_schedule` | 予定どおり | 予定どおり進んでいます | `taiga-status-on-schedule.png` |
| `behind` | 予定より遅れ | 予定より遅れています | `taiga-status-behind.png` |
| `unknown` | 判定不可 | 進捗状況を判定できません | `nova-orbit.svg` |

## Accessibility

- The progress bar exposes `role="progressbar"`, Japanese label, `aria-valuemin`,
  `aria-valuemax`, and `aria-valuenow`.
- Status meaning is text-based and does not depend on the image.
- Status images include concise Japanese alt text.

## Asset Notes

Provided source PNGs contain checkerboard backgrounds in the pixels. Phase 6.5 standardizes crop and
size, but clean alpha cutouts are deferred to Phase 6.75 visual QA.
