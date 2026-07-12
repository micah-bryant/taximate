import { useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"

interface FileLoaderProps {
  disabled?: boolean
  onLoad: (files: [string, string][]) => void
}

/** Step 1 — drag-drop / browse EveryDollar CSV exports; reads them as text. */
export function FileLoader({ disabled, onLoad }: FileLoaderProps) {
  const onDrop = useCallback(
    async (accepted: File[]) => {
      const csvs = accepted.filter((f) => f.name.toLowerCase().endsWith(".csv"))
      if (csvs.length === 0) {
        toast.error("No CSV files found in the drop.")
        return
      }
      try {
        const pairs = await Promise.all(
          csvs.map(async (f): Promise<[string, string]> => [f.name, await f.text()]),
        )
        onLoad(pairs)
      } catch {
        toast.error("Could not read the selected files.")
      }
    },
    [onLoad],
  )

  const { getRootProps, getInputProps, open, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    noClick: true,
    disabled,
  })

  return (
    <div
      {...getRootProps()}
      className={`flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
        isDragActive ? "border-primary bg-primary/5" : "border-border"
      } ${disabled ? "opacity-50" : ""}`}
    >
      <input {...getInputProps()} />
      <p className="text-muted-foreground">
        {isDragActive ? "Drop the CSV files…" : "Drag & drop EveryDollar CSV exports here"}
      </p>
      <Button type="button" variant="secondary" onClick={open} disabled={disabled}>
        Browse files
      </Button>
    </div>
  )
}
