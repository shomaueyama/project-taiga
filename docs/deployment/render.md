# Render Backend デプロイ

Status: Render service `taiga-nova-api` は作成済み。現在 deploy は `live`。

## Service

- Service type: Web Service
- Runtime: Python
- Root directory: `backend`
- Build command: `pip install -e ".[dev]"`
- Start command: `uvicorn taiga.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/api/health`
- Raw URL: `https://taiga-nova-api.onrender.com`
- Custom domain: `api.taiganova.app`

## 必須環境変数

```text
APP_ENV=production
LOCAL_AUTH_ENABLED=false
RUNNER_ENABLED=false
EXAM_ENABLED=false
RATE_LIMIT_ENABLED=true
DATABASE_URL=<Neon runtime URL>
MIGRATION_DATABASE_URL=<Neon migration URL>
FRONTEND_ORIGINS=https://app.taiganova.app
CLOUDFLARE_ACCESS_TEAM_DOMAIN=https://taiganova.cloudflareaccess.com
CLOUDFLARE_ACCESS_AUD=<taiga-nova-web の Access audience>
AUTHORIZED_USER_EMAILS=shomabirdie@icloud.com,taiga-albatross@softbank.ne.jp
```

`CLOUDFLARE_ACCESS_AUD` は `taiga-nova-api` ではなく `taiga-nova-web` の audience を使う。アプリ内 API 通信は `app.taiganova.app/api/*` の Pages Function proxy 経由で Render に届くため。

## Custom domain

`api.taiganova.app` は Render custom domain として設定済み。Cloudflare DNS は DNS-only CNAME にする。

```text
api.taiganova.app CNAME taiga-nova-api.onrender.com DNS-only
```

Cloudflare proxied CNAME にすると `DNS points to prohibited IP` になるため、アプリ内通信には使わない。アプリ内通信は `app.taiganova.app/api/*` を使う。

## Cold start

Render Free は idle 後に cold start する。フロントエンドは API timeout 時に日本語の再試行表示を出す。

## Smoke

```bash
curl -i https://api.taiganova.app/api/health
curl -i https://api.taiganova.app/api/v1/me
```

期待:

- `/api/health` は 200
- `/api/v1/me` は Access JWT なしで 401

公式参照:

- https://render.com/docs/deploy-fastapi
- https://render.com/docs/health-checks
- https://render.com/docs/web-services
- https://render.com/docs/rollbacks
