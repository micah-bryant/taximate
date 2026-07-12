"""Tests for taximate.core.data_loader."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from taximate.core.data_loader import (
    TransactionRow,
    load_csvs_from_paths,
    load_csvs_from_strings,
    unique_items,
)


def test_load_csvs_from_paths_no_files() -> None:
    with pytest.raises(FileNotFoundError, match="No files provided"):
        load_csvs_from_paths([])


def test_load_csvs_from_paths_no_valid_files(tmp_path: Path) -> None:
    txt_file = tmp_path / "not_a_csv.txt"
    txt_file.write_text("hello")
    with pytest.raises(FileNotFoundError, match="No valid CSV files found"):
        load_csvs_from_paths([txt_file])


def test_load_csvs_from_paths_single_file(data_dir: Path) -> None:
    csv_files = list(data_dir.glob("*.csv"))
    assert csv_files, "Expected CSV files in data/"
    rows = load_csvs_from_paths([csv_files[0]])
    assert isinstance(rows, list)
    assert rows
    assert all(isinstance(r, TransactionRow) for r in rows)
    assert rows[0].source_file == csv_files[0].name
    assert isinstance(rows[0].amount, float)
    assert rows[0].item


def test_load_csvs_from_paths_multiple_files(data_dir: Path) -> None:
    csv_files = list(data_dir.glob("*.csv"))
    assert len(csv_files) >= 2
    rows = load_csvs_from_paths(csv_files[:2])
    assert len(rows) > 0
    assert len({r.source_file for r in rows}) == 2


def test_load_csvs_amounts_are_float(data_dir: Path) -> None:
    csv_files = list(data_dir.glob("*.csv"))
    rows = load_csvs_from_paths([csv_files[0]])
    assert all(isinstance(r.amount, float) for r in rows)


def test_load_csvs_from_strings() -> None:
    rows = load_csvs_from_strings(
        [("jan.csv", "Item,Amount\nConsulting,1500.00\nSupplies,-42.50\n")]
    )
    assert [r.item for r in rows] == ["Consulting", "Supplies"]
    assert rows[0].amount == pytest.approx(1500.0)
    assert rows[1].amount == pytest.approx(-42.5)
    assert all(r.source_file == "jan.csv" for r in rows)


def test_load_csvs_from_strings_no_files() -> None:
    with pytest.raises(FileNotFoundError, match="No files provided"):
        load_csvs_from_strings([])


def test_load_csvs_from_strings_no_csv() -> None:
    with pytest.raises(FileNotFoundError, match="No valid CSV files found"):
        load_csvs_from_strings([("notes.txt", "hello")])


def test_invalid_amount_raises_validation_error() -> None:
    """Untrusted input with a non-numeric Amount fails loudly (not silent NaN)."""
    with pytest.raises(ValidationError):
        load_csvs_from_strings([("bad.csv", "Item,Amount\nConsulting,not_a_number\n")])


def test_missing_amount_column_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        load_csvs_from_strings([("bad.csv", "Item\nConsulting\n")])


def test_unique_items_sorted_and_deduped() -> None:
    rows = load_csvs_from_strings([("a.csv", "Item,Amount\nB,1\nA,2\nB,3\n")])
    assert unique_items(rows) == ["A", "B"]
