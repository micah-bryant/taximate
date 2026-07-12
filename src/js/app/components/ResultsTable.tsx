import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatCurrency } from "@/lib/format"
import type { ComputeResult } from "@/types"

/** Step 3 (results): renders the core's `display_rows()` for period + annual. */
export function ResultsTable({ result }: { result: ComputeResult }) {
  return (
    <div className="flex flex-col gap-3">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead />
            <TableHead className="text-right">Period ({result.months} mo)</TableHead>
            <TableHead className="text-right">Annual (12 mo)</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {result.period.map((p, i) => {
            const a = result.annual[i]
            if (p.is_section_header) {
              return (
                <TableRow key={i} className="bg-muted/40 hover:bg-muted/40">
                  <TableCell colSpan={3} className="font-semibold text-primary">
                    {p.label}
                  </TableCell>
                </TableRow>
              )
            }
            return (
              <TableRow key={i}>
                <TableCell className={p.bold ? "font-bold" : ""}>{p.label}</TableCell>
                <TableCell
                  className={`text-right tabular-nums ${p.bold ? "font-bold" : ""}`}
                >
                  {formatCurrency(p.value, p.negate)}
                </TableCell>
                <TableCell
                  className={`text-right tabular-nums ${a.bold ? "font-bold" : ""}`}
                >
                  {formatCurrency(a.value, a.negate)}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>

      {result.uncategorized.length > 0 && (
        <p className="text-sm text-muted-foreground">
          Uncategorized ({result.uncategorized.length}):{" "}
          {result.uncategorized.slice(0, 6).join(", ")}
          {result.uncategorized.length > 6
            ? `, +${result.uncategorized.length - 6} more`
            : ""}
        </p>
      )}
    </div>
  )
}
