# Taximate

A GUI app for self-employed individuals that imports [EveryDollar](https://www.everydollar.com/) CSV transaction exports and calculates estimated taxes.

> **Disclaimer:** For informational purposes only — not financial, tax, or legal advice. Always consult a qualified tax professional.

## How it works

Load your EveryDollar CSVs, assign each transaction item to an income/expense category, then click **Calculate Taxes**. Results are shown for both the loaded period and projected annually.

### Income categories

| Category | Description |
|---|---|
| Freelance (Tax Already Paid) | Income with taxes already withheld (e.g. W-2 gig work) |
| Revenue (Sales Tax Bundled) | Revenue with sales tax included in the price |
| Revenue (Sales Tax Applied) | Revenue where sales tax was collected separately |
| Business Expenses | Deductible business expenses |

### Deductions

- **Home office** — `(Rent + Utilities + Insurance) × Office % × Months`
- **Car (standard mileage)** — Business miles × $0.70/mile
- **Car (actual expenses)** — `(Business miles ÷ Total miles) × Cost of car`

### Calculation flow

1. **Sales tax** extracted from bundled revenue: `Bundled / (1 + rate) × rate`
2. **Business profit** = Sales taxable + Revenue applied − Expenses − Deductions
3. **SE tax** = Business profit × 92.35% × (12.4% SS + 2.9% Medicare), SS portion capped at $176,100
4. **Taxable income** = Business profit − (SE tax × 50%)
5. **Federal / CA state income tax** via progressive brackets
6. **Take home** = Total profit − Total income tax

Tax rates are loaded from CSV files in `tax_rates/` (2025 federal, 2024 California, 7.75% San Diego sales tax) and can be edited directly.

## Usage

```bash
uv sync       # install dependencies
make run      # launch the app
```

On Linux/WSL, install Qt system libraries first:

```bash
sudo apt install -y libegl1 libxkbcommon0 libxcb-cursor0
```

## Development

```bash
make test     # run pytest
make check    # ruff + mypy
make format   # auto-format
```

## Building executables

```bash
make build-mac-intel    # macOS Intel
make build-mac-arm64    # macOS Apple Silicon
make build-windows      # Windows
```

Releases are also built automatically via GitHub Actions on version tags.

## Project structure

```
src/taximate/
├── core/
│   ├── data_loader.py      # CSV loading and parsing
│   └── tax_calculator.py   # Tax calculation engine
└── gui/
    └── app.py              # PySide6 GUI
tests/
tax_rates/                  # Editable tax rate CSVs
data/                       # Sample transaction CSVs
main.py                     # Entry point
```
