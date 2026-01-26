.PHONY: install run format check clean build-mac build-windows clean-build

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
PYINSTALLER_EXCLUDES = --exclude-module matplotlib --exclude-module scipy --exclude-module PIL --exclude-module Pillow --exclude-module IPython --exclude-module notebook --exclude-module pytest

build-mac-intel:
	uv run pyinstaller --windowed --onedir --noupx $(PYINSTALLER_EXCLUDES) --add-data "tax_rates:tax_rates" --name Taximate-mac-intel main.py

build-mac-arm64:
	uv run pyinstaller --windowed --onedir --noupx $(PYINSTALLER_EXCLUDES) --add-data "tax_rates:tax_rates" --name Taximate-mac-arm64 main.py

build-windows:
	uv run pyinstaller --onedir --noconsole --noupx $(PYINSTALLER_EXCLUDES) --add-data "tax_rates;tax_rates" --name Taximate-windows main.py

clean-build:
	rm -rf build dist