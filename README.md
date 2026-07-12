# Taximate

A web app for self-employed individuals that imports [EveryDollar](https://www.everydollar.com/) CSV transaction exports and calculates estimated taxes — entirely in your browser.

> **Disclaimer:** For informational purposes only — not financial, tax, or legal advice. Always consult a qualified tax professional.

**Live app:** <https://micah-bryant.github.io/taximate/>

## How it works

Load your EveryDollar CSVs, assign each transaction item to an income/expense category, then click **Calculate Taxes**. Results are shown for both the loaded period and projected annually.

The tax engine is the same audited **Python** core throughout — it runs client-side via [Pyodide](https://pyodide.org/) (CPython compiled to WebAssembly). **Your CSVs never leave your device**; there is no server.

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

Tax rates are data, not code: they load from CSV files in `src/python/taximate/tax_rates/` (2025 federal, 2024 California, 7.75% San Diego sales tax) and ship inside the Python wheel. Update the CSVs for new tax years/jurisdictions rather than editing the formulas.

## Architecture

Two halves in one repo, both built by the same CI:

- **Python core** (`src/python/taximate/core/`) — the calculation engine and its data model, with **zero UI dependencies** so it stays unit-testable. Uses only the standard library plus `pydantic` (which validates the untrusted uploaded CSV rows at the input boundary). `uv build --wheel` produces a pure-Python wheel that bundles the rate CSVs.
- **React/TypeScript frontend** (`src/js/`) — Vite app that loads Pyodide, installs the wheel, and drives the three-step UI (load → assign → calculate). All tax math happens in the Python core; the frontend only renders it.

The same numbers are guaranteed across desktop-baseline, refactored core, and browser by an out-of-band golden characterization test (see the sibling `taximate-parity/` project).

## Privacy & security

Your uploaded CSVs are read and processed **entirely in your browser** — there is no backend and nothing is uploaded. This is enforced, not just promised: the app ships a [Content-Security-Policy](src/js/index.html) whose `connect-src` allows only this origin (its own wheel + manifest) and the pinned Pyodide CDN, so the page physically cannot send your data anywhere else. (`wasm-unsafe-eval` runs Pyodide's WebAssembly; `unsafe-eval` is included only for Safari, which lacks `wasm-unsafe-eval` support.) The `taximate-parity/` suite includes a browser test asserting the policy blocks nothing the app actually needs.

## Development

### Python core

Requires [`uv`](https://docs.astral.sh/uv/).

```bash
make install   # uv sync
make test      # pytest
make check     # ruff check + ruff format --check + mypy (the CI gate)
make format    # ruff auto-fix + format
make build     # build the pure-Python wheel (dist/)
```

### Web app

Requires Node ≥ 22. The frontend needs the wheel and a manifest staged into `src/js/public/` so Pyodide can install the core (the tax rates ride along inside the wheel):

```bash
# 1. build + stage the wheel and manifest
make build
cp dist/*.whl src/js/public/
WHEEL=$(basename "$(ls dist/*.whl)")
VERSION=$(grep -m1 '^version' pyproject.toml | cut -d'"' -f2)
printf '{"wheel":"%s","version":"%s"}\n' "$WHEEL" "$VERSION" > src/js/public/manifest.json

# 2. run / build the frontend
npm --prefix src/js install
npm --prefix src/js run dev      # local dev server
npm --prefix src/js run build    # production build → src/js/dist/
```

## Project structure

```
src/
├── python/
│   ├── taximate/
│   │   ├── core/               # tax engine (UI-free): data_loader, tax_calculator, deductions
│   │   └── tax_rates/          # editable rate CSVs, bundled into the wheel
│   └── tests/                  # pytest + fixtures/ (sample CSVs)
└── js/                         # React/TS/Vite frontend
    ├── app/                    # source: main.tsx, App.tsx, pyodide-runner.ts, components/
    └── public/                 # CI-staged wheel + manifest (gitignored)
pyproject.toml                  # uv_build backend, module-root = src/python
Makefile
```

## Deploy

`.github/workflows/deploy.yml` runs the Python parity gate, builds the wheel, stages it into the frontend, builds the Vite app, and publishes to this repo's own GitHub Pages at `micah-bryant.github.io/taximate/`. It triggers on `v*` tags (bump `version` in `pyproject.toml` before tagging) and on manual `workflow_dispatch`.
