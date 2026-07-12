# Taximate

Estimate self-employment taxes from your [EveryDollar](https://www.everydollar.com/) CSV exports. [**Live app**](https://micah-bryant.github.io/taximate/), running entirely in your browser.

> ⚠️ **Estimates only, not tax advice.** Taximate approximates your taxes to help you plan. Have a certified tax professional verify every figure before you file.

## How it works

Load your EveryDollar CSVs, assign each item to a category, then **Calculate**. Results cover the loaded period and an annualized projection.

- **Categories:** Freelance (Tax Already Paid), Revenue (Sales Tax Bundled), Revenue (Sales Tax Applied), Business Expenses.
- **Deductions:** home office `(Rent + Utilities + Insurance) × Office% × Months`; car standard-mileage `miles × $0.70`; car actual-expense `(Business ÷ Total miles) × Car cost`.
- **Calc flow:** extract bundled sales tax, then business profit (`sales-taxable + applied revenue - expenses - deductions`), SE tax (92.35% × 15.3%, SS capped at $176,100), taxable income (`profit - ½ SE tax`), federal + CA brackets, take-home.

Rates are data, not code: `src/python/taximate/tax_rates/*.csv` (2025 federal, 2024 CA, 7.75% San Diego), bundled into the wheel. Edit the CSVs for new years.

## Privacy

No backend; nothing is uploaded. A `<meta>` CSP locks `connect-src` to this origin plus the Pyodide CDN, so your data physically can't be sent elsewhere (guarded by `taximate-parity/`'s `csp.spec.ts`).

## Architecture

A UI-free Python core (`src/python/taximate/core/`, stdlib + pydantic) builds to a wheel via `uv build --wheel` and runs client-side via **Pyodide**. The React/TS/Vite frontend (`src/js/`) loads the wheel and renders `display_rows()`. All math stays in Python, auditable in one language.

## Develop

```bash
# Python core (needs uv)
make install | test | check | format | build      # check = ruff + mypy (CI gate); build = wheel

# Web app (needs Node >=22): stage the wheel, then run Vite
make build && cp dist/*.whl src/js/public/
WHEEL=$(basename dist/*.whl); V=$(grep -m1 '^version' pyproject.toml | cut -d'"' -f2)
printf '{"wheel":"%s","version":"%s"}\n' "$WHEEL" "$V" > src/js/public/manifest.json
npm --prefix src/js install && npm --prefix src/js run dev     # or: run build
```

## Structure

```
src/python/taximate/   core/ (engine) + tax_rates/ (bundled CSVs)
src/python/tests/      pytest + fixtures/
src/js/app/            React app (pyodide-runner.ts, components/)
pyproject.toml         deps + uv_build + ruff/mypy/pytest config
```

## Deploy

`.github/workflows/deploy.yml` on a `v*` tag: pytest gate, wheel, Vite build, GitHub Pages at `micah-bryant.github.io/taximate/`. Bump `version` in `pyproject.toml` first.
