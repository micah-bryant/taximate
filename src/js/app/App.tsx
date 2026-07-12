import { useCallback, useEffect, useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { CategoryPanel } from "@/components/CategoryPanel"
import { Deductions } from "@/components/DeductionDialogs"
import { FileLoader } from "@/components/FileLoader"
import { ItemsList } from "@/components/ItemsList"
import { ResultsTable } from "@/components/ResultsTable"
import { initTaximate, type TaximateApi } from "@/pyodide-runner"
import type { CategoryInfo, ComputeResult } from "@/types"

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
  const [months, setMonths] = useState(12)
  const [result, setResult] = useState<ComputeResult | null>(null)

  useEffect(() => {
    let cancelled = false
    initTaximate(setProgress)
      .then((a) => {
        if (cancelled) return
        setApi(a)
        setCategories(a.categories())
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
      setResult(api.compute(assignments, homeOffice, car, months))
    } catch (e) {
      toast.error(`Calculation failed: ${e}`)
    }
  }, [api, assignments, homeOffice, car, months])

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
          browser — your CSVs never leave your device.
        </p>
      </header>

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
              Months of data:
              <input
                type="number"
                min={1}
                max={12}
                value={months}
                onChange={(e) =>
                  setMonths(Math.min(12, Math.max(1, Number(e.target.value) || 1)))
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
          <ResultsTable result={result} />
        </section>
      )}

      <footer className="mt-4 border-t border-border pt-4 text-xs text-muted-foreground">
        Taximate {version && `v${version}`} · Informational only — not tax advice.
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
