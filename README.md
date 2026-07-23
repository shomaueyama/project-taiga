# Project Taiga

Local-first learning platform MVP for Project Taiga.

This repository is implemented from the Project Taiga v4.0 Implementation Pack in:

```text
../design/taiga-42-v4.0-implementation-pack
```

The design pack is read-only. Application code, tests, migrations, and local documentation live in this repository.

## Local Targets

- Frontend: http://localhost:5173
- API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Core Commands

```bash
make setup
make up
make migrate
make seed
make lint
make typecheck
make test
make validate
make down
```

## Local Safety Defaults

- `APP_ENV=local`
- `LOCAL_AUTH_ENABLED=true`
- `RUNNER_ENABLED=false`
- `EXAM_ENABLED=false`

AWS deployment and production connections are out of scope for the Local MVP.

