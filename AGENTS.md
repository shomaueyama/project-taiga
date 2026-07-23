# Project Taiga Agent Instructions

Follow the implementation pack authority order in `../design/taiga-42-v4.0-implementation-pack/01_SOURCE_OF_TRUTH.md`.

## Local Scope

- Build and validate the Docker Compose Local MVP.
- Do not modify the design pack.
- Do not create AWS resources or require AWS credentials.
- Keep LocalAuth enabled only when `APP_ENV=local` and `LOCAL_AUTH_ENABLED=true`.
- Keep `RUNNER_ENABLED=false` and `EXAM_ENABLED=false` until their release gates pass.

## Architecture

- Backend is a modular monolith.
- Domain code must not depend on FastAPI, SQLAlchemy, Docker SDK, AWS SDK, or external notification services.
- Infrastructure implements application ports.
- Learner code must execute only in disposable runner containers.
- Frontend components must not call `fetch` directly.
- Feature modules must not import each other's internal files.

## Git

- Do not push forcefully.
- Do not merge feature PRs into `main` without user confirmation.
- Use focused Conventional Commits.
- Never commit secrets, `.env`, database volumes, uploads, artifacts, results, or hidden test payloads.

