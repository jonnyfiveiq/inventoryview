.PHONY: dev test lint build

dev:
	docker compose -f docker/docker-compose.yml up -d

test:
	cd backend && python -m pytest -v

lint:
	cd backend && python -m ruff check src/ tests/
	cd backend && python -m ruff format --check src/ tests/

build:
	docker build -t inventoryview:dev -f backend/Dockerfile .
