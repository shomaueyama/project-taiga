# Asset Inventory

| Asset | Purpose | Size |
|---|---|---:|
| `frontend/src/assets/brand/nova-mark.svg` | Logo mark | < 1 KB |
| `frontend/src/assets/brand/favicon.svg` | Favicon | < 1 KB |
| `frontend/src/assets/illustrations/nova-orbit.svg` | Decorative orbit / unknown fallback | < 1 KB |
| `frontend/src/assets/taiga-status/taiga-status-ahead.png` | Ahead status image | 87 KB |
| `frontend/src/assets/taiga-status/taiga-status-on-schedule.png` | On-schedule status image | 78 KB |
| `frontend/src/assets/taiga-status/taiga-status-behind.png` | Behind status image | 109 KB |

## Budget

- Each raster status image is under 150 KB.
- Total TAIGA status raster assets are approximately 274 KB.
- The main JS bundle gzip remains below the 150 KB Phase 5/6 budget.

## Deferred

- Convert TAIGA status images to clean transparent WebP or optimized PNG after source cutouts are
  available.
- Add responsive image sources if the status-image system expands beyond the dashboard.
