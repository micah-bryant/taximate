from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# Income category types
CATEGORY_GIGS = "Gigs (Tax Already Paid)"
CATEGORY_REVENUE_NO_SALES_TAX = "Revenue (No Sales Tax)"
CATEGORY_REVENUE_WITH_SALES_TAX = "Revenue (Sales Tax Included)"
CATEGORY_EXPENSES = "Business Expenses"

# Default tax rates directory
TAX_RATES_DIR = Path(__file__).parent.parent / "tax_rates"


@dataclass
class TaxBracket:
    """Represents a single tax bracket."""

    rate: float
    min_income: float
    max_income: float | None  # None means no upper limit


@dataclass
class IncomeCategory:
    """Represents an income/expense category with associated items."""

    name: str
    description: str
    items: list[str] = field(default_factory=list)


class TaxRates:
    """Load and manage tax rates from CSV files."""

    def __init__(self, tax_rates_dir: Path = TAX_RATES_DIR) -> None:
        self.tax_rates_dir = tax_rates_dir
        self.federal_brackets: list[TaxBracket] = []
        self.state_brackets: list[TaxBracket] = []
        self.se_social_security_rate: float = 0.124
        self.se_medicare_rate: float = 0.029
        self.se_additional_medicare_rate: float = 0.009
        self.se_additional_medicare_threshold: float = 200000
        self.se_wage_base: float = 176100
        self.se_income_factor: float = 0.9235
        self.sales_tax_rate: float = 0.0775
        self._load_rates()

    def _load_rates(self) -> None:
        """Load all tax rates from CSV files."""
        self._load_federal_brackets()
        self._load_state_brackets()
        self._load_self_employment_rates()
        self._load_sales_tax_rates()

    def _load_federal_brackets(self) -> None:
        """Load federal income tax brackets."""
        csv_path = self.tax_rates_dir / "federal_income_tax_2025.csv"
        if not csv_path.exists():
            return

        df = pd.read_csv(csv_path)
        # Filter for single filers (default)
        single_df = df[df["filing_status"] == "single"]

        self.federal_brackets = []
        for _, row in single_df.iterrows():
            max_income: str = row["max_income"] if pd.notna(row["max_income"]) else None
            self.federal_brackets.append(
                TaxBracket(
                    rate=float(row["rate"]),
                    min_income=float(row["min_income"]),
                    max_income=float(max_income) if max_income else None,
                )
            )

    def _load_state_brackets(self) -> None:
        """Load California state income tax brackets."""
        csv_path = self.tax_rates_dir / "california_income_tax_2024.csv"
        if not csv_path.exists():
            return

        df = pd.read_csv(csv_path)
        # Filter for single filers (default)
        single_df = df[df["filing_status"] == "single"]

        self.state_brackets = []
        for _, row in single_df.iterrows():
            max_income: str = row["max_income"] if pd.notna(row["max_income"]) else None
            self.state_brackets.append(
                TaxBracket(
                    rate=float(row["rate"]),
                    min_income=float(row["min_income"]),
                    max_income=float(max_income) if max_income else None,
                )
            )

    def _load_self_employment_rates(self) -> None:
        """Load self-employment tax rates."""
        csv_path = self.tax_rates_dir / "self_employment_tax_2025.csv"
        if not csv_path.exists():
            return

        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            tax_type = row["tax_type"]
            rate = float(row["rate"])

            if tax_type == "social_security":
                self.se_social_security_rate = rate
                if pd.notna(row["wage_base"]):
                    self.se_wage_base = float(row["wage_base"])
            elif tax_type == "medicare":
                self.se_medicare_rate = rate
            elif tax_type == "additional_medicare":
                self.se_additional_medicare_rate = rate
                if pd.notna(row["wage_base"]):
                    self.se_additional_medicare_threshold = float(row["wage_base"])
            elif tax_type == "income_factor":
                self.se_income_factor = rate

    def _load_sales_tax_rates(self) -> None:
        """Load sales tax rates."""
        csv_path = self.tax_rates_dir / "sales_tax_2025.csv"
        if not csv_path.exists():
            return

        df = pd.read_csv(csv_path)
        # Use San Diego city rate as default
        san_diego_row = df[df["jurisdiction"] == "san_diego_city"]
        if not san_diego_row.empty:
            self.sales_tax_rate = float(san_diego_row.iloc[0]["rate"])

    def calculate_bracket_tax(self, income: float, brackets: list[TaxBracket]) -> float:
        """Calculate tax using progressive brackets."""
        if income <= 0:
            return 0.0

        total_tax = 0.0

        for bracket in brackets:
            if income <= bracket.min_income:
                break

            # Determine the taxable amount in this bracket
            bracket_min = bracket.min_income
            bracket_max = bracket.max_income if bracket.max_income else float("inf")

            taxable_in_bracket = min(income, bracket_max) - bracket_min
            if taxable_in_bracket > 0:
                total_tax += taxable_in_bracket * bracket.rate

        return total_tax

    def calculate_self_employment_tax(self, net_earnings: float) -> float:
        """
        Calculate self-employment tax.

        SE tax = (net_earnings * 0.9235) * (Social Security rate + Medicare rate)
        Plus additional Medicare tax on high earners.
        """
        if net_earnings <= 0:
            return 0.0

        # Apply the 92.35% factor
        taxable_se_income = net_earnings * self.se_income_factor

        # Social Security portion (capped at wage base)
        ss_taxable = min(taxable_se_income, self.se_wage_base)
        ss_tax = ss_taxable * self.se_social_security_rate

        # Medicare portion (no cap)
        medicare_tax = taxable_se_income * self.se_medicare_rate

        # Additional Medicare tax on high earners
        additional_medicare = 0.0
        if taxable_se_income > self.se_additional_medicare_threshold:
            additional_medicare = (
                taxable_se_income - self.se_additional_medicare_threshold
            ) * self.se_additional_medicare_rate

        return ss_tax + medicare_tax + additional_medicare


