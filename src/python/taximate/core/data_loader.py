"""CSV data loading and validation for Taximate.

Loads EveryDollar CSV transaction exports into validated :class:`TransactionRow`
models. Two entry points are provided:

- :func:`load_csvs_from_paths` reads files from disk (used by tests).
- :func:`load_csvs_from_strings` accepts ``(name, text)`` pairs, for the browser
  (Pyodide), where uploaded files are read as text and never touch a real
  filesystem.

User-supplied CSVs are untrusted, so every row is validated with pydantic: a
malformed ``Amount`` raises a clear ``ValidationError`` instead of silently
becoming ``NaN``.

Supported CSV format (EveryDollar export): a header row with at least ``Item``
and ``Amount`` columns; extra columns (Date, Group, Type, Merchant) are ignored.
Calculations key off the ``Item`` column.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from io import StringIO
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class TransactionRow(BaseModel):
    """A single validated transaction from an EveryDollar CSV export."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    item: str = Field(alias="Item")
    amount: float = Field(alias="Amount")
    source_file: str = ""


def _parse_csv(name: str, text: str) -> list[TransactionRow]:
    reader = csv.DictReader(StringIO(text))
    return [TransactionRow.model_validate({**record, "source_file": name}) for record in reader]


def load_csvs_from_strings(files: Sequence[tuple[str, str]]) -> list[TransactionRow]:
    """Load and combine CSVs from ``(name, text)`` pairs (the browser path).

    Raises:
        FileNotFoundError: If no files provided or none are CSV files.
    """
    if not files:
        raise FileNotFoundError("No files provided")

    csv_files = [(name, text) for name, text in files if name.lower().endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError("No valid CSV files found in the provided paths")

    rows: list[TransactionRow] = []
    for name, text in csv_files:
        rows.extend(_parse_csv(name, text))
    return rows


def load_csvs_from_paths(file_paths: Sequence[str | Path]) -> list[TransactionRow]:
    """Load and combine CSV files from a list of file paths.

    Raises:
        FileNotFoundError: If no files provided or no valid CSV files found.
    """
    if not file_paths:
        raise FileNotFoundError("No files provided")

    files: list[tuple[str, str]] = []
    for file_path in file_paths:
        path = Path(file_path)
        if path.suffix.lower() == ".csv" and path.exists():
            files.append((path.name, path.read_text()))

    if not files:
        raise FileNotFoundError("No valid CSV files found in the provided paths")
    return load_csvs_from_strings(files)


def unique_items(rows: Sequence[TransactionRow]) -> list[str]:
    """Return the sorted, unique transaction item names across ``rows``."""
    return sorted({row.item for row in rows})
