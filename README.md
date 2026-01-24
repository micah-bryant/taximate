# Taximate

A Python application that imports transaction data from EveryDollar CSV exports and calculates self-employment taxes including sales tax, sole proprietor tax, federal and state income taxes.

## Features

- Load and combine multiple CSV transaction files
- GUI for categorizing transactions into income/expense types
- Automatic tax calculations for self-employed/sole proprietors
- Calculates sales tax, self-employment tax, federal and state income taxes
- Shows total take-home pay and gross revenue

## Installation

```bash
uv sync
```

## Usage

1. Export your EveryDollar transactions as CSV files
2. Place the CSV files in the `data/` folder
3. Run the application:

```bash
uv run python main.py
```

4. Click "Load CSV Data" to import transactions
5. Select items and assign them to the appropriate income/expense categories
6. Click "Calculate Taxes" to see your tax summary

## Income Categories

| Category | Description |
|----------|-------------|
| **Gigs (Tax Already Paid)** | Income where sales tax and income tax are already withheld (e.g., W-2 gig work) |
| **Revenue (No Sales Tax)** | Business revenue that needs sales tax calculated (7.75%) |
| **Revenue (Sales Tax Included)** | Business revenue where sales tax is already included |
| **Business Expenses** | Deductible business expenses |

## Tax Calculations

The following taxes are calculated based on your categorized transactions:

| Output | Formula |
|--------|---------|
| Sales Tax Due | Revenue (No Sales Tax) * 7.75% |
| Profit | (Revenue No Tax - Sales Tax) + Revenue With Tax - Expenses |
| Sole Proprietor Tax | (Profit * 92.35%) * 15.3% |
| Federal Income Tax | (Profit - SE Tax * 50%) * 17% |
| State Income Tax | (Profit - SE Tax * 50%) * 5% |
| Total Income Tax | SE Tax + Federal + State |
| Take Home Pay | Profit + Gigs - Total Income Tax |
| Gross Revenue | Gigs + Revenue No Tax + Revenue With Tax - Expenses |

## Project Structure

```
taximate/
├── main.py              # Entry point
├── pyproject.toml       # Dependencies
├── Makefile             # Build commands
├── data/                # CSV transaction files
├── test_data/           # Sample test data
└── src/
    ├── data_loader.py   # CSV loading utilities
    ├── tax_calculator.py # Tax calculation logic
    └── gui.py           # Tkinter GUI
```

## Development

```bash
make install   # Install dependencies
make run       # Run the application
make format    # Format code with ruff
make check     # Lint and type check
make clean     # Remove .venv and caches
```
