from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


# Tax rates (configurable)
SALES_TAX_RATE = 0.0775  # 7.75%
SELF_EMPLOYMENT_TAX_RATE = 0.153  # 15.3%
SELF_EMPLOYMENT_INCOME_FACTOR = 0.9235  # 92.35% of profit is subject to SE tax
FEDERAL_TAX_RATE = 0.17  # 17%
STATE_TAX_RATE = 0.05  # 5%


# Income category types
CATEGORY_GIGS = "Gigs (Tax Already Paid)"
CATEGORY_REVENUE_NO_SALES_TAX = "Revenue (No Sales Tax)"
CATEGORY_REVENUE_WITH_SALES_TAX = "Revenue (Sales Tax Included)"
CATEGORY_EXPENSES = "Business Expenses"
CATEGORY_UNCATEGORIZED = "Uncategorized"


@dataclass
class IncomeCategory:
    """Represents an income/expense category with associated items."""

    name: str
    description: str
    items: list[str] = field(default_factory=list)


class TaxCalculator:
    """Calculate taxes based on categorized transactions."""

    def __init__(self) -> None:
        self.categories: dict[str, IncomeCategory] = {}
        self.item_to_category: dict[str, str] = {}
        self._setup_default_categories()

    def _setup_default_categories(self) -> None:
        """Set up the four main income/expense categories."""
        self.add_category(
            CATEGORY_GIGS,
            "Income where sales tax and income tax are already withheld (e.g., W-2 gig work)",
        )
        self.add_category(
            CATEGORY_REVENUE_NO_SALES_TAX,
            "Business revenue that needs sales tax calculated (7.75%)",
        )
        self.add_category(
            CATEGORY_REVENUE_WITH_SALES_TAX,
            "Business revenue where sales tax is already included",
        )
        self.add_category(
            CATEGORY_EXPENSES,
            "Deductible business expenses",
        )

    def add_category(self, name: str, description: str = "") -> None:
        """Add a new category."""
        self.categories[name] = IncomeCategory(name=name, description=description)

    def assign_item_to_category(self, item: str, category_name: str) -> None:
        """Assign an item (from the data) to a category."""
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

    def _get_category_total(self, df: pd.DataFrame, category_name: str) -> float:
        """Get the sum of amounts for a specific category."""
        if category_name not in self.categories:
            return 0.0

        category = self.categories[category_name]
        if not category.items:
            return 0.0

        mask = df["Item"].isin(category.items)
        return float(df[mask]["Amount"].sum())

    def get_uncategorized_items(self, df: pd.DataFrame) -> list[str]:
        """Get list of items that haven't been categorized."""
        all_items = set(df["Item"].unique())
        categorized_items = set(self.item_to_category.keys())
        return sorted(all_items - categorized_items)

    def get_category_for_item(self, item: str) -> str | None:
        """Get the category name for an item."""
        return self.item_to_category.get(item)

    def calculate_taxes(self, df: pd.DataFrame) -> dict[str, float]:
        """
        Calculate all taxes based on the Excel formulas.

        Input categories:
        - Gigs (B): Income with sales tax & income tax already applied
        - Revenue No Sales Tax (C): Needs sales tax calculated
        - Revenue With Sales Tax (D): Sales tax already included
        - Expenses (F): Deductible business expenses

        Formulas:
        - Sales Tax Due (E) = C * 7.75%
        - Profit (G) = (C - E) + D - F
        - Sole Proprietor Tax (H) = (G * 0.9235) * 15.3%
        - Federal Income Tax (I) = (G - H*0.5) * 17%
        - State Income Tax (J) = (G - H*0.5) * 5%
        - Total Income Tax (K) = H + I + J
        - Take Home (L) = G + B - K
        - Gross Revenue (M) = B + C + D - F
        """
        # Get totals for each input category (amounts are already signed correctly)
        gigs = self._get_category_total(df, CATEGORY_GIGS)
        revenue_no_sales_tax = self._get_category_total(df, CATEGORY_REVENUE_NO_SALES_TAX)
        revenue_with_sales_tax = self._get_category_total(df, CATEGORY_REVENUE_WITH_SALES_TAX)
        expenses = abs(self._get_category_total(df, CATEGORY_EXPENSES))  # Make positive for calc

        # Calculate Sales Tax Due (E = C * 0.0775)
        sales_tax_due = revenue_no_sales_tax * SALES_TAX_RATE

        # Calculate Profit from Business (G = (C - E) + D - F)
        profit = (revenue_no_sales_tax - sales_tax_due) + revenue_with_sales_tax - expenses

        # Calculate Sole Proprietor Tax (H = (G * 0.9235) * 0.153)
        sole_proprietor_tax = (profit * SELF_EMPLOYMENT_INCOME_FACTOR) * SELF_EMPLOYMENT_TAX_RATE

        # Half of SE tax is deductible for income tax calculation
        se_tax_deduction = sole_proprietor_tax * 0.5

        # Calculate Federal Income Tax (I = (G - H*0.5) * 0.17)
        federal_income_tax = (profit - se_tax_deduction) * FEDERAL_TAX_RATE

        # Calculate State Income Tax (J = (G - H*0.5) * 0.05)
        state_income_tax = (profit - se_tax_deduction) * STATE_TAX_RATE

        # Calculate Total Income Taxes Due (K = H + I + J)
        total_income_tax = sole_proprietor_tax + federal_income_tax + state_income_tax

        # Calculate Total Take Home (L = G + B - K)
        take_home = profit + gigs - total_income_tax

        # Calculate Gross Revenue (M = B + C + D - F)
        gross_revenue = gigs + revenue_no_sales_tax + revenue_with_sales_tax - expenses

        return {
            "gigs": gigs,
            "revenue_no_sales_tax": revenue_no_sales_tax,
            "revenue_with_sales_tax": revenue_with_sales_tax,
            "expenses": expenses,
            "sales_tax_due": sales_tax_due,
            "profit": profit,
            "sole_proprietor_tax": sole_proprietor_tax,
            "federal_income_tax": federal_income_tax,
            "state_income_tax": state_income_tax,
            "total_income_tax": total_income_tax,
            "take_home": take_home,
            "gross_revenue": gross_revenue,
        }

    def generate_summary(self, df: pd.DataFrame) -> dict[str, float | dict[str, float]]:
        """Generate a complete tax summary."""
        taxes = self.calculate_taxes(df)
        uncategorized_count = len(self.get_uncategorized_items(df))

        return {
            **taxes,
            "uncategorized_count": uncategorized_count,
        }
