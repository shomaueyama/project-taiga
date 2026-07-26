# Neon PostgreSQL デプロイ手順

Status: `taiga-nova-production` は作成済み。Alembic migration は head まで適用済み。

## 現在の設定

- Project: `taiga-nova-production`
- Database: `taiga`
- Role: `taiga`
- Migration head: `0002_phase5_performance_indexes`

接続文字列は secret なのでコミットしない。operator machine の gitignored env file にだけ保存する。

## API-assisted setup

Neon API key を使って、project の再利用または作成と `.env.neon.local` の生成を行う。

```bash
NEON_API_KEY="<redacted>" \
python3 scripts/neon_prepare.py \
  --project-name taiga-nova-production \
  --database-name taiga \
  --role-name taiga \
  --create \
  --env-file .env.neon.local \
  --migrate-command
```

Neon が organization ID を要求する場合は `--org-id` を付ける。

```bash
NEON_API_KEY="<redacted>" \
python3 scripts/neon_prepare.py \
  --org-id "<neon-org-id>" \
  --project-name taiga-nova-production \
  --database-name taiga \
  --role-name taiga \
  --create \
  --env-file .env.neon.local \
  --migrate-command
```

このスクリプトの挙動:

- 同名 project があれば再利用する。
- `--create` があり、同名 project がなければ作成する。
- `DATABASE_URL` と `MIGRATION_DATABASE_URL` を `.env.neon.local` に書く。
- URL に `&` が含まれても `source` できるよう shell-safe に quote する。
- 出力には redacted URI だけを表示する。

## Migration

本番 migration は direct Neon connection に対して実行する。

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

現在 revision の確認:

```bash
cd backend
set -a
source ../.env.neon.local
set +a
FRONTEND_ORIGINS=https://app.taiganova.app \
CLOUDFLARE_ACCESS_TEAM_DOMAIN=https://taiganova.cloudflareaccess.com \
CLOUDFLARE_ACCESS_AUD="<web-access-audience>" \
AUTHORIZED_USER_EMAILS=shomabirdie@icloud.com,taiga-albatross@softbank.ne.jp \
../.venv/bin/alembic current
```

## Production user bootstrap

初回ユーザーは `taiga.production_users` で idempotent に upsert する。

```bash
cd backend
set -a
source ../.env.neon.local
set +a
FRONTEND_ORIGINS=https://app.taiganova.app \
CLOUDFLARE_ACCESS_TEAM_DOMAIN=https://taiganova.cloudflareaccess.com \
CLOUDFLARE_ACCESS_AUD="<web-access-audience>" \
AUTHORIZED_USER_EMAILS=shomabirdie@icloud.com,taiga-albatross@softbank.ne.jp \
../.venv/bin/python -m taiga.production_users \
  --file ../.env.production-users.json \
  --apply
```

`production-users` JSON は operator machine の未コミットファイルとして扱う。

## Free tier 注意

Neon Free は storage、compute、scale-to-zero、backup/restore に制限がある。運用前後で dashboard の plan/limit を確認する。

公式参照:

- https://neon.com/docs/introduction/plans
- https://neon.com/docs/introduction/usage-calculations
- https://neon.com/docs/guides/scale-to-zero-guide
- https://neon.com/docs/guides/backup-restore
