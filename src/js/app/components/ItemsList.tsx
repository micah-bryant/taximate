interface ItemsListProps {
  items: string[]
  assignments: Record<string, string>
  selected: Set<string>
  onToggle: (item: string) => void
}

/** Step 2 (left) — the transaction items, multi-select, with [category] tags. */
export function ItemsList({ items, assignments, selected, onToggle }: ItemsListProps) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">Load CSV files to see transaction items.</p>
  }
  return (
    <ul className="max-h-96 divide-y divide-border overflow-y-auto rounded-md border border-border">
      {items.map((item) => {
        const category = assignments[item]
        const isSelected = selected.has(item)
        return (
          <li key={item}>
            <button
              type="button"
              onClick={() => onToggle(item)}
              className={`flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm transition-colors ${
                isSelected ? "bg-primary/15" : "hover:bg-accent"
              }`}
            >
              <span className="truncate">{item}</span>
              {category && (
                <span className="shrink-0 rounded bg-secondary px-1.5 py-0.5 text-xs text-muted-foreground">
                  {category}
                </span>
              )}
            </button>
          </li>
        )
      })}
    </ul>
  )
}
