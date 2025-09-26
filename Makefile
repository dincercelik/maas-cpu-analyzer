.PHONY: help install install-dev test test-unit test-integration test-coverage test-performance test-quality lint format security clean docs pep8 pylint pre-commit

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in development mode
	pip install -e .

install-dev: ## Install the package with development dependencies
	pip install -e ".[dev]"

test: ## Run all tests
	pytest -v

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	pytest --cov=maas_cpu_analyzer --cov-report=html --cov-report=term-missing

lint: ## Run linting checks
	flake8 maas_cpu_analyzer/ tests/ --config=.flake8

format: ## Format code with black and isort
	black maas_cpu_analyzer/ tests/
	isort maas_cpu_analyzer/ tests/

format-check: ## Check code formatting
	black --check --diff maas_cpu_analyzer/ tests/
	isort --check-only --diff maas_cpu_analyzer/ tests/

security: ## Run security checks
	bandit -r maas_cpu_analyzer/ -ll
	# Prefer pip-audit (PyPA) over deprecated safety check
	pip-audit -r requirements.txt -r requirements-test.txt

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .tox/
	rm -rf docs/_build/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

clean-all: clean docker-clean docs-clean ## Clean all artifacts including Docker and docs

docs: ## Build documentation
	sphinx-build -W -b html docs/ docs/_build/html

test-docs: ## Test documentation build and content
	pytest tests/documentation/ -v

docs-clean: ## Clean documentation build artifacts
	rm -rf docs/_build/

docker-build: ## Build Docker image
	docker build -t maas-cpu-analyzer .

docker-run: ## Run Docker container (requires environment variables)
	docker run --rm maas-cpu-analyzer --help

docker-compose-up: ## Run with Docker Compose
	@echo "Note: Create a .env file with your configuration (see docker.env.example)"
	docker-compose up maas-cpu-analyzer

docker-compose-dev: ## Run development container with live code reloading
	@echo "Note: Create a .env file with your configuration (see docker.env.example)"
	docker-compose up maas-cpu-analyzer-dev

docker-clean: ## Clean Docker images and containers
	docker-compose down
	docker rmi maas-cpu-analyzer || true

tox: ## Run tox tests
	tox

tox-lint: ## Run tox linting
	tox -e lint

tox-format: ## Run tox formatting
	tox -e format

tox-security: ## Run tox security checks
	tox -e security

build: ## Build the package
	python -m build

install-tox: ## Install tox
	pip install tox

ci: ## Run CI pipeline (lint, test, security, docs)
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) security
	$(MAKE) docs
	$(MAKE) test-docs

pre-commit: ## Run pre-commit checks
	pre-commit run --all-files

test-performance: ## Run performance tests
	pytest tests/performance/ -v --benchmark-only

test-quality: ## Run code quality checks
	radon cc maas_cpu_analyzer/ --min A
	radon mi maas_cpu_analyzer/ --min A
	xenon maas_cpu_analyzer/ --max-absolute A --max-modules A --max-average A
	vulture maas_cpu_analyzer/ --min-confidence 100

pep8: ## Run PEP 8 style checks
	flake8 maas_cpu_analyzer/ tests/ --config=.flake8

pylint: ## Run pylint static analysis
	pylint maas_cpu_analyzer/

install-pre-commit: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install

setup-dev: ## Setup development environment
	$(MAKE) install-dev
	$(MAKE) install-pre-commit
	$(MAKE) format
	$(MAKE) test

ci-full: ## Run full CI pipeline
	$(MAKE) pep8
	$(MAKE) pylint
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) test-performance
	$(MAKE) test-quality
	$(MAKE) security
	$(MAKE) docs
	$(MAKE) test-docs
