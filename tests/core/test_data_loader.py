"""Tests for taximate.core.data_loader."""

from pathlib import Path

import pandas as pd
import pytest

from taximate.core.data_loader import (
    filter_by_column,
    get_summary_by_group,
    get_unique_values,
    load_csvs_from_paths,
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
    df = load_csvs_from_paths([csv_files[0]])
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "source_file" in df.columns
    assert "Amount" in df.columns
    assert "Date" in df.columns


def test_load_csvs_from_paths_multiple_files(data_dir: Path) -> None:
    csv_files = list(data_dir.glob("*.csv"))
    assert len(csv_files) >= 2
    df = load_csvs_from_paths(csv_files[:2])
    assert len(df) > 0
    assert df["source_file"].nunique() == 2


def test_load_csvs_amounts_are_numeric(data_dir: Path) -> None:
    csv_files = list(data_dir.glob("*.csv"))
    df = load_csvs_from_paths([csv_files[0]])
    assert pd.api.types.is_float_dtype(df["Amount"])


def test_get_unique_values(data_dir: Path) -> None:
    csv_files = list(data_dir.glob("*.csv"))
    df = load_csvs_from_paths([csv_files[0]])
    groups = get_unique_values(df, "Group")
    assert isinstance(groups, list)
    assert len(groups) > 0
    # values should be sorted
    assert groups == sorted(groups)


def test_filter_by_column(data_dir: Path) -> None:
    csv_files = list(data_dir.glob("*.csv"))
    df = load_csvs_from_paths([csv_files[0]])
    groups = get_unique_values(df, "Group")
    first_group = groups[0]
    filtered = filter_by_column(df, "Group", [first_group])
    assert not filtered.empty
    assert (filtered["Group"] == first_group).all()


def test_filter_by_column_no_match(data_dir: Path) -> None:
    csv_files = list(data_dir.glob("*.csv"))
    df = load_csvs_from_paths([csv_files[0]])
    filtered = filter_by_column(df, "Group", ["__nonexistent__"])
    assert filtered.empty


def test_get_summary_by_group(data_dir: Path) -> None:
    csv_files = list(data_dir.glob("*.csv"))
    df = load_csvs_from_paths([csv_files[0]])
    summary = get_summary_by_group(df)
    assert isinstance(summary, pd.DataFrame)
    assert "Group" in summary.columns
    assert "Item" in summary.columns
    assert "Amount" in summary.columns
    # summary should have fewer rows than the original (grouped)
    assert len(summary) <= len(df)