class TaxCalculator:
    """Calculate taxes based on categorized transactions."""

    def __init__(self, tax_rates_dir: Path = TAX_RATES_DIR) -> None:
        self.categories: dict[str, IncomeCategory] = {}
        self.item_to_category: dict[str, str] = {}
        self.tax_rates = TaxRates(tax_rates_dir)
        self._setup_default_categories()

    def _setup_default_categories(self) -> None:
        """Set up the four main income/expense categories."""
        self.add_category(
            CATEGORY_GIGS,
            "Income where sales tax and income tax are already withheld (e.g., W-2 gig work)",
        )
        self.add_category(
            CATEGORY_REVENUE_NO_SALES_TAX,
            f"Business revenue that needs sales tax calculated ({self.tax_rates.sales_tax_rate * 100:.2f}%)",
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
        Calculate all taxes using bracket-based rates from CSV files.

        Input categories:
        - Gigs (B): Income with sales tax & income tax already applied
        - Revenue No Sales Tax (C): Needs sales tax calculated
        - Revenue With Sales Tax (D): Sales tax already included
        - Expenses (F): Deductible business expenses

        Calculations:
        - Sales Tax Due = C * sales_tax_rate
        - Profit = (C - Sales Tax) + D - F
        - Self-Employment Tax = calculated using SE tax rules (SS + Medicare)
        - Federal Income Tax = calculated using federal brackets on (Profit - SE deduction)
        - State Income Tax = calculated using CA brackets on (Profit - SE deduction)
        - Total Income Tax = SE Tax + Federal + State
        - Take Home = Profit + Gigs - Total Income Tax
        - Gross Revenue = Gigs + C + D - F
        """
        # Get totals for each input category
        gigs = self._get_category_total(df, CATEGORY_GIGS)
        revenue_no_sales_tax = self._get_category_total(df, CATEGORY_REVENUE_NO_SALES_TAX)
        revenue_with_sales_tax = self._get_category_total(df, CATEGORY_REVENUE_WITH_SALES_TAX)
        expenses = abs(self._get_category_total(df, CATEGORY_EXPENSES))

        # Calculate Sales Tax Due
        sales_tax_due = revenue_no_sales_tax * self.tax_rates.sales_tax_rate

        # Calculate Profit from Business
        profit = (revenue_no_sales_tax - sales_tax_due) + revenue_with_sales_tax - expenses

        # Calculate Self-Employment Tax using proper SE tax rules
        sole_proprietor_tax = self.tax_rates.calculate_self_employment_tax(profit)

        # Half of SE tax is deductible for income tax calculation
        se_tax_deduction = sole_proprietor_tax * 0.5
        taxable_income = max(0, profit - se_tax_deduction)

        # Calculate Federal Income Tax using brackets
        federal_income_tax = self.tax_rates.calculate_bracket_tax(
            taxable_income, self.tax_rates.federal_brackets
        )

        # Calculate State Income Tax using California brackets
        state_income_tax = self.tax_rates.calculate_bracket_tax(
            taxable_income, self.tax_rates.state_brackets
        )

        # Calculate Total Income Taxes Due
        total_income_tax = sole_proprietor_tax + federal_income_tax + state_income_tax

        # Calculate Total Take Home
        take_home = profit + gigs - total_income_tax

        # Calculate Gross Revenue
        gross_revenue = gigs + revenue_no_sales_tax + revenue_with_sales_tax - expenses

        return {
            "gigs": gigs,
            "revenue_no_sales_tax": revenue_no_sales_tax,
            "revenue_with_sales_tax": revenue_with_sales_tax,
            "expenses": expenses,
            "sales_tax_rate": self.tax_rates.sales_tax_rate,
            "sales_tax_due": sales_tax_due,
            "profit": profit,
            "taxable_income": taxable_income,
            "sole_proprietor_tax": sole_proprietor_tax,
            "federal_income_tax": federal_income_tax,
            "state_income_tax": state_income_tax,
            "total_income_tax": total_income_tax,
            "take_home": take_home,
            "gross_revenue": gross_revenue,
        }

    def generate_summary(self, df: pd.DataFrame) -> dict[str, float]:
        """Generate a complete tax summary."""
        taxes = self.calculate_taxes(df)
        uncategorized_count = len(self.get_uncategorized_items(df))

        return {
            **taxes,
            "uncategorized_count": float(uncategorized_count),
        }
