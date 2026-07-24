# Production Smoke Test

Status: not executed. Requires Gate D approval and deployed services.

Run without exposing tokens or connection strings.

## Public Health

```bash
curl -i https://api.taiganova.app/api/health
```

Expected: `200` and `{"status":"ok"}`.

Legacy health routes should not expose detail in production:

```bash
curl -i https://api.taiganova.app/health
curl -i https://api.taiganova.app/ready
```

Expected: `404`.

## Access Boundary

Unauthenticated application API call:

```bash
curl -i https://api.taiganova.app/api/v1/me
```

Expected: `401`.

Browser test:

1. Open `https://app.taiganova.app`.
2. Complete Cloudflare Access login with an approved email.
3. Verify dashboard loads.
4. Verify assignments/progress load.
5. Verify runner controls remain disabled.

Denied user test:

1. Attempt Access login with a non-allowlisted email.
2. Confirm Cloudflare denies access or the backend returns a Japanese unauthorized state.
