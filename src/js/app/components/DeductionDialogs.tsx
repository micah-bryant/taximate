import type { ReactNode } from "react"
import { useState } from "react"
import { Controller, useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { NumericFormat } from "react-number-format"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { formatCurrency } from "@/lib/format"
import type { TaximateApi } from "@/pyodide-runner"

const inputClass =
  "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40"

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-muted-foreground">{label}</span>
      {children}
    </label>
  )
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function MoneyField({ control, name }: { control: any; name: string }) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field }) => (
        <NumericFormat
          className={inputClass}
          value={field.value}
          thousandSeparator
          prefix="$"
          allowNegative={false}
          decimalScale={2}
          onValueChange={(v) => field.onChange(v.floatValue ?? 0)}
        />
      )}
    />
  )
}

// ---------------- Home office ----------------
const homeOfficeSchema = z.object({
  rent: z.number().min(0),
  utilities: z.number().min(0),
  insurance: z.number().min(0),
  officePct: z.number().min(0).max(100),
})
type HomeOfficeValues = z.infer<typeof homeOfficeSchema>

function HomeOfficeDialog({
  api,
  months,
  current,
  onSet,
}: {
  api: TaximateApi
  months: number
  current: number
  onSet: (value: number) => void
}) {
  const [open, setOpen] = useState(false)
  const form = useForm<HomeOfficeValues>({
    resolver: zodResolver(homeOfficeSchema),
    defaultValues: { rent: 0, utilities: 0, insurance: 0, officePct: 0 },
  })

  const submit = (v: HomeOfficeValues) => {
    onSet(api.homeOffice(v.rent, v.utilities, v.insurance, v.officePct / 100, months))
    setOpen(false)
  }

  return (
    <>
      <Button variant="secondary" type="button" onClick={() => setOpen(true)}>
        Home office{current > 0 ? `: ${formatCurrency(current)}` : "…"}
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Home office deduction</DialogTitle>
            <DialogDescription>
              (Rent + utilities + insurance) × office %, over {months} month
              {months === 1 ? "" : "s"}.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={form.handleSubmit(submit)} className="flex flex-col gap-3">
            <Field label="Monthly rent">
              <MoneyField control={form.control} name="rent" />
            </Field>
            <Field label="Monthly utilities">
              <MoneyField control={form.control} name="utilities" />
            </Field>
            <Field label="Monthly insurance">
              <MoneyField control={form.control} name="insurance" />
            </Field>
            <Field label="Office % of home">
              <Controller
                control={form.control}
                name="officePct"
                render={({ field }) => (
                  <NumericFormat
                    className={inputClass}
                    value={field.value}
                    suffix="%"
                    allowNegative={false}
                    decimalScale={1}
                    onValueChange={(v) => field.onChange(v.floatValue ?? 0)}
                  />
                )}
              />
            </Field>
            <DialogFooter>
              <Button type="submit">Apply</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  )
}

// ---------------- Car ----------------
const carSchema = z.object({
  method: z.enum(["standard", "actual"]),
  businessMiles: z.number().min(0),
  totalMiles: z.number().min(0),
  carCost: z.number().min(0),
})
type CarValues = z.infer<typeof carSchema>

function CarDialog({
  api,
  current,
  onSet,
}: {
  api: TaximateApi
  current: number
  onSet: (value: number) => void
}) {
  const [open, setOpen] = useState(false)
  const form = useForm<CarValues>({
    resolver: zodResolver(carSchema),
    defaultValues: { method: "standard", businessMiles: 0, totalMiles: 0, carCost: 0 },
  })
  const method = form.watch("method")

  const submit = (v: CarValues) => {
    const value =
      v.method === "standard"
        ? api.carStandard(v.businessMiles)
        : api.carActual(v.businessMiles, v.totalMiles, v.carCost)
    onSet(value)
    setOpen(false)
  }

  return (
    <>
      <Button variant="secondary" type="button" onClick={() => setOpen(true)}>
        Car{current > 0 ? `: ${formatCurrency(current)}` : "…"}
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Car / vehicle deduction</DialogTitle>
            <DialogDescription>Standard mileage or actual-expense method.</DialogDescription>
          </DialogHeader>
          <form onSubmit={form.handleSubmit(submit)} className="flex flex-col gap-3">
            <Controller
              control={form.control}
              name="method"
              render={({ field }) => (
                <RadioGroup
                  value={field.value}
                  onValueChange={(value) => field.onChange(value)}
                  className="flex gap-4"
                >
                  <label className="flex items-center gap-2 text-sm">
                    <RadioGroupItem value="standard" /> Standard mileage
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <RadioGroupItem value="actual" /> Actual expense
                  </label>
                </RadioGroup>
              )}
            />
            <Field label="Business miles">
              <Controller
                control={form.control}
                name="businessMiles"
                render={({ field }) => (
                  <NumericFormat
                    className={inputClass}
                    value={field.value}
                    thousandSeparator
                    allowNegative={false}
                    onValueChange={(v) => field.onChange(v.floatValue ?? 0)}
                  />
                )}
              />
            </Field>
            {method === "actual" && (
              <>
                <Field label="Total miles (all purposes)">
                  <Controller
                    control={form.control}
                    name="totalMiles"
                    render={({ field }) => (
                      <NumericFormat
                        className={inputClass}
                        value={field.value}
                        thousandSeparator
                        allowNegative={false}
                        onValueChange={(v) => field.onChange(v.floatValue ?? 0)}
                      />
                    )}
                  />
                </Field>
                <Field label="Total car cost">
                  <MoneyField control={form.control} name="carCost" />
                </Field>
              </>
            )}
            <DialogFooter>
              <Button type="submit">Apply</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  )
}

export function Deductions({
  api,
  months,
  homeOffice,
  car,
  onSetHomeOffice,
  onSetCar,
}: {
  api: TaximateApi
  months: number
  homeOffice: number
  car: number
  onSetHomeOffice: (value: number) => void
  onSetCar: (value: number) => void
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <HomeOfficeDialog api={api} months={months} current={homeOffice} onSet={onSetHomeOffice} />
      <CarDialog api={api} current={car} onSet={onSetCar} />
    </div>
  )
}
