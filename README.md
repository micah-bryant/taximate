# Taximate

A Python application that imports transaction data from EveryDollar CSV exports and helps categorize expenses for tax calculations.

## Features

- Load and combine multiple CSV transaction files
- GUI for sorting transactions into tax categories
- Assign items to deductible categories (Business, Home Office, Medical, etc.)
- Calculate total deductions and taxable income

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
5. Select items from the list and assign them to tax categories
6. Click "Calculate Taxes" to see your summary

## Project Structure

```
taximate/
├── main.py              # Entry point
├── pyproject.toml       # Dependencies
├── data/                # CSV transaction files
└── src/
    ├── data_loader.py   # CSV loading utilities
    ├── tax_calculator.py # Tax calculation logic
    └── gui.py           # Tkinter GUI
```

## Tax Categories

- Business Expenses
- Home Office
- Vehicle/Mileage
- Medical
- Charitable
- Education
- Retirement
- Not Deductible
