# HTTP and Browser Security

## Changes

All backend responses now receive:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; base-uri 'self'`
- `Cache-Control: no-store`

CORS is restricted to the local frontend origin, explicit HTTP methods, and explicit request headers.

## Notes

- The backend does not use cookies in the Local MVP.
- CSP is intentionally conservative for API responses. The Vite frontend is served separately in local development.
- Rate limiting uses the actual client socket host and does not trust forwarded headers.

## Tests

Phase 4 verifies security headers on health responses and rejects an untrusted CORS preflight origin.
