# Access Login Runbook

Status: production procedure. Requires Cloudflare Access applications to exist.

## Approved Users

| User | Email | Expected role |
|---|---|---|
| Shoma | `shomabirdie@icloud.com` | admin |
| Taiga | `taiga-albatross@softbank.ne.jp` | learner |

## Login Verification

1. Open a private browser window.
2. Visit `https://app.taiganova.app`.
3. Confirm Cloudflare Access appears before TAIGA NOVA application content.
4. Authenticate with one approved email.
5. Confirm the dashboard loads.
6. Confirm `/api/v1/me` maps the email to the expected application role.

For Taiga's carrier email, confirm the authentication message is received. If delivery fails, stop
and report; do not silently substitute another email.

## Denied Access Check

Inspect Cloudflare Access policy configuration and confirm no third email, domain-wide selector,
Everyone rule, all-valid-emails rule, or broad Bypass rule is present. Do not create a third test
account unless the owner supplies one.
