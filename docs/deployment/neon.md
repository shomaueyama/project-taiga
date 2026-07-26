# Neon PostgreSQL デプロイ手順

Status: `taiga-nova-production` は作成済み。Alembic migration は head まで適用済み。

## 現在の設定

- Project: `taiga-nova-production`
- Database: `taiga`
- Role: `taiga`
- Migration head: `0003_schedule_calendar`

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

## Production curriculum seed

本番の課題、週、試験、variant、feature flag、schedule item は `taiga.production_seed` で投入する。これは本番 2 ユーザーが bootstrap 済みであることを確認し、canonical curriculum の assignment と schedule item を `taiga-albatross@softbank.ne.jp` に割り当てる。local demo submission、runner job、exam attempt fixture は投入しない。

```bash
cd backend
set -a
source ../.env.neon.local
set +a
LOCAL_STORAGE_ROOT=../local-storage-production \
CURRICULUM_SOURCE_DIR=../../design/taiga-42-v4.0-implementation-pack/curriculum \
FRONTEND_ORIGINS=https://app.taiganova.app \
CLOUDFLARE_ACCESS_TEAM_DOMAIN=https://taiganova.cloudflareaccess.com \
CLOUDFLARE_ACCESS_AUD="<web-access-audience>" \
AUTHORIZED_USER_EMAILS=shomabirdie@icloud.com,taiga-albatross@softbank.ne.jp \
../.venv/bin/python -m taiga.production_seed
```

投入後の期待件数:

- `weeks`: 28
- `task_templates`: 196
- `task_assignments` for `taiga-albatross@softbank.ne.jp`: 196
- `exams`: 28
- `exam_variants`: 56
- `schedule_items`: 2026-07-27 から 2027-03-26 まで全日分

## Free tier 注意

Neon Free は storage、compute、scale-to-zero、backup/restore に制限がある。運用前後で dashboard の plan/limit を確認する。

公式参照:

- https://neon.com/docs/introduction/plans
- https://neon.com/docs/introduction/usage-calculations
- https://neon.com/docs/guides/scale-to-zero-guide
- https://neon.com/docs/guides/backup-restore
