COMPOSE := docker compose

.PHONY: setup up down logs migrate seed lint typecheck test test-backend test-frontend test-coverage test-e2e validate reset

setup:
	cp -n .env.example .env || true

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

migrate:
	$(COMPOSE) run --rm backend alembic upgrade head

seed:
	$(COMPOSE) run --rm backend python -m taiga.seed

lint:
	cd backend && ../.venv/bin/ruff check .
	cd frontend && npm run lint

typecheck:
	cd backend && ../.venv/bin/mypy src tests
	cd frontend && npm run typecheck

test: test-backend test-frontend

test-backend:
	cd backend && DATABASE_URL=$${DATABASE_URL:-postgresql+psycopg://taiga:taiga@localhost:5432/taiga} CURRICULUM_SOURCE_DIR=$${CURRICULUM_SOURCE_DIR:-../../design/taiga-42-v4.0-implementation-pack/curriculum} LOCAL_STORAGE_ROOT=$${LOCAL_STORAGE_ROOT:-../local-storage} ../.venv/bin/pytest

test-frontend:
	cd frontend && npm test -- --run

test-coverage:
	cd backend && DATABASE_URL=$${DATABASE_URL:-postgresql+psycopg://taiga:taiga@localhost:5432/taiga} CURRICULUM_SOURCE_DIR=$${CURRICULUM_SOURCE_DIR:-../../design/taiga-42-v4.0-implementation-pack/curriculum} LOCAL_STORAGE_ROOT=$${LOCAL_STORAGE_ROOT:-../local-storage} ../.venv/bin/pytest --cov=taiga --cov-report=term-missing
	cd frontend && npm run test:coverage -- --run

test-e2e:
	cd frontend && npm run test:e2e

validate:
	$(COMPOSE) config --quiet
	cd backend && ../.venv/bin/python -m taiga.validation

reset:
	$(COMPOSE) down -v
	rm -rf local-storage/uploads/* local-storage/artifacts/* local-storage/results/*
