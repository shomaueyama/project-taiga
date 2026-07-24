# Cloudflare Pages Deployment

Status: plan only. No Cloudflare Pages project, custom domain, or Access policy was created.

## Build Settings

- Root directory: `frontend`
- Build command: `npm install && npm run build`
- Output directory: `dist`
- Production environment variable: `VITE_API_BASE_URL=https://api.<domain>`

The Vite production build fails if `VITE_API_BASE_URL` is missing or not HTTPS.

## Routing

`frontend/public/_redirects` provides the SPA fallback for direct route loads.

## Access Requirement

Before first production deployment, protect `app.<domain>` with Cloudflare Access:

- Include only the two owner-approved email addresses.
- Do not use broad domain-based or Everyone rules.
- Keep the repository private and avoid exposing frontend config beyond the API origin.

Official reference:

- https://developers.cloudflare.com/pages/
