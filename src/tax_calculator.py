"""Tax calculation engine for self-employment income.

This module provides classes for calculating various taxes on self-employment
income including:
- Federal income tax (progressive brackets)
- California state income tax (progressive brackets)
- Self-employment tax (Social Security + Medicare)
- Sales tax

Tax rates are loaded from CSV files in the tax_rates/ directory, making them
easy to update for new tax years or different jurisdictions.

Classes:
    TaxBracket: Represents a single progressive tax bracket.
    IncomeCategory: Groups transaction items into income/expense categories.
    TaxInputs: Input values aggregated from transaction categories.
    TaxResults: Complete tax calculation results with all computed values.
    TaxRates: Loads and manages tax rates from CSV files.
    TaxCalculator: Main calculation engine for computing taxes.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# Income category type constants
CATEGORY_FREELANCE = "Freelance (Tax Already Paid)"
CATEGORY_REVENUE_SALES_TAX_BUNDLED = "Revenue (Sales Tax Bundled)"
CATEGORY_REVENUE_SALES_TAX_APPLIED = "Revenue (Sales Tax Applied)"
CATEGORY_EXPENSES = "Business Expenses"


def _get_base_path() -> Path:
    """Get the base path for resources, handling PyInstaller bundles."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running as PyInstaller bundle
        return Path(sys._MEIPASS)
    # Running as normal Python script
    return Path(__file__).parent.parent


# Default tax rates directory
TAX_RATES_DIR = _get_base_path() / "tax_rates"


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


@dataclass(frozen=True, slots=True)
class TaxInputs:
    """Input values for tax calculations, aggregated from transaction categories.

    Attributes:
        all_tax_applied: Freelance income where taxes are already withheld.
        sales_tax_bundled: Revenue with sales tax included in the price.
        sales_tax_applied: Revenue where sales tax was collected separately.
        expenses: Total deductible business expenses (positive value).
        deductions: Manual deductions (e.g., home office deduction).
    """

    all_tax_applied: float
    sales_tax_bundled: float
    sales_tax_applied: float
    expenses: float
    deductions: float = 0.0

    def annualized(self, months: int) -> TaxInputs:
        factor = 12 / months
        return TaxInputs(
            all_tax_applied=self.all_tax_applied * factor,
            sales_tax_bundled=self.sales_tax_bundled * factor,
            sales_tax_applied=self.sales_tax_applied * factor,
            expenses=self.expenses * factor,
            deductions=self.deductions * factor,
        )


