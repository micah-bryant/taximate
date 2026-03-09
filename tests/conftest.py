"""Shared pytest fixtures for taximate tests."""

from pathlib import Path

import pytest


@pytest.fixture
def data_dir() -> Path:
    """Path to the data/ directory for CSV loading tests."""
    return Path(__file__).parent.parent / "data"


@pytest.fixture
def tax_rates_dir() -> Path:
    """Path to the tax_rates/ directory."""
    return Path(__file__).parent.parent / "tax_rates"
