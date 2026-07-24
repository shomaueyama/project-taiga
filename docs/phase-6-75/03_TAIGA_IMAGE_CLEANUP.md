# TAIGA Image Cleanup

Output assets:

| Asset | Dimensions | Size | Notes |
|---|---:|---:|---|
| `taiga-status-ahead.webp` | 360 x 360 | 6.69 KB | Neutral canvas, adjacent source fragments removed |
| `taiga-status-on-schedule.webp` | 360 x 360 | 5.91 KB | Neutral canvas, white sportswear preserved |
| `taiga-status-behind.webp` | 360 x 360 | 7.03 KB | Neutral canvas, single crying figure retained |

Before cleanup, the three PNG assets totaled approximately 279.94 KB in the production build. After cleanup, the three WebP assets total approximately 19.63 KB.

The cleanup uses a deliberately neutral background instead of transparency. This avoids visible checkerboard artifacts while keeping white clothing readable on the TAIGA NOVA card background.

Known minor visual debt:

- The source images are AI-generated bitmap crops, so fine hair and clothing edges are not studio-quality cutouts.
- The `ahead` source has limited lower-body detail due to the original crop.

These are non-blocking for Phase 6.9 owner testing.
