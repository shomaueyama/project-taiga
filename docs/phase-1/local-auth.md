# LocalAuth Verification

LocalAuth is permitted only when `APP_ENV=local` and `LOCAL_AUTH_ENABLED=true`.

## Known Users

| Email | Role | Display name |
|---|---|---|
| `taiga@example.local` | learner | 上山 虎雅 |
| `reviewer@example.local` | reviewer | Local Reviewer |
| `admin@example.local` | admin | 上山 捷馬 |

## Required Behavior

- Unknown local email: `401`.
- Missing local header/token: `401`.
- Suspended user: `403`.
- LocalAuth outside local: fail fast during settings validation.
