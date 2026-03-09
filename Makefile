.PHONY: install run format check test clean build-mac build-windows clean-build

install:
	uv sync

run:
	@QT_QPA_PLATFORM=xcb uv run python main.py

format:
	@uv run ruff check --fix
	@uv run ruff format

check:
	@uv run ruff check && \
	uv run ruff format --check && \
	uv run mypy --config-file .mypy.ini --cache-dir .mypy_cache .

test:
	@QT_QPA_PLATFORM=offscreen uv run pytest

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + ; rm -rf .venv .mypy_cache

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