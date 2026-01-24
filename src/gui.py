from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from .data_loader import get_unique_values, load_all_csvs
from .tax_calculator import TaxCalculator

if TYPE_CHECKING:
    import pandas as pd


class TaximateGUI:
    """Main GUI for the Taximate application."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Taximate - Tax Calculator")
        self.root.geometry("1100x750")

        self.df: pd.DataFrame | None = None
        self.calculator = TaxCalculator()

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Load data button
        load_frame = ttk.Frame(main_frame)
        load_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        self.load_btn = ttk.Button(load_frame, text="Load CSV Data", command=self._load_data)
        self.load_btn.pack(side="left")

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

        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            cat_frame, textvariable=self.category_var, state="readonly", width=35
        )
        self.category_combo["values"] = list(self.calculator.categories.keys())
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

        self.results_text = tk.Text(right_frame, width=38, height=25, state="disabled")
        self.results_text.pack(fill="both", expand=True)

        self.calc_btn = ttk.Button(
            right_frame, text="Calculate Taxes", command=self._calculate_taxes
        )
        self.calc_btn.pack(pady=(10, 0))

        main_frame.columnconfigure(2, weight=1)

    def _load_data(self) -> None:
        """Load CSV data from the data directory."""
        try:
            self.df = load_all_csvs("data")
            items = get_unique_values(self.df, "Item")

            self.items_listbox.delete(0, tk.END)
            for item in items:
                self.items_listbox.insert(tk.END, item)

            row_count = len(self.df)
            self.status_label.config(
                text=f"Loaded {row_count} transactions, {len(items)} unique items"
            )
        except FileNotFoundError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")

    def _assign_items(self) -> None:
        """Assign selected items to the chosen category."""
        selected_indices = self.items_listbox.curselection()  # type: ignore[no-untyped-call]
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select items to assign")
            return

        category = self.category_var.get()
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
        if self.df is None:
            return

        items = get_unique_values(self.df, "Item")
        self.items_listbox.delete(0, tk.END)

        for item in items:
            category = self.calculator.get_category_for_item(item)
            display_text = f"{item} [{category}]" if category else item
            self.items_listbox.insert(tk.END, display_text)

    def _on_category_selected(self, _event: tk.Event[tk.Widget] | None = None) -> None:
        """Handle category selection - update description and contents."""
        category = self.category_var.get()
        if category and category in self.calculator.categories:
            desc = self.calculator.categories[category].description
            self.category_desc_label.config(text=desc)
        else:
            self.category_desc_label.config(text="")
        self._update_category_contents()

    def _update_category_contents(self, _event: tk.Event[tk.Widget] | None = None) -> None:
        """Update the category contents display."""
        category = self.category_var.get()
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

        summary = self.calculator.generate_summary(self.df)

        self.results_text.config(state="normal")
        self.results_text.delete(1.0, tk.END)

        self.results_text.insert(tk.END, "═══════ TAX SUMMARY ═══════\n\n")

        # Input categories
        self.results_text.insert(tk.END, "─── INPUT TOTALS ───\n")
        self.results_text.insert(tk.END, f"Gigs (tax paid):      ${summary['gigs']:>12,.2f}\n")
        self.results_text.insert(
            tk.END, f"Revenue (no tax):     ${summary['revenue_no_sales_tax']:>12,.2f}\n"
        )
        self.results_text.insert(
            tk.END, f"Revenue (w/ tax):     ${summary['revenue_with_sales_tax']:>12,.2f}\n"
        )
        self.results_text.insert(tk.END, f"Expenses:             ${summary['expenses']:>12,.2f}\n")

        self.results_text.insert(tk.END, "\n─── CALCULATED TAXES ───\n")
        self.results_text.insert(
            tk.END, f"Sales Tax Due:        ${summary['sales_tax_due']:>12,.2f}\n"
        )
        self.results_text.insert(
            tk.END, f"Sole Proprietor Tax:  ${summary['sole_proprietor_tax']:>12,.2f}\n"
        )
        self.results_text.insert(
            tk.END, f"Federal Income Tax:   ${summary['federal_income_tax']:>12,.2f}\n"
        )
        self.results_text.insert(
            tk.END, f"State Income Tax:     ${summary['state_income_tax']:>12,.2f}\n"
        )
        self.results_text.insert(tk.END, "                      ─────────────\n")
        self.results_text.insert(
            tk.END, f"Total Income Tax:     ${summary['total_income_tax']:>12,.2f}\n"
        )

        self.results_text.insert(tk.END, "\n─── SUMMARY ───\n")
        self.results_text.insert(
            tk.END, f"Gross Revenue:        ${summary['gross_revenue']:>12,.2f}\n"
        )
        self.results_text.insert(tk.END, f"Business Profit:      ${summary['profit']:>12,.2f}\n")
        self.results_text.insert(tk.END, "                      ═════════════\n")
        self.results_text.insert(tk.END, f"TOTAL TAKE HOME:      ${summary['take_home']:>12,.2f}\n")

        # Show uncategorized items
        uncategorized = self.calculator.get_uncategorized_items(self.df)
        if uncategorized:
            self.results_text.insert(tk.END, f"\n─── UNCATEGORIZED ({len(uncategorized)}) ───\n")
            for item in uncategorized[:8]:
                self.results_text.insert(tk.END, f"  • {item}\n")
            if len(uncategorized) > 8:
                self.results_text.insert(tk.END, f"  ... +{len(uncategorized) - 8} more\n")

        self.results_text.config(state="disabled")

    def run(self) -> None:
        """Start the GUI main loop."""
        self.root.mainloop()
