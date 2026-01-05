.PHONY: help install dev test lint format run docker-build docker-up docker-down clean

help:
	@echo "AgentOps Studio - Development Commands"
	@echo ""
	@echo "install       Install production dependencies"
	@echo "dev           Install development dependencies"
	@echo "test          Run tests"
	@echo "lint          Run linters (ruff, mypy)"
	@echo "format        Format code with black"
	@echo "run           Run development server"
	@echo "docker-build  Build Docker image"
	@echo "docker-up     Start Docker Compose stack"
	@echo "docker-down   Stop Docker Compose stack"
	@echo "clean         Clean cache and build files"

install:
	poetry install --no-dev

dev:
	poetry install

test:
	poetry run pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	poetry run ruff check app/
	poetry run mypy app/

format:
	poetry run black app/ tests/
	poetry run ruff check --fix app/

run:
	poetry run python -m app.main

docker-build:
	docker build -t agentops-studio:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf dist/ build/
