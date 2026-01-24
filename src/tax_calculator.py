from dataclasses import dataclass, field

import pandas as pd


@dataclass
class TaxCategory:
    """Represents a tax category with associated items."""

    name: str
    description: str
    items: list = field(default_factory=list)
    deduction_rate: float = 1.0  # Percentage of amount that's deductible (0.0 to 1.0)


class TaxCalculator:
    """Calculate taxes based on categorized transactions."""

    def __init__(self) -> None:
        self.categories: dict[str, TaxCategory] = {}
        self.item_to_category: dict[str, str] = {}

    def add_category(self, name: str, description: str = "", deduction_rate: float = 1.0) -> None:
        """Add a new tax category."""
        self.categories[name] = TaxCategory(
            name=name, description=description, deduction_rate=deduction_rate
        )

    def assign_item_to_category(self, item: str, category_name: str) -> None:
        """Assign an item (from the data) to a tax category."""
        if category_name not in self.categories:
            raise ValueError(f"Category '{category_name}' does not exist")

        # Remove from previous category if exists
        if item in self.item_to_category:
            old_category = self.item_to_category[item]
            if item in self.categories[old_category].items:
                self.categories[old_category].items.remove(item)

        self.categories[category_name].items.append(item)
        self.item_to_category[item] = category_name

    def remove_item_from_category(self, item: str) -> None:
        """Remove an item from its category."""
        if item in self.item_to_category:
            category_name = self.item_to_category[item]
            if item in self.categories[category_name].items:
                self.categories[category_name].items.remove(item)
            del self.item_to_category[item]

    def calculate_category_totals(self, df: pd.DataFrame) -> dict[str, float]:
        """Calculate totals for each category from the dataframe."""
        totals = {}

        for category_name, category in self.categories.items():
            if category.items:
                # Filter transactions matching category items
                mask = df["Item"].isin(category.items)
                category_df = df[mask]
                raw_total = category_df["Amount"].sum()
                # Apply deduction rate
                totals[category_name] = raw_total * category.deduction_rate
            else:
                totals[category_name] = 0.0

        return totals

    def calculate_total_deductions(self, df: pd.DataFrame) -> float:
        """Calculate total deductions across all categories."""
        totals = self.calculate_category_totals(df)
        return sum(totals.values())

    def get_uncategorized_items(self, df: pd.DataFrame) -> list:
        """Get list of items that haven't been categorized."""
        all_items = set(df["Item"].unique())
        categorized_items = set(self.item_to_category.keys())
        return sorted(all_items - categorized_items)

    def get_category_for_item(self, item: str) -> str | None:
        """Get the category name for an item."""
        return self.item_to_category.get(item)

    def generate_summary(self, df: pd.DataFrame) -> dict:
        """Generate a complete tax summary."""
        totals = self.calculate_category_totals(df)
        total_income = df[df["Type"] == "income"]["Amount"].sum()
        total_expenses = df[df["Type"] == "expense"]["Amount"].sum()
        total_deductions = sum(totals.values())

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "category_totals": totals,
            "total_deductions": total_deductions,
            "taxable_income": total_income + total_deductions,  # deductions are negative
        }
