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
build-mac-intel:
	uv run pyinstaller --windowed --onefile --name Taximate-mac-intel main.py

build-mac-arm64:
	uv run pyinstaller --windowed --onefile --name Taximate-mac-arm64 main.py

build-windows:
	uv run pyinstaller --onefile --noconsole --name Taximate-windows main.py

clean-build:
	rm -rf build dist