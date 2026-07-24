# Private Repository Setup

Status: manual owner checklist only. No repository visibility or integration permission was changed.

The GitHub repository `shomaueyama/project-taiga` is private. Cloudflare cannot read it through a
GitHub integration unless the owner explicitly grants access to that repository or to a selected
set of repositories containing it.

## Owner Checklist

1. Confirm the repository remains private.
2. Connect Cloudflare to GitHub from the Cloudflare dashboard or approved Wrangler workflow.
3. Select `shomaueyama/project-taiga` explicitly, or grant access only to required repositories.
4. Verify the intended production branch after the PR stack is settled.
5. Verify build command and output directory.
6. Configure environment-variable names only; do not paste values into documentation.
7. Verify preview deployment behavior.
8. Confirm pull-request previews do not receive production secrets.
9. Confirm deployment permissions follow least privilege.
10. Document how to revoke Cloudflare GitHub App access.
11. Document how to rotate the Cloudflare API token.
12. Document fallback Wrangler CLI deployment.

## Placeholder Secret Names

- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_D1_DATABASE_ID`
- `CLOUDFLARE_R2_BUCKET_NAME`

Do not commit secret values.

## Fallback Wrangler Flow

Use only after owner approval:

```bash
npm install
npx wrangler whoami
npx wrangler deploy
```

Do not run `wrangler login`, create D1/R2/Queue resources, or deploy from this assessment branch.

