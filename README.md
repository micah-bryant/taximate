# Taximate

A Python application that imports transaction data from EveryDollar CSV exports and calculates self-employment taxes including sales tax, sole proprietor tax, federal and state income taxes.

## Features

- Load and combine multiple CSV transaction files
- GUI for categorizing transactions into income/expense types
- Progressive tax bracket calculations for federal and California state income tax
- Self-employment tax with Social Security wage base cap
- Configurable tax rates stored in CSV files
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
| **Revenue (No Sales Tax)** | Business revenue that needs sales tax calculated |
| **Revenue (Sales Tax Included)** | Business revenue where sales tax is already included |
| **Business Expenses** | Deductible business expenses |

## Tax Calculations

Taxes are calculated using progressive brackets loaded from CSV files:

| Tax Type | Source |
|----------|--------|
| Federal Income Tax | 2025 IRS brackets (7 brackets: 10%-37%) |
| California State Tax | 2024 FTB brackets (10 brackets: 1%-13.3%) |
| Self-Employment Tax | Social Security (12.4%) + Medicare (2.9%) |
| Sales Tax | San Diego rate (7.75%) |

### Calculation Flow

1. **Sales Tax Due** = Revenue (No Sales Tax) × Sales Tax Rate
2. **Profit** = (Revenue No Tax - Sales Tax) + Revenue With Tax - Expenses
3. **Self-Employment Tax** = (Profit × 92.35%) × (12.4% SS + 2.9% Medicare)
4. **Taxable Income** = Profit - (SE Tax × 50%)
5. **Federal Income Tax** = Progressive bracket calculation on Taxable Income
6. **State Income Tax** = Progressive bracket calculation on Taxable Income
7. **Total Tax** = SE Tax + Federal Tax + State Tax
8. **Take Home** = Profit + Gigs - Total Tax

## Tax Rates Configuration

Tax rates are stored in CSV files in the `tax_rates/` directory:

| File | Contents |
|------|----------|
| `federal_income_tax_2025.csv` | Federal tax brackets by filing status |
| `california_income_tax_2024.csv` | California state tax brackets |
| `self_employment_tax_2025.csv` | Social Security and Medicare rates |
| `sales_tax_2025.csv` | Sales tax rates by jurisdiction |

To update tax rates, edit these CSV files directly.

## Project Structure

```
taximate/
├── main.py              # Entry point
├── pyproject.toml       # Dependencies
├── Makefile             # Build commands
├── data/                # CSV transaction files
├── test_data/           # Sample test data
├── tax_rates/           # Tax rate CSV files
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

## Data Sources

Tax rates sourced from:
- [IRS Federal Income Tax Brackets 2025](https://www.irs.gov/filing/federal-income-tax-rates-and-brackets)
- [California FTB Tax Rate Schedules](https://www.ftb.ca.gov/forms/2025/2025-540-tax-rate-schedules.pdf)
- [IRS Self-Employment Tax](https://www.irs.gov/businesses/small-businesses-self-employed/self-employment-tax-social-security-and-medicare-taxes)
- [California CDTFA Sales Tax Rates](https://cdtfa.ca.gov/taxes-and-fees/rates.aspx)
