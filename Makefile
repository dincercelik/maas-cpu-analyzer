.PHONY: help install install-dev test test-unit test-integration test-coverage lint format security clean docs

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in development mode
	pip install -e .

install-dev: ## Install the package with development dependencies
	pip install -e ".[dev]"

test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	pytest --cov=maas_cpu_analyzer --cov-report=html --cov-report=term-missing

lint: ## Run linting checks
	flake8 maas_cpu_analyzer/ tests/ --max-line-length=88 --extend-ignore=E203,W503,E501,D100,D101,D102,D103,D104,D105,D107,D400,D401,I100,I201

format: ## Format code with black and isort
	black maas_cpu_analyzer/ tests/
	isort maas_cpu_analyzer/ tests/

format-check: ## Check code formatting
	black --check --diff maas_cpu_analyzer/ tests/
	isort --check-only --diff maas_cpu_analyzer/ tests/

security: ## Run security checks
	bandit -r maas_cpu_analyzer/ -ll
	safety check

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .tox/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

docs: ## Build documentation
	sphinx-build -W -b html docs/ docs/_build/html

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

ci: ## Run CI pipeline (lint, test, security)
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) security

pre-commit: ## Run pre-commit checks
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test-unit
