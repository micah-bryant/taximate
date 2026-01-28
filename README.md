# Taximate

A Python GUI application that imports transaction data from EveryDollar CSV exports and calculates self-employment taxes including sales tax, sole proprietor tax, federal and state income taxes.

> **⚠️ Disclaimer:** This application is for informational and educational purposes only. It is **not** financial, tax, or legal advice. Tax laws are complex and vary by jurisdiction. Always consult a qualified tax professional or accountant for advice specific to your situation. The developers are not responsible for any errors in calculations or any decisions made based on the output of this application.

## Features

- **Drag-and-drop file loading** - Drop multiple CSV files directly onto the app
- **Multi-file support** - Load and combine multiple CSV transaction files at once
- **File browser** - Select CSV files from anywhere on your system
- **Transaction categorization** - Assign transactions to income/expense categories
- **Deduction calculators** - Built-in calculators for home office and car deductions
- **Side-by-side comparison** - View current period and annualized tax calculations together
- **Progressive tax brackets** - Federal and California state income tax calculations
- **Self-employment tax** - Social Security and Medicare with wage base cap
- **Configurable tax rates** - Tax rates stored in editable CSV files
- **Annual projections** - Extrapolate partial year data to annual estimates

## Installation

```bash
uv sync
```

### Linux/WSL Requirements

On Linux or WSL, you may need to install Qt system dependencies:

```bash
sudo apt install -y libegl1 libxkbcommon0 libxcb-cursor0
```

## Usage

1. Export your EveryDollar transactions as CSV files
2. Run the application:

```bash
make run
# or
uv run python main.py
```

3. Load your CSV files using one of these methods:
   - **Drag and drop** multiple CSV files onto the drop zone
   - **Click "Browse Files"** to select files from anywhere on your system
   - Files can be loaded incrementally - new files are added to existing data

4. Select items in the left panel and assign them to income/expense categories
5. Set the number of months your data covers (for annual projections)
6. Click "Calculate Taxes" to see your tax summary with period and annualized columns

## Income Categories

| Category | Description |
|----------|-------------|
| **Freelance (Tax Already Paid)** | Income where taxes are already withheld (e.g., W-2 gig work) |
| **Revenue (Sales Tax Bundled)** | Business revenue with sales tax included in the price |
| **Revenue (Sales Tax Applied)** | Business revenue where sales tax was collected separately |
| **Business Expenses** | Deductible business expenses |

## Deduction Calculators

The application includes built-in calculators for common self-employment deductions. Click the deduction buttons in the Tax Summary panel to open the calculator dialogs.

### Home Office Deduction

Calculate your home office deduction based on:
- **Office Space Percentage** - The percentage of your home used exclusively for business
- **Monthly Rent** - Your monthly rent or mortgage payment
- **Monthly Utilities** - Electric, gas, water, internet, etc.
- **Monthly Insurance** - Renter's or homeowner's insurance

The deduction is calculated as: `(Rent + Utilities + Insurance) × Office % × Months`

### Car Deduction

Choose between two mutually exclusive methods:

| Method | Calculation |
|--------|-------------|
| **Standard Mileage Rate** | Business miles driven × $0.70/mile (2024 IRS rate) |
| **Actual Expenses** | (Business miles ÷ Total miles) × Cost of car |

The Standard Mileage Rate is simpler but the Actual Expenses method may result in a larger deduction for expensive vehicles with high business use.

## Tax Summary Display

The tax summary shows two columns side-by-side:
- **Period** - Actual values for the months of data loaded
- **Annual** - Projected values extrapolated to 12 months

```
                            PERIOD        ANNUAL
                            (6 mo)       (12 mo)
========================================================

--- INCOME ---
Freelance (Tax Already Paid) $  5,000.00  $ 10,000.00
Revenue (Sales Tax Bundled)  $ 12,000.00  $ 24,000.00
Business Expenses            $ -2,000.00  $ -4,000.00
Deductions                   $ -1,500.00  $ -3,000.00
...

--- TAXES ---
Sales Tax (7.75%)            $    862.07  $  1,724.14
Self-Employment Tax          $  1,847.23  $  3,694.46
...

--- SUMMARY ---
TAKE HOME                    $ 11,234.56  $ 22,469.12
```

## Tax Calculations

Taxes are calculated using progressive brackets loaded from CSV files:

