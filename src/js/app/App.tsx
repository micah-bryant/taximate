import { useCallback, useEffect, useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { CategoryPanel } from "@/components/CategoryPanel"
import { Deductions } from "@/components/DeductionDialogs"
import { FileLoader } from "@/components/FileLoader"
import { ItemsList } from "@/components/ItemsList"
import { ResultsTable } from "@/components/ResultsTable"
import { initTaximate, type TaximateApi } from "@/pyodide-runner"
import {
  DEFAULT_STATE,
  type CategoryInfo,
  type ComputeResult,
  type StateOption,
  type USState,
} from "@/types"

const STATE_STORAGE_KEY = "taximate.state"
const MIN_MONTHS = 1
const MAX_MONTHS = 12

// Read the persisted state as-is; validated against the engine's list after boot.
function loadPersistedState(): USState {
  try {
    const s = localStorage.getItem(STATE_STORAGE_KEY)
    if (s) return s as USState
  } catch {
    // localStorage may be unavailable (private mode); fall back to the default.
  }
  return DEFAULT_STATE
}

export default function App() {
  const [api, setApi] = useState<TaximateApi | null>(null)
  const [status, setStatus] = useState<"booting" | "ready" | "error">("booting")
  const [progress, setProgress] = useState("Starting…")
  const [bootError, setBootError] = useState<string | null>(null)
  const [version, setVersion] = useState("")

  const [categories, setCategories] = useState<CategoryInfo[]>([])
  const [items, setItems] = useState<string[]>([])
  const [fileInfo, setFileInfo] = useState<{ count: number; files: number } | null>(null)
  const [assignments, setAssignments] = useState<Record<string, string>>({})
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [category, setCategory] = useState("")
  const [homeOffice, setHomeOffice] = useState(0)
  const [car, setCar] = useState(0)
  const [months, setMonths] = useState(MAX_MONTHS)
  const [stateOptions, setStateOptions] = useState<StateOption[]>([])
  const [usState, setUsState] = useState<USState>(loadPersistedState)
  const [result, setResult] = useState<ComputeResult | null>(null)

  useEffect(() => {
    let cancelled = false
    initTaximate(setProgress)
      .then((a) => {
        if (cancelled) return
        setApi(a)
        const options = a.supportedStates()
        setStateOptions(options)
        // Drop a persisted state the engine no longer supports.
        setUsState((prev) => (options.some((o) => o.value === prev) ? prev : DEFAULT_STATE))
        setStatus("ready")
      })
      .catch((e: unknown) => {
        if (cancelled) return
        console.error(e)
        setBootError(String(e))
        setStatus("error")
      })
    fetch(`${import.meta.env.BASE_URL}manifest.json`)
      .then((r) => r.json())
      .then((m) => {
        if (!cancelled) setVersion(m.version)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  // Reload categories on boot/state change (descriptions embed the state's sales-tax rate).
  useEffect(() => {
    if (!api) return
    try {
      setCategories(api.categories(usState))
    } catch (e) {
      console.error(e)
      toast.error(`Could not load categories: ${e}`)
    }
  }, [api, usState])

  // Persist the chosen state so it survives reloads.
  useEffect(() => {
    try {
      localStorage.setItem(STATE_STORAGE_KEY, usState)
    } catch {
      // ignore unavailable localStorage
    }
  }, [usState])

  const handleLoad = useCallback(
    (files: [string, string][]) => {
      if (!api) return
      try {
        const res = api.loadFiles(files)
        setItems(res.items)
        setFileInfo({ count: res.count, files: res.files })
        setResult(null)
        toast.success(
          `Loaded ${res.files} file(s), ${res.count} transactions, ${res.items.length} items.`,
        )
      } catch (e) {
        toast.error(`Could not load CSVs: ${e}`)
      }
    },
    [api],
  )

  const toggleSelect = useCallback((item: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(item)) next.delete(item)
      else next.add(item)
      return next
    })
  }, [])

  const assign = useCallback(() => {
    if (!category) return
    setAssignments((prev) => {
      const next = { ...prev }
      for (const item of selected) next[item] = category
      return next
    })
    setSelected(new Set())
  }, [category, selected])

  const remove = useCallback(() => {
    setAssignments((prev) => {
      const next = { ...prev }
      for (const item of selected) delete next[item]
      return next
    })
    setSelected(new Set())
  }, [selected])

  const calculate = useCallback(() => {
    if (!api) return
    if (Object.keys(assignments).length === 0) {
      toast.error("Assign at least one item to a category first.")
      return
    }
    try {
      setResult(api.compute(assignments, homeOffice, car, months, usState))
    } catch (e) {
      toast.error(`Calculation failed: ${e}`)
    }
  }, [api, assignments, homeOffice, car, months, usState])

  if (status === "booting") return <LoadingOverlay progress={progress} />
  if (status === "error") {
    return (
      <div className="mx-auto max-w-lg p-8 text-center">
        <h1 className="mb-2 text-xl font-semibold text-destructive">
          Failed to load the tax engine
        </h1>
        <p className="text-sm text-muted-foreground">{bootError}</p>
      </div>
    )
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8 p-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold">Taximate</h1>
        <p className="text-sm text-muted-foreground">
          Estimate self-employment taxes from your EveryDollar exports. Everything runs in your
          browser; your CSVs never leave your device.
        </p>
      </header>

      <div
        role="note"
        className="rounded-md border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-800 dark:text-amber-300"
      >
        <strong>Estimates only, not tax advice.</strong> Taximate approximates your
        self-employment taxes to help you plan. Have a certified tax professional verify every
        figure before you file.
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold text-primary">1 · Load transactions</h2>
        <FileLoader onLoad={handleLoad} disabled={!api} />
        {fileInfo && (
          <p className="text-sm text-muted-foreground" data-testid="file-info">
            {fileInfo.files} file(s), {fileInfo.count} transactions, {items.length} unique items.
          </p>
        )}
      </section>

      {items.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold text-primary">2 · Assign items to categories</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <ItemsList
              items={items}
              assignments={assignments}
              selected={selected}
              onToggle={toggleSelect}
            />
            <CategoryPanel
              categories={categories}
              category={category}
              selectedCount={selected.size}
              onCategoryChange={setCategory}
              onAssign={assign}
              onRemove={remove}
            />
          </div>
        </section>
      )}

      {items.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold text-primary">3 · Calculate</h2>
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 text-sm">
              State:
              <Select
                value={usState}
                onValueChange={(v) => {
                  setUsState(v ?? DEFAULT_STATE)
                  setResult(null)
                }}
              >
                <SelectTrigger className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {stateOptions.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </label>
            <label className="flex items-center gap-2 text-sm">
              Months of data:
              <input
                type="number"
                min={MIN_MONTHS}
                max={MAX_MONTHS}
                value={months}
                onChange={(e) =>
                  setMonths(
                    Math.min(MAX_MONTHS, Math.max(MIN_MONTHS, Number(e.target.value) || MIN_MONTHS)),
                  )
                }
                className="h-9 w-16 rounded-md border border-input bg-transparent px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
              />
            </label>
            {api && (
              <Deductions
                api={api}
                months={months}
                homeOffice={homeOffice}
                car={car}
                onSetHomeOffice={setHomeOffice}
                onSetCar={setCar}
              />
            )}
            <Button onClick={calculate}>Calculate taxes</Button>
          </div>
        </section>
      )}

      {result && (
        <section className="flex flex-col gap-3" data-testid="results">
          <p className="text-xs text-muted-foreground">
            Estimates, not tax advice. Verify with a certified tax professional before filing.
          </p>
          <ResultsTable result={result} />
        </section>
      )}

      <footer className="mt-4 border-t border-border pt-4 text-xs text-muted-foreground">
        Taximate {version && `v${version}`} · Estimates only, not tax advice. Verify with a
        certified tax professional before filing.
      </footer>
    </div>
  )
}

function LoadingOverlay({ progress }: { progress: string }) {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4 p-8 text-center">
      <div className="h-10 w-10 animate-spin rounded-full border-2 border-muted border-t-primary" />
      <div>
        <p className="font-medium">Loading Taximate</p>
        <p className="text-sm text-muted-foreground" data-testid="progress">
          {progress}
        </p>
        <p className="mt-2 text-xs text-muted-foreground">
          First load downloads the Python engine (cached after).
        </p>
      </div>
    </div>
  )
}
