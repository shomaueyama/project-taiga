# Cloudflare Access Security

Status: repository enforcement implemented; external Cloudflare Access applications are not created.

## Backend Enforcement

Production API requests authenticate through the Cloudflare Access JWT header:

```http
Cf-Access-Jwt-Assertion: <redacted>
```

The backend verifies:

- JWT signature using Cloudflare Access signing keys.
- Algorithm allowlist: `RS256`.
- Expiration.
- Issuer equal to `CLOUDFLARE_ACCESS_TEAM_DOMAIN`.
- Audience equal to `CLOUDFLARE_ACCESS_AUD`.
- Email claim is present and belongs to `AUTHORIZED_USER_EMAILS`.

The backend does not trust `Cf-Access-Authenticated-User-Email` by itself. Missing, malformed,
expired, incorrectly signed, wrong-issuer, wrong-audience, unknown-key, and unapproved-email tokens
fail closed with `401`.

Signing keys are fetched from:

```text
<CLOUDFLARE_ACCESS_TEAM_DOMAIN>/cdn-cgi/access/certs
```

Keys are cached for a bounded period and refreshed once on unknown `kid`. Raw JWTs, secrets, and
connection strings must not be logged.

## Cloudflare Configuration

Create two Access applications after Gate B approval:

- `app.<domain>` for Cloudflare Pages.
- `api.<domain>` for the Cloudflare-proxied Render custom hostname.

Policy shape:

- Action: Allow.
- Include: exactly the two owner-approved email addresses.
- Avoid: Everyone, all valid emails, broad email domains, and broad Bypass policies.

Cloudflare's documentation states that Access sends the JWT in `Cf-Access-Jwt-Assertion`, publishes
public keys under the team domain, and requires validating issuer and audience.

Official references:

- https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/
- https://developers.cloudflare.com/cloudflare-one/access-controls/policies/
- https://developers.cloudflare.com/cloudflare-one/tutorials/fastapi/

## Health Boundary

Production public unauthenticated surface:

```http
GET /api/health
```

Response:

```json
{"status":"ok"}
```

Legacy health/readiness routes are hidden in production. Application endpoints still require a valid
Cloudflare Access JWT and an existing active application user mapped by email.
