"""Tkinter GUI for Taximate tax calculation application.

This module provides the main graphical user interface for Taximate, featuring:
- Drag-and-drop CSV file loading (when tkinterdnd2 is available)
- Multi-file selection via file browser dialog
- Transaction item categorization with visual feedback
- Real-time tax calculation and summary display
- Annual projection based on partial year data

The GUI uses a three-panel layout:
- Left: Transaction items list with category indicators
- Center: Category assignment controls and category contents
- Right: Tax calculation summary and results
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

import pandas as pd

# Try to import tkinterdnd2 for drag-and-drop support (optional)
# Falls back gracefully to file browser only if unavailable
try:
    from tkinterdnd2 import DND_FILES
except (ImportError, RuntimeError):
    DND_FILES = None

from .data_loader import get_unique_values, load_csvs_from_paths
from .tax_calculator import TaxCalculator, TaxResults


class TaximateGUI:
    """Main GUI window for the Taximate application.

    Provides a graphical interface for loading CSV transaction files,
    categorizing items into income/expense types, and calculating
    self-employment taxes with annual projections.

    Attributes:
        root: The Tkinter root window.
        df: DataFrame containing loaded transaction data.
        calculator: TaxCalculator instance for tax computations.
        loaded_files: List of file paths that have been loaded.
        has_dnd: Whether drag-and-drop functionality is available.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Taximate - Tax Calculator")
        self.root.geometry("1200x750")

        self.df: pd.DataFrame | None = None
        self.calculator = TaxCalculator()
        self.loaded_files: list[str] = []

        # Check if drag-and-drop is available (root must be TkinterDnD.Tk)
        self.has_dnd = DND_FILES is not None and hasattr(root, "TkdndVersion")

        self._create_widgets()
        self._on_category_selected()  # Show description for default category

    def _create_widgets(self) -> None:
        """Create all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Drop zone and load buttons
        load_frame = ttk.Frame(main_frame)
        load_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        # Drop zone - with optional drag-and-drop support
        drop_text = (
            "Drop CSV files here\nor click Browse" if self.has_dnd else "Click to select CSV files"
        )
        self.drop_zone = tk.Label(
            load_frame,
            text=drop_text,
            relief="groove",
            width=30,
            height=2,
            bg="#f0f0f0",
            cursor="hand2",
        )
        self.drop_zone.pack(side="left", padx=(0, 10))
        self.drop_zone.bind("<Button-1>", lambda e: self._browse_files())

        # Register drag-and-drop if available
        if self.has_dnd and DND_FILES is not None:
            drop_zone_dnd: Any = self.drop_zone
            drop_zone_dnd.drop_target_register(DND_FILES)
            drop_zone_dnd.dnd_bind("<<Drop>>", self._on_drop)
            drop_zone_dnd.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            drop_zone_dnd.dnd_bind("<<DragLeave>>", self._on_drag_leave)

        self.browse_btn = ttk.Button(load_frame, text="Browse Files", command=self._browse_files)
        self.browse_btn.pack(side="left", padx=(0, 10))

        self.clear_btn = ttk.Button(load_frame, text="Clear Data", command=self._clear_data)
        self.clear_btn.pack(side="left", padx=(0, 10))

        self.status_label = ttk.Label(load_frame, text="No data loaded")
        self.status_label.pack(side="left", padx=(10, 0))

        # Left panel - Items list
        left_frame = ttk.LabelFrame(main_frame, text="Transaction Items", padding="5")
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))

        self.items_listbox = tk.Listbox(left_frame, selectmode="extended", width=45, height=25)
        self.items_listbox.pack(side="left", fill="both", expand=True)

        items_scrollbar = ttk.Scrollbar(
            left_frame, orient="vertical", command=self.items_listbox.yview
        )
        items_scrollbar.pack(side="right", fill="y")
        self.items_listbox.config(yscrollcommand=items_scrollbar.set)

        # Middle panel - Category assignment
        middle_frame = ttk.Frame(main_frame)
        middle_frame.grid(row=1, column=1, sticky="nsew", padx=5)
        middle_frame.rowconfigure(1, weight=1)
        middle_frame.columnconfigure(0, weight=1)

        # Category selection
        cat_frame = ttk.LabelFrame(middle_frame, text="Assign to Category", padding="5")
        cat_frame.grid(row=0, column=0, sticky="new")

        self.category_combo = ttk.Combobox(cat_frame, state="readonly", width=35)
        self.category_combo["values"] = list(self.calculator.categories.keys())
        if self.calculator.categories:
            self.category_combo.current(0)  # Select first category by default
        self.category_combo.pack(pady=5)

        # Category description label
        self.category_desc_label = ttk.Label(cat_frame, text="", wraplength=250, foreground="gray")
        self.category_desc_label.pack(pady=(0, 5))

        self.assign_btn = ttk.Button(
            cat_frame, text="Assign Selected Items", command=self._assign_items
        )
        self.assign_btn.pack(pady=5)

        self.unassign_btn = ttk.Button(
            cat_frame, text="Remove from Category", command=self._unassign_items
        )
        self.unassign_btn.pack(pady=5)

        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_selected)

        # Category contents
        contents_frame = ttk.LabelFrame(middle_frame, text="Category Contents", padding="5")
        contents_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        self.category_contents = tk.Text(contents_frame, width=40, height=12, state="disabled")
        self.category_contents.pack(fill="both", expand=True)

        # Right panel - Results
        right_frame = ttk.LabelFrame(main_frame, text="Tax Summary", padding="5")
        right_frame.grid(row=1, column=2, sticky="nsew", padx=(5, 0))

        self.results_text = tk.Text(right_frame, width=52, height=25, state="disabled")
        self.results_text.pack(fill="both", expand=True)

        # Months input and calculate button frame
        calc_frame = ttk.Frame(right_frame)
        calc_frame.pack(pady=(10, 0), fill="x")

        ttk.Label(calc_frame, text="Months of data:").pack(side="left")
        self.months_var = tk.StringVar(value="12")
        self.months_spinbox = ttk.Spinbox(
            calc_frame,
            from_=1,
            to=12,
            width=3,
            textvariable=self.months_var,
        )
        self.months_spinbox.pack(side="left", padx=(5, 10))

        self.calc_btn = ttk.Button(
            calc_frame, text="Calculate Taxes", command=self._calculate_taxes
        )
        self.calc_btn.pack(side="left")

        main_frame.columnconfigure(2, weight=1)

    def _parse_dropped_files(self, data: str) -> list[str]:
        """Parse the dropped file paths from the DnD data string."""
        # Handle different formats from different OS
        # Windows may wrap paths in {} if they contain spaces
        files = []
        current = ""
        in_braces = False

        for char in data:
            if char == "{":
                in_braces = True
            elif char == "}":
                in_braces = False
                if current:
                    files.append(current.strip())
                    current = ""
            elif char == " " and not in_braces:
                if current:
                    files.append(current.strip())
                    current = ""
            else:
                current += char

        if current:
            files.append(current.strip())

        return [f for f in files if f]

    def _on_drop(self, event: Any) -> None:
        """Handle files dropped onto the drop zone."""
        files = self._parse_dropped_files(event.data)
        csv_files = [f for f in files if f.lower().endswith(".csv")]

        if not csv_files:
            messagebox.showwarning("Warning", "No CSV files found in dropped items")
            return

        self._load_files(csv_files)
        self._reset_drop_zone()

    def _on_drag_enter(self, event: Any) -> None:
        """Visual feedback when dragging over drop zone."""
        self.drop_zone.config(bg="#d0e8ff", text="Release to load files")

    def _on_drag_leave(self, event: Any) -> None:
        """Reset visual feedback when leaving drop zone."""
        self._reset_drop_zone()

    def _reset_drop_zone(self) -> None:
        """Reset drop zone to default appearance."""
        text = (
            "Drop CSV files here\nor click Browse" if self.has_dnd else "Click to select CSV files"
        )
        self.drop_zone.config(bg="#f0f0f0", text=text)

    def _browse_files(self) -> None:
        """Open file dialog to select CSV files."""
        files = filedialog.askopenfilenames(
            title="Select CSV Files",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if files:
            self._load_files(list(files))

    def _load_files(self, file_paths: list[str]) -> None:
        """Load CSV files from the given paths."""
        try:
            new_df = load_csvs_from_paths(file_paths)

            # Add to existing data or replace
            if self.df is not None:
                # Append new files, avoiding duplicates based on source_file
                existing_sources = set(self.df["source_file"].unique())
                new_sources = set(new_df["source_file"].unique())
                truly_new = new_sources - existing_sources

                if truly_new:
                    new_rows = new_df[new_df["source_file"].isin(truly_new)]
                    self.df = pd.concat([self.df, new_rows], ignore_index=True)
                    self.loaded_files.extend(
                        [f for f in file_paths if any(s in f for s in truly_new)]
                    )
            else:
                self.df = new_df
                self.loaded_files = list(file_paths)

            self._update_items_list()
            self._update_status()

        except FileNotFoundError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")

    def _clear_data(self) -> None:
        """Clear all loaded data."""
        self.df = None
        self.loaded_files = []
        self.items_listbox.delete(0, tk.END)
        self.status_label.config(text="No data loaded")
        self._reset_drop_zone()

    def _update_items_list(self) -> None:
        """Update the items listbox with current data."""
        if self.df is None:
            return

        items = get_unique_values(self.df, "Item")
        self.items_listbox.delete(0, tk.END)

        for item in items:
            category = self.calculator.get_category_for_item(item)
            display_text = f"{item} [{category}]" if category else item
            self.items_listbox.insert(tk.END, display_text)

    def _update_status(self) -> None:
        """Update the status label with current data info."""
        if self.df is None:
            self.status_label.config(text="No data loaded")
            return

        row_count = len(self.df)
        file_count = len(self.loaded_files)
        items = get_unique_values(self.df, "Item")
        self.status_label.config(
            text=f"Loaded {file_count} file(s), {row_count} transactions, {len(items)} unique items"
        )

    def _assign_items(self) -> None:
        """Assign selected items to the chosen category."""
        selected_indices = self.items_listbox.curselection()  # type: ignore[no-untyped-call]
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select items to assign")
            return

        category = self.category_combo.get()
        if not category:
            messagebox.showwarning("Warning", "Please select a category")
            return

        for idx in selected_indices:
            item = self.items_listbox.get(idx)
            # Remove category suffix if present
            if " [" in item:
                item = item.rsplit(" [", 1)[0]
            self.calculator.assign_item_to_category(item, category)

        self._update_category_contents()
        self._update_item_display()

    def _unassign_items(self) -> None:
        """Remove selected items from their categories."""
        selected_indices = self.items_listbox.curselection()  # type: ignore[no-untyped-call]
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select items to remove")
            return

        for idx in selected_indices:
            item = self.items_listbox.get(idx)
            # Remove category suffix if present
            if " [" in item:
                item = item.rsplit(" [", 1)[0]
            self.calculator.remove_item_from_category(item)

        self._update_category_contents()
        self._update_item_display()

    def _update_item_display(self) -> None:
        """Update the items listbox to show category assignments."""
        self._update_items_list()

    def _on_category_selected(self, _event: tk.Event[tk.Widget] | None = None) -> None:
        """Handle category selection - update description and contents."""
        category = self.category_combo.get()
        if category and category in self.calculator.categories:
            desc = self.calculator.categories[category].description
            self.category_desc_label.config(text=desc)
        else:
            self.category_desc_label.config(text="")
        self._update_category_contents()

    def _update_category_contents(self, _event: tk.Event[tk.Widget] | None = None) -> None:
        """Update the category contents display."""
        category = self.category_combo.get()
        if not category or category not in self.calculator.categories:
            return

        cat = self.calculator.categories[category]
        self.category_contents.config(state="normal")
        self.category_contents.delete(1.0, tk.END)

        if cat.items:
            self.category_contents.insert(tk.END, f"Items in {category}:\n\n")
            for item in cat.items:
                self.category_contents.insert(tk.END, f"  - {item}\n")
        else:
            self.category_contents.insert(tk.END, "No items assigned")

        self.category_contents.config(state="disabled")

    def _calculate_taxes(self) -> None:
        """Calculate and display tax summary."""
        if self.df is None:
            messagebox.showwarning("Warning", "Please load data first")
            return

        # Get months from spinbox
        try:
            months = int(self.months_var.get())
        except ValueError:
            months = 12

        summary = self.calculator.generate_summary(self.df, months)
        period: TaxResults = summary["period_taxes"]
        annual: TaxResults = summary["annual_taxes"]

        self.results_text.config(state="normal")
        self.results_text.delete(1.0, tk.END)

        # Header with column labels
        self.results_text.insert(tk.END, f"{'':20} {'PERIOD':>12}  {'ANNUAL':>12}\n")
        self.results_text.insert(
            tk.END, f"{'':20} {'(' + str(months) + ' mo)':>12}  {'(12 mo)':>12}\n"
        )
        self.results_text.insert(tk.END, "═" * 48 + "\n\n")

        # Income section
        self.results_text.insert(tk.END, "─── INCOME ───\n")
        self._insert_row(
            "Freelance (Tax Already Paid)", period.all_tax_applied, annual.all_tax_applied
        )
        self._insert_row(
            "Revenue (Sales Tax Bundled)", period.sales_tax_bundled, annual.sales_tax_bundled
        )
        self._insert_row(
            "Revenue (Sales Tax Applied)", period.sales_tax_applied, annual.sales_tax_applied
        )
        self._insert_row("Business Expenses", -period.expenses, -annual.expenses)
        self.results_text.insert(tk.END, "\n")

        # Business calculations
        self.results_text.insert(tk.END, "─── PROFIT ───\n")
        self._insert_row("Gross Revenue", period.gross_revenue, annual.gross_revenue)
        self._insert_row("Business Profit", period.business_profit, annual.business_profit)
        self._insert_row("Total Profit", period.profit, annual.profit)
        self._insert_row("Sales Taxable Income", period.sales_taxable, annual.sales_taxable)
        self._insert_row("Taxable Income", period.taxable_income, annual.taxable_income)
        self.results_text.insert(tk.END, "\n")

        # Taxes section
        self.results_text.insert(tk.END, "─── TAXES ───\n")
        self._insert_row(
            f"Sales Tax ({period.sales_tax_rate * 100:.2f}%)", period.sales_tax, annual.sales_tax
        )
        self._insert_row(
            "Self-Employment Tax", period.sole_proprietor_tax, annual.sole_proprietor_tax
        )
        self._insert_row("Federal Income Tax", period.federal_income_tax, annual.federal_income_tax)
        self._insert_row("State Income Tax", period.state_income_tax, annual.state_income_tax)
        self.results_text.insert(tk.END, f"{'':20} {'─' * 12}  {'─' * 12}\n")
        self._insert_row("Total Income Tax", period.total_income_tax, annual.total_income_tax)
        self._insert_row("Total Tax", period.total_tax, annual.total_tax)
        self.results_text.insert(tk.END, "\n")

        # Summary section
        self.results_text.insert(tk.END, "─── SUMMARY ───\n")
        self.results_text.insert(tk.END, f"{'':20} {'═' * 12}  {'═' * 12}\n")
        self._insert_row("TAKE HOME", period.take_home, annual.take_home)

        # Show uncategorized items
        uncategorized = self.calculator.get_uncategorized_items(self.df)
        if uncategorized:
            self.results_text.insert(tk.END, f"\n─── UNCATEGORIZED ({len(uncategorized)}) ───\n")
            for item in uncategorized[:6]:
                self.results_text.insert(tk.END, f"  • {item}\n")
            if len(uncategorized) > 6:
                self.results_text.insert(tk.END, f"  ... +{len(uncategorized) - 6} more\n")

        self.results_text.config(state="disabled")

    def _insert_row(self, label: str, period_val: float, annual_val: float) -> None:
        """Insert a row with label and two value columns."""
        self.results_text.insert(
            tk.END, f"{label:20} ${period_val:>11,.2f}  ${annual_val:>11,.2f}\n"
        )

    def run(self) -> None:
        """Start the GUI main loop."""
        self.root.mainloop()
