// Hand-written mirrors of the Python core's JSON payload. Kept in sync with the
// dataclasses in taximate.core by the drift-guard test (see the drift-guard
// test, which type-checks the golden fixture against these interfaces).

/** One row of the tax summary table — mirrors core `DisplayRow` (snake_case). */
export interface DisplayRow {
  label: string
  value: number
  section: string
  bold: boolean
  negate: boolean
  is_section_header: boolean
}

/** Result of loading CSV files. */
export interface LoadResult {
  items: string[]
  count: number
  files: number
}

/** Result of a full tax computation. */
export interface ComputeResult {
  period: DisplayRow[]
  annual: DisplayRow[]
  uncategorized: string[]
  months: number
}

/** An income/expense category the user assigns items to. */
export interface CategoryInfo {
  name: string
  description: string
}
