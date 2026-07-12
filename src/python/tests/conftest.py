"""Shared pytest fixtures for taximate tests."""

from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent


@pytest.fixture
def data_dir() -> Path:
    """Sample EveryDollar CSVs used as CSV-loading test fixtures."""
    return _HERE / "fixtures"


@pytest.fixture
def tax_rates_dir() -> Path:
    """The tax_rates/ directory bundled inside the package."""
    return _HERE.parent / "taximate" / "tax_rates"
