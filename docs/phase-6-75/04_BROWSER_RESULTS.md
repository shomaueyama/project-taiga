# Browser Results

Playwright projects:

- Chromium
- Firefox
- WebKit

Results from the final local run:

```text
25 passed
26 skipped
0 failed
```

Skipped tests are intentional:

- Stateful Local MVP mutation flows run in Chromium only to avoid rate-limit and shared-database interference across parallel browser projects.
- Screenshot regression baselines run in Chromium only.

Cross-browser coverage retained:

- axe accessibility checks
- responsive overflow checks from 320 to 1440 px
- keyboard skip-link and route focus
- duplicate initial API request regression

WebKit note:

- WebKit on macOS does not reliably move focus to links through the first Tab press in the same way as Chromium and Firefox. The test focuses the skip link directly for WebKit and still verifies focus visibility and activation behavior.
