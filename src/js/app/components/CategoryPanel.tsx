import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { CategoryInfo } from "@/types"

interface CategoryPanelProps {
  categories: CategoryInfo[]
  category: string
  selectedCount: number
  onCategoryChange: (category: string) => void
  onAssign: () => void
  onRemove: () => void
}

/** Step 2 (right) — pick a category and assign/remove the selected items. */
export function CategoryPanel({
  categories,
  category,
  selectedCount,
  onCategoryChange,
  onAssign,
  onRemove,
}: CategoryPanelProps) {
  const description = categories.find((c) => c.name === category)?.description

  return (
    <div className="flex flex-col gap-3">
      <Select value={category} onValueChange={(v) => onCategoryChange(v ?? "")}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Choose a category" />
        </SelectTrigger>
        <SelectContent>
          {categories.map((c) => (
            <SelectItem key={c.name} value={c.name}>
              {c.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {description && <p className="text-sm text-muted-foreground">{description}</p>}

      <div className="flex gap-2">
        <Button onClick={onAssign} disabled={!category || selectedCount === 0}>
          Assign {selectedCount > 0 ? `(${selectedCount})` : ""}
        </Button>
        <Button variant="secondary" onClick={onRemove} disabled={selectedCount === 0}>
          Remove
        </Button>
      </div>
    </div>
  )
}
