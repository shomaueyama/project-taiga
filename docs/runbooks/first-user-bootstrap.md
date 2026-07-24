# First User Bootstrap Runbook

Status: command available; do not run against production before Gate 7 approval.

## Owner-Approved Records

| Email | Display name | Role | Timezone |
|---|---|---|---|
| `shomabirdie@icloud.com` | Shoma | admin | Asia/Tokyo |
| `taiga-albatross@softbank.ne.jp` | Taiga | learner | Asia/Tokyo |

## JSON Input

Create an uncommitted JSON file on the operator machine:

```json
[
  {
    "email": "shomabirdie@icloud.com",
    "displayName": "Shoma",
    "role": "admin",
    "timezone": "Asia/Tokyo"
  },
  {
    "email": "taiga-albatross@softbank.ne.jp",
    "displayName": "Taiga",
    "role": "learner",
    "timezone": "Asia/Tokyo"
  }
]
```

## Dry Run

```bash
cd backend
APP_ENV=production \
LOCAL_AUTH_ENABLED=false \
RUNNER_ENABLED=false \
DATABASE_URL="<redacted-direct-neon-url>" \
FRONTEND_ORIGINS="<approved-frontend-origin>" \
CLOUDFLARE_ACCESS_TEAM_DOMAIN="<redacted-team-domain>" \
CLOUDFLARE_ACCESS_AUD="<redacted-audience>" \
AUTHORIZED_USER_EMAILS="<two-approved-emails-comma-separated>" \
../.venv/bin/python -m taiga.production_users --file /path/to/production-users.json
```

## Apply

Run only after Gate 7 owner approval:

```bash
cd backend
APP_ENV=production \
LOCAL_AUTH_ENABLED=false \
RUNNER_ENABLED=false \
DATABASE_URL="<redacted-direct-neon-url>" \
FRONTEND_ORIGINS="<approved-frontend-origin>" \
CLOUDFLARE_ACCESS_TEAM_DOMAIN="<redacted-team-domain>" \
CLOUDFLARE_ACCESS_AUD="<redacted-audience>" \
AUTHORIZED_USER_EMAILS="<two-approved-emails-comma-separated>" \
../.venv/bin/python -m taiga.production_users --file /path/to/production-users.json --apply
```

The command is idempotent. It validates exactly two users and requires the JSON email set to match
`AUTHORIZED_USER_EMAILS` exactly. It upserts active application users and does not create passwords.
