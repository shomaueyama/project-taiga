# Cloudflare Pages デプロイ

Status: Pages project `taiga-nova-web` は作成済み。`app.taiganova.app` は active。

## Build 設定

- Root directory: `frontend`
- Build command: `npm install && npm run build`
- Output directory: `dist`
- Production environment variable: `VITE_API_BASE_URL=https://app.taiganova.app`

Vite production build は `VITE_API_BASE_URL` が未設定、または HTTPS でない場合に失敗する。

## Routing

`frontend/public/_redirects` が SPA fallback を提供する。直接 `/dashboard` などにアクセスしても React app に戻る。

## Pages Function proxy

`frontend/functions/api/[[path]].ts` が `/api/*` を Render raw URL に proxy する。

```text
https://app.taiganova.app/api/* -> https://taiga-nova-api.onrender.com/api/*
```

この proxy が Cloudflare Access JWT header を Render に転送するため、本番アプリ内 API 通信は `app.taiganova.app` の same-origin で行う。

## Deploy

```bash
cd frontend
VITE_API_BASE_URL=https://app.taiganova.app npm run build
npx wrangler pages deploy dist --project-name=taiga-nova-web --branch=main --commit-dirty=true
```

## Custom domain

- `app.taiganova.app`
- DNS: `app.taiganova.app CNAME taiga-nova-web.pages.dev` proxied
- Cloudflare Access app: `taiga-nova-web`
- Login method: One-time PIN

## Access policy

許可するメール:

- `shomabirdie@icloud.com`
- `taiga-albatross@softbank.ne.jp`

Everyone、domain-wide、all valid emails、broad Bypass は使わない。

## Smoke

未認証で以下を確認する。

```bash
curl -i https://app.taiganova.app
curl -i https://app.taiganova.app/api/health
```

期待:

- Cloudflare Access login に redirect される。
- Login method に One-time PIN が表示される。

公式参照:

- https://developers.cloudflare.com/pages/
- https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/one-time-pin/
