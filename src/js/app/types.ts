// Hand-written mirrors of the Python core's JSON payload; keep in sync with the
// taximate.core dataclasses.

/** One row of the tax summary table, mirroring core `DisplayRow` (snake_case). */
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

/** US state whose tax rules the engine applies (keys into state_tax_rules.csv). */
export type USState = "california" | "massachusetts"

/** Default state when none is persisted or selected. */
export const DEFAULT_STATE: USState = "massachusetts"

/** One selectable state for the picker, from the engine's `supported_states()`. */
export interface StateOption {
  value: USState
  label: string
}
