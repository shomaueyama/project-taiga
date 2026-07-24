# Backup And Restore Runbook

Status: manual lightweight plan for the two-user free deployment.

## Backup

Recommended frequency: weekly while usage is low, and before every migration.

Use a logical PostgreSQL export from an approved operator machine:

```bash
pg_dump "$DATABASE_URL" --format=custom --file taiga-nova-YYYYMMDD.dump
```

Store the dump in a private, encrypted location. Do not commit dumps.

## Restore Drill

1. Create a temporary Neon database.
2. Restore the dump:

```bash
pg_restore --dbname "$RESTORE_DATABASE_URL" taiga-nova-YYYYMMDD.dump
```

3. Run:

```bash
cd backend
DATABASE_URL="$RESTORE_DATABASE_URL" alembic current
```

4. Point a local backend at the restored database and verify core read paths.

## Risks

Free-tier database services do not replace tested backups. Backup automation is intentionally not
added in Phase 7.2 to avoid new secrets or paid services.