@dataclass(frozen=True, slots=True)
class TaxResults:
    """Complete tax calculation results.

    Contains both input values (for display) and all calculated tax amounts.

    Input Fields:
        all_tax_applied: Freelance income (taxes already withheld).
        sales_tax_bundled: Revenue with sales tax bundled in price.
        sales_tax_applied: Revenue with sales tax collected separately.
        expenses: Business expenses.
        deductions: Manual deductions (e.g., home office).

    Calculated Fields:
        sales_taxable: Revenue after extracting bundled sales tax.
        sales_tax_rate: Applied sales tax rate.
        sales_tax: Calculated sales tax owed.
        profit: Total profit (business + freelance).
        business_profit: Profit from business revenue minus expenses.
        taxable_income: Income subject to income tax (after SE deduction).
        sole_proprietor_tax: Self-employment tax (SS + Medicare).
        federal_income_tax: Federal income tax from brackets.
        state_income_tax: State income tax from brackets.
        total_income_tax: Sum of SE + federal + state taxes.
        total_tax: Total tax including sales tax.
        take_home: Net income after all income taxes.
        gross_business_revenue: Total business revenue before taxes.
        gross_revenue: Total revenue including freelance income.
    """

    all_tax_applied: float
    sales_tax_bundled: float
    sales_tax_applied: float
    expenses: float
    deductions: float

    sales_taxable: float
    sales_tax_rate: float
    sales_tax: float

    profit: float
    business_profit: float
    taxable_income: float

    sole_proprietor_tax: float
    federal_income_tax: float
    state_income_tax: float
    total_income_tax: float
    total_tax: float

    take_home: float
    gross_business_revenue: float
    gross_revenue: float

    def as_dict(self) -> dict[str, float]:
        """Convert results to a dictionary."""
        return self.__dict__


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
        self.home_office_deduction: float = 0.0
        self.car_deduction: float = 0.0
        self._setup_default_categories()

    @property
    def manual_deductions(self) -> float:
        """Total of all manual deductions."""
        return self.home_office_deduction + self.car_deduction

    def _setup_default_categories(self) -> None:
        """Set up the four main income/expense categories."""
        self.add_category(
            CATEGORY_FREELANCE,
            "Income where sales tax and income tax are already withheld (e.g., W-2 gig work)",
        )
        self.add_category(
            CATEGORY_REVENUE_SALES_TAX_BUNDLED,
            f"Business revenue that has sales tax bundled in ({self.tax_rates.sales_tax_rate * 100:.2f}%)",
        )
        self.add_category(
            CATEGORY_REVENUE_SALES_TAX_APPLIED,
            "Business revenue where sales tax is already applied",
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

    def calculate_taxes(self, inputs: TaxInputs) -> TaxResults:
        """Core tax calculator given category totals (already aggregated)."""
        # Backcalculate how much sales tax in included in the sales_tax_bundled
        sales_taxable = inputs.sales_tax_bundled / (1 + self.tax_rates.sales_tax_rate)
        sales_tax = inputs.sales_tax_bundled - sales_taxable

        # Calculate how much profit from hustles and main business
        # Deductions reduce profit similar to expenses
        total_deductible = inputs.expenses + inputs.deductions
        business_profit = sales_taxable + inputs.sales_tax_applied - total_deductible
        profit = business_profit + inputs.all_tax_applied

        sole_proprietor_tax = self.tax_rates.calculate_self_employment_tax(business_profit)

        se_tax_deduction = sole_proprietor_tax * 0.5
        taxable_income = max(0.0, business_profit - se_tax_deduction)

        federal_income_tax = self.tax_rates.calculate_bracket_tax(
            taxable_income, self.tax_rates.federal_brackets
        )
        state_income_tax = self.tax_rates.calculate_bracket_tax(
            taxable_income, self.tax_rates.state_brackets
        )

        total_income_tax = sole_proprietor_tax + federal_income_tax + state_income_tax
        total_tax = total_income_tax + sales_tax
        take_home = profit - total_income_tax
        gross_business_revenue = inputs.sales_tax_applied + inputs.sales_tax_bundled
        gross_revenue = gross_business_revenue + inputs.all_tax_applied

        return TaxResults(
            all_tax_applied=inputs.all_tax_applied,
            sales_tax_bundled=inputs.sales_tax_bundled,
            sales_tax_applied=inputs.sales_tax_applied,
            expenses=inputs.expenses,
            deductions=inputs.deductions,
            sales_taxable=sales_taxable,
            sales_tax_rate=self.tax_rates.sales_tax_rate,
            sales_tax=sales_tax,
            profit=profit,
            business_profit=business_profit,
            taxable_income=taxable_income,
            sole_proprietor_tax=sole_proprietor_tax,
            federal_income_tax=federal_income_tax,
            state_income_tax=state_income_tax,
            total_income_tax=total_income_tax,
            total_tax=total_tax,
            take_home=take_home,
            gross_business_revenue=gross_business_revenue,
            gross_revenue=gross_revenue,
        )

    def extract_period_totals(self, df: pd.DataFrame) -> TaxInputs:
        return TaxInputs(
            all_tax_applied=self._get_category_total(df, CATEGORY_FREELANCE),
            sales_tax_bundled=self._get_category_total(df, CATEGORY_REVENUE_SALES_TAX_BUNDLED),
            sales_tax_applied=self._get_category_total(df, CATEGORY_REVENUE_SALES_TAX_APPLIED),
            expenses=abs(self._get_category_total(df, CATEGORY_EXPENSES)),
            deductions=self.manual_deductions,
        )

    def generate_summary(
        self, df: pd.DataFrame, months: int = 12
    ) -> dict[str, TaxInputs | TaxResults | float]:
        """Generate a complete tax summary with optional annualization."""
        # Collect all the data needed for calculation
        tax_inputs = self.extract_period_totals(df)

        # project those values for a year
        annual_inputs = tax_inputs.annualized(months)

        # calculate current and annualized taxes
        period_taxes = self.calculate_taxes(tax_inputs)
        annual_taxes = self.calculate_taxes(annual_inputs)

        uncategorized_count = len(self.get_uncategorized_items(df))

        return {
            "tax_inputs": tax_inputs,
            "annual_inputs": annual_inputs,
            "period_taxes": period_taxes,
            "annual_taxes": annual_taxes,
            "uncategorized_count": float(uncategorized_count),
        }