| Tax Type | Source |
|----------|--------|
| Federal Income Tax | 2025 IRS brackets (7 brackets: 10%-37%) |
| California State Tax | 2024 FTB brackets (10 brackets: 1%-13.3%) |
| Self-Employment Tax | Social Security (12.4%) + Medicare (2.9%) |
| Sales Tax | San Diego rate (7.75%) |

### Calculation Flow

1. **Sales Tax** = Revenue (Bundled) / (1 + rate) × rate
2. **Business Profit** = Sales Taxable + Revenue (Applied) - Expenses - Deductions
3. **Total Profit** = Business Profit + Freelance Income
4. **Self-Employment Tax** = (Business Profit × 92.35%) × (12.4% SS + 2.9% Medicare)
5. **Taxable Income** = Business Profit - (SE Tax × 50%)
6. **Federal Income Tax** = Progressive bracket calculation
7. **State Income Tax** = Progressive bracket calculation
8. **Take Home** = Total Profit - Total Income Tax

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
├── main.py              # Application entry point
├── pyproject.toml       # Project dependencies and metadata
├── Makefile             # Build and development commands
├── data/                # Sample CSV transaction files
├── tax_rates/           # Tax rate configuration CSV files
│   ├── federal_income_tax_2025.csv
│   ├── california_income_tax_2024.csv
│   ├── self_employment_tax_2025.csv
│   └── sales_tax_2025.csv
└── src/
    ├── __init__.py      # Package initialization
    ├── data_loader.py   # CSV file loading and parsing
    ├── tax_calculator.py # Tax calculation engine
    └── gui.py           # PySide6 GUI with modern styling
```

## Development

```bash
make install      # Install dependencies
make run          # Run the application
make format       # Format code with ruff
make check        # Lint and type check
make clean        # Remove .venv and caches
make clean-build  # Remove PyInstaller build artifacts
```

## Building Standalone Executables

The application can be built as a standalone executable using PyInstaller. Builds use `--onedir` mode for faster startup times.

### macOS

```bash
make build-mac-intel   # Intel Macs
make build-mac-arm64   # Apple Silicon Macs
```

This creates a `.app` bundle in `dist/Taximate-mac-intel/` or `dist/Taximate-mac-arm64/`. The app can be distributed to users without requiring Python installation.

### Windows

```bash
make build-windows
```

This creates an executable in `dist/Taximate-windows/`. Distribute the entire folder to users.

### Build Output Structure

```
dist/
├── Taximate-mac-intel.app    # macOS Intel app bundle
├── Taximate-mac-arm64.app    # macOS Apple Silicon app bundle
└── Taximate-windows/         # Windows folder
    ├── Taximate-windows.exe
    └── (supporting files)
```

### Build Options

The build process includes optimizations for faster startup:
- `--onedir`: Files are unpacked (no extraction delay on launch)
- `--noupx`: Disables UPX compression (avoids decompression delay)
- Module exclusions: Unused libraries (matplotlib, scipy, etc.) are excluded to reduce size

## Data Sources

Tax rates sourced from:
- [IRS Federal Income Tax Brackets 2025](https://www.irs.gov/filing/federal-income-tax-rates-and-brackets)
- [California FTB Tax Rate Schedules](https://www.ftb.ca.gov/forms/2025/2025-540-tax-rate-schedules.pdf)
- [IRS Self-Employment Tax](https://www.irs.gov/businesses/small-businesses-self-employed/self-employment-tax-social-security-and-medicare-taxes)
- [IRS Standard Mileage Rates](https://www.irs.gov/tax-professionals/standard-mileage-rates)
- [California CDTFA Sales Tax Rates](https://cdtfa.ca.gov/taxes-and-fees/rates.aspx)

## Disclaimer

**This application is provided for informational and educational purposes only.**

- This is **not** financial, tax, or legal advice
- Tax laws are complex, change frequently, and vary by jurisdiction
- Calculations may not account for all deductions, credits, or special circumstances applicable to your situation
- The standard mileage rate and other values may be outdated; verify current rates with the IRS
- Always consult a qualified tax professional, CPA, or tax attorney for advice specific to your situation
- The developers make no warranties about the accuracy or completeness of the calculations
- Use of this application is at your own risk

**Do not rely solely on this application for tax planning or filing purposes.**
