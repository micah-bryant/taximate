.PHONY: install run format check clean build-mac clean-build

install:
	uv sync

run:
	uv run python main.py

format:
	@uv run ruff check --fix
	@uv run ruff format

check:
	@uv run ruff check && \
	uv run ruff format --check && \
	uv run mypy --config-file .mypy.ini --cache-dir .mypy_cache .

clean:
	rm -rf .venv __pycache__ src/__pycache__ .mypy_cache

# PyInstaller build targets
build-mac:
	uv run pyinstaller taximate_mac.spec --noconfirm

clean-build:
	rm -rf build dist