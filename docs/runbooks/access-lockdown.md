# Access Lockdown Runbook

Use this when a production access mistake is suspected.

## Immediate Actions

1. Disable or tighten Cloudflare Access policies for `app.<domain>` and `api.<domain>`.
2. Confirm no policy uses Everyone, all valid emails, or a broad email domain.
3. Verify `AUTHORIZED_USER_EMAILS` in Render contains exactly the two approved emails.
4. Restart the Render service after env var correction.
5. Check that `https://api.<domain>/api/v1/me` returns `401` without Access.

## Backend Verification

The backend must fail closed when any of these are missing or wrong:

- `CLOUDFLARE_ACCESS_TEAM_DOMAIN`
- `CLOUDFLARE_ACCESS_AUD`
- `AUTHORIZED_USER_EMAILS`
- `Cf-Access-Jwt-Assertion`

Do not switch production to `APP_ENV=local`.
