# Project Taiga

Project Taiga は、TAIGA NOVA の学習プラットフォーム MVP です。

このリポジトリは、次の設計パックを読み取り専用の正本として実装しています。

```text
../design/taiga-42-v4.0-implementation-pack
```

設計パックは変更しません。アプリケーションコード、テスト、migration、ローカル用ドキュメントはこのリポジトリに置きます。

## 本番環境

- アプリ: https://app.taiganova.app
- API health: https://api.taiganova.app/api/health
- フロントエンド: Cloudflare Pages
- API: Render Free Web Service
- DB: Neon Free PostgreSQL
- 認証: Cloudflare Access + One-time PIN
- 許可ユーザー:
  - `shomabirdie@icloud.com` / admin
  - `taiga-albatross@softbank.ne.jp` / learner

本番のアプリ内 API 通信は `https://app.taiganova.app/api/*` から Cloudflare Pages Function 経由で Render に転送します。`api.taiganova.app` は health/direct 確認用のカスタムドメインです。

## ローカル URL

- フロントエンド: http://localhost:5173
- API: http://localhost:8000
- API docs: http://localhost:8000/docs

## ローカル画面

- `/dashboard`
- `/assignments`
- `/assignments/:assignmentId`
- `/reviews`
- `/runner`
- `/exams`
- `/admin`

## 前提ツール

- Docker / Docker Compose
- Node.js / npm
- Python 仮想環境 `.venv`
- 読み取り専用の設計パック `../design/taiga-42-v4.0-implementation-pack`

## よく使うコマンド

```bash
make setup
docker compose up -d --build
make migrate
make seed
make lint
make typecheck
make test
make test-coverage
make test-e2e
make validate
python3 scripts/perf_load.py --scenario baseline
make down
```

## クリーンなローカル起動

```bash
make setup
docker compose down -v
docker compose build --no-cache
docker compose up -d
make migrate
make seed
make seed
docker compose ps
```

2 回目の `make seed` は seed の冪等性確認です。backend と worker は同じ backend Dockerfile を使います。正本 curriculum は設計パックから読み取り専用でマウントします。

## ローカルデータ

PostgreSQL 起動後に migration と seed を実行します。

```bash
docker compose up -d --build
make migrate
make seed
make seed
```

seed は local 専用で、設計パックの canonical curriculum を取り込みます。あわせて、Local MVP 用の現実的な fixture を追加します。

- 管理者: `admin@example.local` / 上山 捷馬
- 学習者: `taiga@example.local` / 上山 虎雅
- レビュー互換ユーザー: `reviewer@example.local`
- 課題状態、immutable submission、review comment、runner job 状態、exam attempt 状態、rank、capability progress

ローカルデータを消す場合:

```bash
make reset
docker compose up -d
make migrate
make seed
```

## テスト

```bash
make lint
make typecheck
make test
make test-coverage
cd frontend && npx playwright install
make test-e2e
cd frontend && npx playwright test --repeat-each=3
cd frontend && npx playwright test --retries=2
```

現在の Local MVP テスト範囲は `docs/local-mvp-test-matrix.md` に記録しています。Playwright は `pageerror`、`console.error`、失敗 request、想定外の HTTP 5xx を監視します。

## 本番デプロイ

本番は Cloudflare Pages、Render Free、Neon Free、Cloudflare Access の 2 ユーザー構成です。

- Cloudflare Pages project: `taiga-nova-web`
- Render service: `taiga-nova-api`
- Neon project: `taiga-nova-production`
- Cloudflare Access team domain: `taiganova.cloudflareaccess.com`
- Login method: One-time PIN

Render の重要な安全設定:

```text
APP_ENV=production
LOCAL_AUTH_ENABLED=false
RUNNER_ENABLED=false
EXAM_ENABLED=false
RATE_LIMIT_ENABLED=true
FRONTEND_ORIGINS=https://app.taiganova.app
```

本番 DB migration は Neon の direct connection に対して Alembic を実行します。接続文字列は `.env.neon.local` などの gitignored ファイルにだけ保存し、コミットしません。

## 機能フラグ

ローカルと本番の安全デフォルト:

```text
RUNNER_ENABLED=false
EXAM_ENABLED=false
RATE_LIMIT_ENABLED=true
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_MAX_REQUESTS=120
WORKER_IDLE_POLL_SECONDS=5
WORKER_ERROR_RETRY_SECONDS=30
```

`RUNNER_ENABLED=false` の間、runner queue request は安全に拒否され、学習者コードは実行されません。`EXAM_ENABLED=false` の間、exam mutation request は拒否され、フロントエンドも exam flow を開始しません。

## ローカル安全設定

- `APP_ENV=local`
- `LOCAL_AUTH_ENABLED=true`
- `RUNNER_ENABLED=false`
- `EXAM_ENABLED=false`
- `RATE_LIMIT_ENABLED=true`

LocalAuth は `APP_ENV=local` かつ `LOCAL_AUTH_ENABLED=true` のときだけ有効です。本番では必ず無効にします。

## ドキュメント

- Phase 0: `docs/phase-0/`
- Phase 1: `docs/phase-1/`
- Phase 2: `docs/phase-2/`
- Phase 3: `docs/phase-3/`
- Phase 4: `docs/phase-4/`
- Phase 5: `docs/phase-5/`
- Phase 6: `docs/phase-6/`
- Phase 6.5: `docs/phase-6-5/`
- Phase 6.75: `docs/phase-6-75/`
- Phase 7 AWS 将来構成: `docs/phase-7/` と `infra/`
- Cloudflare/Render/Neon 本番構成: `docs/deployment/`

## ログとトラブル対応

```bash
docker compose ps
docker compose logs --tail=200
docker compose restart
docker compose down
docker compose up -d
```

migration や seed が失敗する場合は、PostgreSQL が healthy か、設計パックのパスが存在するか確認してください。LocalAuth が失敗する場合は、`.env` の `APP_ENV=local` と `LOCAL_AUTH_ENABLED=true` を確認してください。
