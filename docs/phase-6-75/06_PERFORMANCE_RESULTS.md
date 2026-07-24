# Performance Results

Production build:

```text
JS: 406.42 KB, gzip 123.27 KB
CSS: 12.93 KB, gzip 3.46 KB
```

Comparison:

| Metric | Phase 6.5 | Phase 6.75 | Delta |
|---|---:|---:|---:|
| JS gzip | 122.92 KB | 123.27 KB | +0.35 KB |
| TAIGA status assets | 279.94 KB | 19.63 KB | -260.31 KB |

The gzip increase is under the 5 KB Phase 6.75 explanation threshold.

Image-related layout stability:

- Status images declare 360 x 360 intrinsic dimensions.
- CSS constrains rendered image size with stable max dimensions.
- Mission content uses bounded text width and progress-track width to avoid overlap with the image column.
