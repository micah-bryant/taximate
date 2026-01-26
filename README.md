# Taximate

A Python GUI application that imports transaction data from EveryDollar CSV exports and calculates self-employment taxes including sales tax, sole proprietor tax, federal and state income taxes.

## Features

- **Drag-and-drop file loading** - Drop multiple CSV files directly onto the app (macOS)
- **Multi-file support** - Load and combine multiple CSV transaction files at once
- **File browser** - Select CSV files from anywhere on your system
- **Transaction categorization** - GUI for categorizing transactions into income/expense types
- **Progressive tax brackets** - Federal and California state income tax calculations
- **Self-employment tax** - Social Security and Medicare with wage base cap
- **Configurable tax rates** - Tax rates stored in editable CSV files
- **Annual projections** - Extrapolate partial year data to annual estimates
- **Take-home calculation** - Shows total take-home pay and gross revenue

## Installation

```bash
uv sync
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
   - **Drag and drop** multiple CSV files onto the drop zone (macOS)
   - **Click "Browse Files"** to select files from anywhere on your system
   - Files can be loaded incrementally - new files are added to existing data

4. Select items in the left panel and assign them to income/expense categories
5. Set the number of months your data covers (for annual projections)
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
    └── gui.py           # Tkinter GUI with drag-and-drop support
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
- [California CDTFA Sales Tax Rates](https://cdtfa.ca.gov/taxes-and-fees/rates.aspx)
