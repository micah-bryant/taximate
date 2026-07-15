// Loads Pyodide, installs the taximate wheel (which bundles the rate tables), and
// exposes a small typed calc API to React. All tax math runs in Python.
//
// Bridge: JSON-string in / JSON-string out for structured data; scalars pass through.

import type { CategoryInfo, ComputeResult, LoadResult, StateOption, USState } from "./types"

// Pinned Pyodide: Python 3.13, bundles pydantic 2.10.6 + micropip (verified).
const PYODIDE_VERSION = "0.28.2"
const PYODIDE_INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`

// Python facade run inside Pyodide: holds the parsed rows and exposes JSON I/O.
const FACADE = String.raw`
import json
from dataclasses import asdict
from taximate.core.data_loader import load_csvs_from_strings, unique_items
from taximate.core.tax_calculator import DEFAULT_STATE, TaxCalculator, supported_states as _supported_states
from taximate.core import deductions as _ded

_rows = []

def supported_states():
    return json.dumps(_supported_states())

def load_files(files_json):
    global _rows
    pairs = [(n, t) for n, t in json.loads(files_json)]
    _rows = load_csvs_from_strings(pairs)
    return json.dumps({
        "items": unique_items(_rows),
        "count": len(_rows),
        "files": len({r.source_file for r in _rows}),
    })

def categories(state=DEFAULT_STATE):
    calc = TaxCalculator(state=state)
    return json.dumps([
        {"name": c.name, "description": c.description}
        for c in calc.categories.values()
    ])

def compute(assignments_json, home_office, car, months, state=DEFAULT_STATE):
    assignments = json.loads(assignments_json)
    calc = TaxCalculator(state=state)
    for item, cat in assignments.items():
        if cat:
            calc.assign_item_to_category(item, cat)
    calc.home_office_deduction = float(home_office)
    calc.car_deduction = float(car)
    summary = calc.generate_summary(_rows, int(months))
    return json.dumps({
        "period": [asdict(r) for r in summary.period_taxes.display_rows()],
        "annual": [asdict(r) for r in summary.annual_taxes.display_rows()],
        "uncategorized": calc.get_uncategorized_items(_rows),
        "months": int(months),
    })

def calc_home_office(rent, utilities, insurance, office_pct, months):
    return _ded.home_office_deduction(
        float(rent), float(utilities), float(insurance), float(office_pct), int(months)
    )

def calc_home_office_simplified(square_feet, months):
    return _ded.home_office_deduction_simplified(float(square_feet), int(months))

def calc_car_standard(miles):
    return _ded.car_standard_mileage_deduction(float(miles))

def calc_car_actual(business_miles, total_miles, car_cost):
    return _ded.car_actual_expense_deduction(
        float(business_miles), float(total_miles), float(car_cost)
    )
`

export interface TaximateApi {
  loadFiles(files: [string, string][]): LoadResult
  supportedStates(): StateOption[]
  categories(state: USState): CategoryInfo[]
  compute(
    assignments: Record<string, string>,
    homeOffice: number,
    car: number,
    months: number,
    state: USState,
  ): ComputeResult
  homeOffice(
    rent: number,
    utilities: number,
    insurance: number,
    officePct: number,
    months: number,
  ): number
  homeOfficeSimplified(squareFeet: number, months: number): number
  carStandard(miles: number): number
  carActual(businessMiles: number, totalMiles: number, carCost: number): number
}

async function boot(
  onProgress: (msg: string) => void,
  baseUrl: string,
): Promise<TaximateApi> {
  onProgress("Downloading tax engine…")
  // Load Pyodide from the pinned CDN, kept out of the app bundle.
  const mod = await import(/* @vite-ignore */ `${PYODIDE_INDEX_URL}pyodide.mjs`)
  const pyodide = await mod.loadPyodide({ indexURL: PYODIDE_INDEX_URL })

  onProgress("Loading Python packages…")
  await pyodide.loadPackage(["micropip", "pydantic"])

  onProgress("Installing tax engine…")
  const manifest = await (await fetch(`${baseUrl}manifest.json`)).json()
  const micropip = pyodide.pyimport("micropip")
  const wheelUrl = new URL(`${baseUrl}${manifest.wheel}`, location.origin).href
  await micropip.install.callKwargs(wheelUrl, { deps: false })

  onProgress("Starting…")
  pyodide.runPython(FACADE)
  const g = pyodide.globals
  const loadFilesPy = g.get("load_files")
  const supportedStatesPy = g.get("supported_states")
  const categoriesPy = g.get("categories")
  const computePy = g.get("compute")
  const hoPy = g.get("calc_home_office")
  const hosPy = g.get("calc_home_office_simplified")
  const csPy = g.get("calc_car_standard")
  const caPy = g.get("calc_car_actual")

  const api: TaximateApi = {
    loadFiles: (files) => JSON.parse(loadFilesPy(JSON.stringify(files))),
    supportedStates: () => JSON.parse(supportedStatesPy()),
    categories: (state) => JSON.parse(categoriesPy(state)),
    compute: (a, ho, car, m, state) =>
      JSON.parse(computePy(JSON.stringify(a), ho, car, m, state)),
    homeOffice: (r, u, i, p, m) => hoPy(r, u, i, p, m),
    homeOfficeSimplified: (sqft, m) => hosPy(sqft, m),
    carStandard: (mi) => csPy(mi),
    carActual: (b, t, c) => caPy(b, t, c),
  }
  // Expose the API for programmatic/testing access (harmless debug handle on a public app).
  ;(globalThis as unknown as { __taximateApi?: TaximateApi }).__taximateApi = api
  return api
}

let bootPromise: Promise<TaximateApi> | null = null

/** Initialise Pyodide + the tax engine once (idempotent under React StrictMode). */
export function initTaximate(
  onProgress: (msg: string) => void,
  baseUrl: string = import.meta.env.BASE_URL,
): Promise<TaximateApi> {
  bootPromise ??= boot(onProgress, baseUrl)
  return bootPromise
}
