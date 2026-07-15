.PHONY: install format check test build run clean

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

# Build + stage the wheel, then serve the app at localhost:5173/taximate/ (Vite dev).
# Re-run after Python-core changes; JS hot-reloads.
run: build
	@WHEEL_PATH=$$(ls -t dist/*.whl | head -1) && cp "$$WHEEL_PATH" src/js/public/ && WHEEL=$$(basename "$$WHEEL_PATH") && VERSION=$$(grep -m1 '^version' pyproject.toml | cut -d'"' -f2) && printf '{"wheel":"%s","version":"%s"}\n' "$$WHEEL" "$$VERSION" > src/js/public/manifest.json && echo "Staged $$WHEEL (v$$VERSION); serving at http://localhost:5173/taximate/"
	@[ -d src/js/node_modules ] || npm --prefix src/js install
	npm --prefix src/js run dev

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + ; rm -rf .venv .mypy_cache dist
