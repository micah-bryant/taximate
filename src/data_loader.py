from pathlib import Path

import pandas as pd


def load_all_csvs(data_dir: str = "data") -> pd.DataFrame:
    """Load all CSV files from the data directory and combine them."""
    data_path = Path(data_dir)

    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    csv_files = list(data_path.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {data_dir}")

    dataframes = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        df["source_file"] = csv_file.name
        dataframes.append(df)

    combined_df = pd.concat(dataframes, ignore_index=True)

    # Clean up the Amount column - convert to float
    combined_df["Amount"] = pd.to_numeric(combined_df["Amount"], errors="coerce")

    # Parse dates
    combined_df["Date"] = pd.to_datetime(combined_df["Date"], format="%m/%d/%Y", errors="coerce")

    return combined_df


def get_unique_values(df: pd.DataFrame, column: str) -> list:
    """Get unique values from a column."""
    return sorted(df[column].dropna().unique().tolist())


def filter_by_column(df: pd.DataFrame, column: str, values: list) -> pd.DataFrame:
    """Filter dataframe by column values."""
    return df[df[column].isin(values)]


def get_summary_by_group(df: pd.DataFrame) -> pd.DataFrame:
    """Get sum of amounts grouped by Group and Item."""
    return df.groupby(["Group", "Item"])["Amount"].sum().reset_index()
