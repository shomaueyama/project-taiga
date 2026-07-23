COMPOSE := docker compose

.PHONY: setup up down logs migrate seed lint typecheck test test-backend test-frontend test-e2e validate reset

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
	cd backend && ruff check .
	cd frontend && npm run lint

typecheck:
	cd backend && mypy src tests
	cd frontend && npm run typecheck

test: test-backend test-frontend

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm test -- --run

test-e2e:
	cd frontend && npm run test:e2e

validate:
	$(COMPOSE) config --quiet
	cd backend && python -m taiga.validation

reset:
	$(COMPOSE) down -v
	rm -rf local-storage/uploads/* local-storage/artifacts/* local-storage/results/*
