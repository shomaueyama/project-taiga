# 本番公開メモ

Status: `taiganova.app` の初回本番デプロイは完了済み。

## 現在の構成

```text
Cloudflare Access
  app.taiganova.app
    -> Cloudflare Pages taiga-nova-web
    -> React/Vite static assets
    -> /api/* は Pages Function で Render raw URL へ proxy

Render Free
  taiga-nova-api
  https://taiga-nova-api.onrender.com
  FastAPI / uvicorn

Neon Free
  taiga-nova-production
  PostgreSQL

api.taiganova.app
  -> Render custom domain
  -> health/direct 確認用
```

本番アプリ内の API base URL は `https://app.taiganova.app` です。`/api/*` を Pages Function が Render に転送します。これは、Render の `onrender.com` を Cloudflare proxied CNAME にすると Cloudflare 側で `DNS points to prohibited IP` になったためです。

## 本番 URL

- アプリ: https://app.taiganova.app
- API health: https://api.taiganova.app/api/health
- Pages preview: `taiga-nova-web.pages.dev`
- Render raw API: `https://taiga-nova-api.onrender.com`

## 認証

Cloudflare Access を有効化済みです。

- Team domain: `taiganova.cloudflareaccess.com`
- Login method: One-time PIN
- Access app: `taiga-nova-web` for `app.taiganova.app`
- Access app: `taiga-nova-api` for `api.taiganova.app`

許可 policy は次の 2 メールだけを Allow します。

- `shomabirdie@icloud.com`
- `taiga-albatross@softbank.ne.jp`

Everyone、domain-wide、all valid emails、broad Bypass は使いません。

## Render 設定

- Service: `taiga-nova-api`
- Runtime: Python
- Root directory: `backend`
- Build command: `pip install -e ".[dev]"`
- Start command: `uvicorn taiga.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/api/health`

重要な環境変数:

```text
APP_ENV=production
LOCAL_AUTH_ENABLED=false
RUNNER_ENABLED=false
EXAM_ENABLED=false
RATE_LIMIT_ENABLED=true
FRONTEND_ORIGINS=https://app.taiganova.app
CLOUDFLARE_ACCESS_TEAM_DOMAIN=https://taiganova.cloudflareaccess.com
AUTHORIZED_USER_EMAILS=shomabirdie@icloud.com,taiga-albatross@softbank.ne.jp
```

`CLOUDFLARE_ACCESS_AUD` は `taiga-nova-web` の Access audience を使います。アプリ内 API は `app.taiganova.app/api/*` 経由で呼ばれ、Cloudflare Access の JWT audience も web app のものになるためです。

## Neon 設定

- Project: `taiga-nova-production`
- Database: `taiga`
- Migration: Alembic `head` 適用済み
- 現在 revision: `0002_phase5_performance_indexes`

接続文字列は `.env.neon.local` などの gitignored ファイルだけに保存します。コミットしません。

## 初期ユーザー

本番 DB に bootstrap 済みです。

| メール | 表示名 | ロール | タイムゾーン |
|---|---|---|---|
| `shomabirdie@icloud.com` | Shoma | admin | Asia/Tokyo |
| `taiga-albatross@softbank.ne.jp` | Taiga | learner | Asia/Tokyo |

## Smoke 結果

確認済み:

- `https://app.taiganova.app` は未認証で Cloudflare Access login に redirect
- `https://app.taiganova.app/api/health` は未認証で Cloudflare Access login に redirect
- `https://api.taiganova.app/api/health` は 200
- `https://api.taiganova.app/api/v1/me` は Access JWT なしで 401
- `Origin: https://app.taiganova.app` の CORS は許可
- Render deploy は `live`

ブラウザで確認済み:

- Cloudflare Access の One-time PIN ログイン画面が表示される
- 許可済みメールでログインできる

## 本番制限

- Render Free の cold start は許容する。
- Render の local filesystem upload は永続ストレージではない。
- `RUNNER_ENABLED=false` のままにする。
- `EXAM_ENABLED=false` のままにする。
- runner 実行、durable upload、backup 自動化は将来対応。

## Rollback

短期 rollback:

1. Cloudflare Pages の直前 deployment に戻す。
2. Render の直前 deployment に戻す。
3. 必要なら Cloudflare Access app/policy を無効化せず、許可メールだけ確認する。

DB migration rollback は現在想定しません。Neon Free の backup/restore 制限があるため、production data rollback は事前の手動 export または Neon 側の復元機能確認が必要です。
