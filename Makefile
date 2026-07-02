.PHONY: help install test cov lint type check demo serve docker-build docker-run clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:  ## Install core + api + dev tooling
	uv sync --all-extras

test:  ## Run the test suite
	uv run pytest

cov:  ## Run tests with coverage
	uv run pytest --cov=stunassure --cov-report=term-missing

lint:  ## Lint with ruff
	uv run ruff check src tests

type:  ## Strict type-check with mypy
	uv run mypy

check: cov lint type  ## Full quality gate (tests + coverage + lint + types)

demo:  ## Run the end-to-end verification demo (clean salmon batch)
	uv run stunassure demo --species atlantic_salmon --lot 50000 --failure-rate 0.0

serve:  ## Run the HTTP API locally on :8000
	uv run uvicorn stunassure.api:app --reload --port 8000

docker-build:  ## Build the API container image
	docker build -t stunassure:local .

docker-run:  ## Run the API container on :8000
	docker run --rm -p 8000:8000 stunassure:local

clean:  ## Remove caches and build artifacts
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
