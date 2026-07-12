.PHONY: install format check test build clean

install:
	uv sync

format:
	@uv run ruff check --fix
	@uv run ruff format

check:
	@uv run ruff check && \
	uv run ruff format --check && \
	uv run mypy src/python

test:
	@uv run pytest

build:
	uv build --wheel

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + ; rm -rf .venv .mypy_cache dist
