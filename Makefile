.PHONY: help install install-dev test lint format clean run docker-build docker-run deploy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install

test: ## Run tests with coverage
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-quick: ## Run tests without coverage
	pytest tests/ -v

lint: ## Run linting checks
	black --check src tests
	ruff check src tests
	mypy src

format: ## Format code with black and ruff
	black src tests
	ruff check --fix src tests

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete

run: ## Run the application locally
	python -m src.main

run-dev: ## Run the application in development mode with reload
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

docker-build: ## Build Docker image
	docker build -f deployment/Dockerfile -t genai-learning-assistant:latest .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env genai-learning-assistant:latest

docker-compose-up: ## Start services with docker-compose
	docker-compose -f deployment/docker-compose.yml up -d

docker-compose-down: ## Stop services with docker-compose
	docker-compose -f deployment/docker-compose.yml down

docker-compose-logs: ## View logs from docker-compose
	docker-compose -f deployment/docker-compose.yml logs -f

deploy-aws: ## Deploy to AWS using CloudFormation
	aws cloudformation deploy \
		--template-file deployment/cloudformation.yml \
		--stack-name genai-learning-assistant \
		--capabilities CAPABILITY_IAM \
		--parameter-overrides ContainerImage=$(IMAGE)

setup-pre-commit: ## Set up pre-commit hooks
	pre-commit install
	pre-commit run --all-files

check: lint test ## Run all checks (lint + test)

all: clean install-dev check ## Clean, install, and check everything
