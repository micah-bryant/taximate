"""CSV data loading utilities for Taximate.

This module provides functions for loading and combining EveryDollar CSV
transaction exports. It handles multiple file loading, date parsing,
and amount conversion.

Supported CSV format (EveryDollar export):
    - Date: Transaction date (MM/DD/YYYY format)
    - Item: Transaction description/payee
    - Amount: Transaction amount (positive or negative)
    - Group: Budget category group
"""

from collections.abc import Sequence
from pathlib import Path

import pandas as pd


def load_csvs_from_paths(file_paths: Sequence[str | Path]) -> pd.DataFrame:
    """Load and combine CSV files from a list of file paths.

    Args:
        file_paths: Sequence of file paths (strings or Path objects) to load.

    Returns:
        Combined DataFrame with all transactions and a 'source_file' column.

    Raises:
        FileNotFoundError: If no files provided or no valid CSV files found.
    """
    if not file_paths:
        raise FileNotFoundError("No files provided")

    dataframes = []
    for file_path in file_paths:
        path = Path(file_path)
        if path.suffix.lower() == ".csv" and path.exists():
            df = pd.read_csv(path)
            df["source_file"] = path.name
            dataframes.append(df)

    if not dataframes:
        raise FileNotFoundError("No valid CSV files found in the provided paths")

    combined_df = pd.concat(dataframes, ignore_index=True)

    # Clean up the Amount column - convert to float
    combined_df["Amount"] = pd.to_numeric(combined_df["Amount"], errors="coerce")

    # Parse dates
    combined_df["Date"] = pd.to_datetime(combined_df["Date"], format="%m/%d/%Y", errors="coerce")

    return combined_df


def load_all_csvs(data_dir: str = "data") -> pd.DataFrame:
    """Load all CSV files from a directory and combine them.

    Args:
        data_dir: Path to directory containing CSV files.

    Returns:
        Combined DataFrame with all transactions.

    Raises:
        FileNotFoundError: If directory doesn't exist or contains no CSV files.
    """
    data_path = Path(data_dir)

    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    csv_files = list(data_path.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {data_dir}")

    return load_csvs_from_paths(csv_files)


def get_unique_values(df: pd.DataFrame, column: str) -> list:
    """Get sorted unique values from a DataFrame column.

    Args:
        df: Source DataFrame.
        column: Column name to extract unique values from.

    Returns:
        Sorted list of unique non-null values.
    """
    return sorted(df[column].dropna().unique().tolist())


def filter_by_column(df: pd.DataFrame, column: str, values: list) -> pd.DataFrame:
    """Filter DataFrame to rows where column matches any of the given values.

    Args:
        df: Source DataFrame.
        column: Column name to filter on.
        values: List of values to include.

    Returns:
        Filtered DataFrame.
    """
    return df[df[column].isin(values)]


def get_summary_by_group(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate transaction amounts by Group and Item.

    Args:
        df: Source DataFrame with 'Group', 'Item', and 'Amount' columns.

    Returns:
        DataFrame with summed amounts grouped by Group and Item.
    """
    return df.groupby(["Group", "Item"])["Amount"].sum().reset_index()
