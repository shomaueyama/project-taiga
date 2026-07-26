# Cloudflare + Render + Neon 本番構成

Status: 初回デプロイ済み。外部サービスは Cloudflare Pages、Render Free、Neon Free を利用する。

## 構成

```text
Cloudflare Pages
  React/Vite static assets
  HTTPS/CDN/custom domain
  SPA fallback: frontend/public/_redirects
  Pages Function: frontend/functions/api/[[path]].ts

Render Free Web Service
  FastAPI
  uvicorn taiga.main:app --host 0.0.0.0 --port $PORT
  Health check: /api/health
  DATABASE_URL で Neon に接続

Neon Free
  PostgreSQL
  Alembic migration 適用先

Cloudflare Access
  One-time PIN
  2 メールだけ許可
```

runner は無効のままにする。

```text
RUNNER_ENABLED=false
```

AWS Terraform under `infra/` は、将来の有料または enterprise 構成として残す。

## 重要な実装判断

本番フロントエンドの `VITE_API_BASE_URL` は `https://app.taiganova.app` にする。

理由:

- `app.taiganova.app` は Cloudflare Access で保護される。
- `app.taiganova.app/api/*` は Pages Function が Render raw URL に proxy する。
- Cloudflare Access JWT が Pages Function から Render に転送される。
- Render の `onrender.com` を Cloudflare proxied CNAME にすると Cloudflare 側で `DNS points to prohibited IP` になった。

`api.taiganova.app` は direct health 確認と Render custom domain 確認用として残す。

## 環境変数

Frontend:

- `VITE_API_BASE_URL=https://app.taiganova.app`

Backend:

- `APP_ENV=production`
- `LOCAL_AUTH_ENABLED=false`
- `DATABASE_URL`
- `MIGRATION_DATABASE_URL`
- `FRONTEND_ORIGINS=https://app.taiganova.app`
- `RUNNER_ENABLED=false`
- `EXAM_ENABLED=false`
- `RATE_LIMIT_ENABLED=true`
- `RATE_LIMIT_WINDOW_SECONDS`
- `RATE_LIMIT_MAX_REQUESTS`
- `WORKER_IDLE_POLL_SECONDS`
- `WORKER_ERROR_RETRY_SECONDS`
- `CLOUDFLARE_ACCESS_TEAM_DOMAIN=https://taiganova.cloudflareaccess.com`
- `CLOUDFLARE_ACCESS_AUD`
- `AUTHORIZED_USER_EMAILS=shomabirdie@icloud.com,taiga-albatross@softbank.ne.jp`

`CLOUDFLARE_ACCESS_AUD` は `taiga-nova-web` の audience を使う。

## Cloudflare Pages

- Project: `taiga-nova-web`
- Root directory: `frontend`
- Build command: `npm install && npm run build`
- Output directory: `dist`
- Custom domain: `app.taiganova.app`
- Production build variable: `VITE_API_BASE_URL=https://app.taiganova.app`

Direct deploy 例:

```bash
cd frontend
VITE_API_BASE_URL=https://app.taiganova.app npm run build
npx wrangler pages deploy dist --project-name=taiga-nova-web --branch=main --commit-dirty=true
```

## Pages Function proxy

`frontend/functions/api/[[path]].ts` が `/api/*` を Render raw URL に転送する。

```text
https://app.taiganova.app/api/health
  -> Pages Function
  -> https://taiga-nova-api.onrender.com/api/health
```

Access JWT を含む request header を Render に渡すため、バックエンドは Cloudflare Access JWT を検証できる。

## Render backend

- Service: `taiga-nova-api`
- Runtime: Python
- Root directory: `backend`
- Build command: `pip install -e ".[dev]"`
- Start command: `uvicorn taiga.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/api/health`
- Raw URL: `https://taiga-nova-api.onrender.com`
- Custom domain: `api.taiganova.app`

Render Free は idle 後の cold start がある。フロントエンドはタイムアウト時に日本語の再試行状態を表示する。

## Neon PostgreSQL

- Project: `taiga-nova-production`
- Database: `taiga`
- Migration revision: `0002_phase5_performance_indexes`

接続文字列は gitignored の operator env に保存する。

```bash
NEON_API_KEY="<redacted>" \
python3 scripts/neon_prepare.py \
  --project-name taiga-nova-production \
  --database-name taiga \
  --role-name taiga \
  --env-file .env.neon.local
```

Migration:

```bash
cd backend
set -a
source ../.env.neon.local
set +a
FRONTEND_ORIGINS=https://app.taiganova.app \
CLOUDFLARE_ACCESS_TEAM_DOMAIN=https://taiganova.cloudflareaccess.com \
CLOUDFLARE_ACCESS_AUD="<web-access-audience>" \
AUTHORIZED_USER_EMAILS=shomabirdie@icloud.com,taiga-albatross@softbank.ne.jp \
../.venv/bin/alembic upgrade head
```

## 認証

Cloudflare Access は `app.taiganova.app` と `api.taiganova.app` の両方に設定する。

Policy:

- Action: Allow
- Include:
  - `shomabirdie@icloud.com`
  - `taiga-albatross@softbank.ne.jp`

Login method:

- One-time PIN

バックエンドは `Cf-Access-Jwt-Assertion` を検証し、許可メールを DB の既存 active user に対応付ける。`Cf-Access-Authenticated-User-Email` だけは信用しない。

## Storage 制限

現在の upload completion は `LOCAL_STORAGE_ROOT/uploads` に manifest を書く。Render local disk は永続ストレージではない。

- 本番で upload-backed evidence を永続証跡として扱わない。
- durable object storage は R2 などを将来導入する。
- runner は無効のままにする。

## Upgrade 判断

最初の想定コストは 2 ユーザーでおおむね 0 JPY/月。ただし provider free tier は変わり得る。

有料化を検討する条件:

- Render cold start が運用上つらい。
- backend uptime が重要になる。
- Neon storage/compute 制限に近づく。
- 利用者が 2 人を超える。
- durable upload が必要になる。
- 自動 backup が必要になる。
- runner 実行を導入する。
