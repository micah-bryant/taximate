const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

/** Format a dollar value, optionally negated (for expenses/deductions). */
export function formatCurrency(value: number, negate = false): string {
  return currency.format(negate ? -value : value)
}
