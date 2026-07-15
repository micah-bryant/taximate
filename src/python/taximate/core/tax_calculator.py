"""Tax calculation engine for self-employment income.

Computes federal + state (CA, MA) income tax, self-employment tax (SS + Medicare +
Additional Medicare), sales tax, and manual deductions (home office, car). Rates load
from ``tax_rates/*.csv``.

Estimates only, not tax advice. Deliberate simplifications:
    - No federal standard deduction (federal taxable income starts at $0).
    - Freelance income already taxed (``all_tax_applied``) doesn't fill the lower
      brackets, so business income's marginal rate can be understated.
    - The Social Security wage base isn't reduced by W-2 wages already taxed.
    - The home-office deduction isn't limited to business income.
    - Massachusetts clothing is fully taxable (the $175/item exemption isn't modeled).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from taximate.core.data_loader import TransactionRow

# Income category type constants
CATEGORY_FREELANCE = "Freelance (Tax Already Paid)"
CATEGORY_REVENUE_SALES_TAX_BUNDLED = "Revenue (Sales Tax Bundled)"
CATEGORY_REVENUE_SALES_TAX_APPLIED = "Revenue (Sales Tax Applied)"
CATEGORY_EXPENSES = "Business Expenses"

# Default US state when none is specified (keys into state_tax_rules.csv).
DEFAULT_STATE = "california"


@dataclass(frozen=True)
class DisplayRow:
    """A single row for the tax summary display table."""

    label: str
    value: float
    section: str  # "INCOME", "PROFIT", "TAXES", "SUMMARY"
    bold: bool = False
    negate: bool = False  # display value negated (expenses, deductions)
    is_section_header: bool = False


# tax_rates/ ships inside the package (src/python/taximate/tax_rates/), so the
# rates are found wherever taximate is installed, including in the browser wheel.
TAX_RATES_DIR = Path(__file__).resolve().parent.parent / "tax_rates"

# rate_type keys that rate_files.csv must map to a year-specific CSV. State
# income-tax brackets are resolved per state via state_tax_rules.csv instead.
_REQUIRED_RATE_FILES = frozenset({"federal_brackets", "self_employment", "sales_tax"})


def _read_rows(csv_path: Path) -> list[dict[str, str]]:
    """Read a trusted rate CSV into ``dict[str, str]`` rows (``csv.reader`` keeps values ``str`` for strict mypy)."""
    with csv_path.open(newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            return []
        return [dict(zip(header, record, strict=False)) for record in reader if record]


@dataclass
class TaxBracket:
    """Represents a single tax bracket."""

    rate: float
    min_income: float
    max_income: float | None  # None means no upper limit


@dataclass(frozen=True)
class StateTaxRules:
    """Per-state tax-base and sales-tax parameters, from ``state_tax_rules.csv``.

    ``se_deduction_cap`` None -> follow the federal half-of-SE-tax deduction (CA);
    a number -> deduct the full SE tax paid up to that cap (MA, $2,000).
    ``sales_tax_jurisdiction`` keys into the sales-tax CSV (via ``rate_files.csv``).
    """

    brackets_csv: str
    standard_deduction: float
    se_deduction_cap: float | None
    sales_tax_jurisdiction: str


@dataclass
class IncomeCategory:
    """Represents an income/expense category with associated items."""

    name: str
    description: str
    items: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class TaxInputs:
    """Category totals fed into a tax calculation."""

    all_tax_applied: float  # freelance income, taxes already withheld
    sales_tax_bundled: float  # revenue with sales tax included in the price
    sales_tax_applied: float  # revenue with sales tax collected separately
    expenses: float  # deductible business expenses (positive)
    deductions: float = 0.0  # manual deductions (home office, car)

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
    """Input values plus all computed tax amounts for one calculation."""

    all_tax_applied: float
    sales_tax_bundled: float
    sales_tax_applied: float
    expenses: float
    deductions: float

    sales_taxable: float  # bundled revenue after extracting sales tax
    sales_tax_rate: float
    sales_tax: float

    profit: float  # business_profit + freelance
    business_profit: float  # sales-taxable + applied revenue - expenses - deductions
    taxable_income: float  # federal base: business_profit - half the deductible SE tax

    sole_proprietor_tax: float  # SE tax (SS + Medicare + Additional Medicare)
    federal_income_tax: float
    state_income_tax: float
    total_income_tax: float  # SE + federal + state
    total_tax: float  # total_income_tax + sales tax

    take_home: float  # profit - total_income_tax
    gross_business_revenue: float
    gross_revenue: float  # gross_business_revenue + freelance

    def as_dict(self) -> dict[str, float]:
        """Convert results to a dictionary."""
        return self.__dict__

    def display_rows(self) -> list[DisplayRow]:
        """Return ordered display rows for the tax summary table."""
        return [
            DisplayRow("INCOME", 0.0, "INCOME", is_section_header=True),
            DisplayRow(CATEGORY_FREELANCE, self.all_tax_applied, "INCOME"),
            DisplayRow(CATEGORY_REVENUE_SALES_TAX_BUNDLED, self.sales_tax_bundled, "INCOME"),
            DisplayRow(CATEGORY_REVENUE_SALES_TAX_APPLIED, self.sales_tax_applied, "INCOME"),
            DisplayRow(CATEGORY_EXPENSES, self.expenses, "INCOME", negate=True),
            DisplayRow("Deductions", self.deductions, "INCOME", negate=True),
            DisplayRow("PROFIT", 0.0, "PROFIT", is_section_header=True),
            DisplayRow("Gross Revenue", self.gross_revenue, "PROFIT"),
            DisplayRow("Business Profit", self.business_profit, "PROFIT"),
            DisplayRow("Total Profit", self.profit, "PROFIT"),
            DisplayRow("Sales Taxable Income", self.sales_taxable, "PROFIT"),
            DisplayRow("Taxable Income", self.taxable_income, "PROFIT"),
            DisplayRow("TAXES", 0.0, "TAXES", is_section_header=True),
            DisplayRow(f"Sales Tax ({self.sales_tax_rate:.2%})", self.sales_tax, "TAXES"),
            DisplayRow("Self-Employment Tax", self.sole_proprietor_tax, "TAXES"),
            DisplayRow("Federal Income Tax", self.federal_income_tax, "TAXES"),
            DisplayRow("State Income Tax", self.state_income_tax, "TAXES"),
            DisplayRow("Total Income Tax", self.total_income_tax, "TAXES"),
            DisplayRow("Total Tax", self.total_tax, "TAXES"),
            DisplayRow("SUMMARY", 0.0, "SUMMARY", is_section_header=True),
            DisplayRow("TAKE HOME", self.take_home, "SUMMARY", bold=True),
        ]


@dataclass(frozen=True, slots=True)
class SummaryResult:
    """Result of generate_summary(), containing period and annual tax calculations."""

    tax_inputs: TaxInputs
    annual_inputs: TaxInputs
    period_taxes: TaxResults
    annual_taxes: TaxResults
    uncategorized_count: int


class TaxRates:
    """Load and manage tax rates from CSV files."""

    # Populated from the rate CSVs at construction; no hardcoded fallbacks.
    se_social_security_rate: float
    se_medicare_rate: float
    se_additional_medicare_rate: float
    se_additional_medicare_threshold: float
    se_wage_base: float
    se_income_factor: float
    sales_tax_rate: float

    def __init__(self, tax_rates_dir: Path = TAX_RATES_DIR, state: str = DEFAULT_STATE) -> None:
        self.tax_rates_dir = tax_rates_dir
        self.state = state
        self.federal_brackets: list[TaxBracket] = []
        self.state_brackets: list[TaxBracket] = []
        self.rate_files = self._load_rate_files()
        self.rules = self._load_state_rules()
        self._load_rates()

    def _load_rates(self) -> None:
        """Load all tax rates from CSV files."""
        self._load_federal_brackets()
        self._load_state_brackets()
        self._load_self_employment_rates()
        self._load_sales_tax_rates()

    def _require(self, filename: str) -> Path:
        """Resolve a bundled rate file; raise if absent (a missing file is a packaging error)."""
        csv_path = self.tax_rates_dir / filename
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Required tax-rate file {filename!r} not found in {self.tax_rates_dir} "
                "-- is it bundled in the wheel?"
            )
        return csv_path

    def _load_rate_files(self) -> dict[str, str]:
        """Map ``rate_type`` -> filename from ``rate_files.csv`` (keeps the tax year out of code)."""
        manifest_path = self._require("rate_files.csv")
        rate_files = {
            row["rate_type"]: row["csv"]
            for row in _read_rows(manifest_path)
            if row.get("rate_type")
        }
        missing = _REQUIRED_RATE_FILES - rate_files.keys()
        if missing:
            raise ValueError(
                f"rate_files.csv is missing required rate_type row(s): {sorted(missing)}"
            )
        return rate_files

    def _load_state_rules(self) -> StateTaxRules:
        """Look up the rules row for ``self.state``; raise if the state is unknown."""
        csv_path = self._require("state_tax_rules.csv")
        for row in _read_rows(csv_path):
            if row.get("state") == self.state:
                cap = row.get("se_deduction_cap", "").strip()
                return StateTaxRules(
                    brackets_csv=row["brackets_csv"],
                    standard_deduction=float(row["standard_deduction"]),
                    se_deduction_cap=float(cap) if cap else None,
                    sales_tax_jurisdiction=row["sales_tax_jurisdiction"],
                )
        raise ValueError(f"Unsupported state {self.state!r}; add a row to state_tax_rules.csv")

    def _load_brackets(self, csv_path: Path) -> list[TaxBracket]:
        """Parse single-filer progressive brackets from a rate CSV."""
        brackets: list[TaxBracket] = []
        for row in _read_rows(csv_path):
            if row.get("filing_status") != "single":
                continue
            max_income = row.get("max_income", "").strip()
            brackets.append(
                TaxBracket(
                    rate=float(row["rate"]),
                    min_income=float(row["min_income"]),
                    max_income=float(max_income) if max_income else None,
                )
            )
        return brackets

    def _load_federal_brackets(self) -> None:
        """Load federal income tax brackets (single filers)."""
        self.federal_brackets = self._load_brackets(
            self._require(self.rate_files["federal_brackets"])
        )

    def _load_state_brackets(self) -> None:
        """Load the selected state's income tax brackets (single filers)."""
        self.state_brackets = self._load_brackets(self._require(self.rules.brackets_csv))

    def _load_self_employment_rates(self) -> None:
        """Load SE tax rates (SS, Medicare, additional Medicare, factor); raise on a missing row."""
        csv_path = self._require(self.rate_files["self_employment"])
        rows = {row["tax_type"]: row for row in _read_rows(csv_path) if row.get("tax_type")}

        def _row(tax_type: str) -> dict[str, str]:
            if tax_type not in rows:
                raise ValueError(
                    f"self-employment rate file {csv_path.name!r} is missing the {tax_type!r} row"
                )
            return rows[tax_type]

        self.se_social_security_rate = float(_row("social_security")["rate"])
        self.se_wage_base = float(_row("social_security")["wage_base"])
        self.se_medicare_rate = float(_row("medicare")["rate"])
        self.se_additional_medicare_rate = float(_row("additional_medicare")["rate"])
        self.se_additional_medicare_threshold = float(_row("additional_medicare")["wage_base"])
        self.se_income_factor = float(_row("income_factor")["rate"])

    def _load_sales_tax_rates(self) -> None:
        """Load the sales tax rate for the selected state's jurisdiction."""
        csv_path = self._require(self.rate_files["sales_tax"])
        jurisdiction = self.rules.sales_tax_jurisdiction
        for row in _read_rows(csv_path):
            if row.get("jurisdiction") == jurisdiction:
                self.sales_tax_rate = float(row["rate"])
                return
        raise ValueError(
            f"Sales-tax jurisdiction {jurisdiction!r} (state {self.state!r}) not found "
            f"in {csv_path.name}"
        )

    def state_se_tax_deduction(self, net_earnings: float) -> float:
        """State-side SE-tax deduction.

        CA: half the deductible Schedule SE tax (SS + Medicare, excl. Additional Medicare).
        MA: full SE tax paid, capped at ``se_deduction_cap`` ($2,000).
        """
        cap = self.rules.se_deduction_cap
        if cap is None:
            return 0.5 * self.deductible_se_tax(net_earnings)
        return min(self.calculate_self_employment_tax(net_earnings), cap)

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

    def deductible_se_tax(self, net_earnings: float) -> float:
        """Schedule SE tax: SS + Medicare on 92.35% of net earnings.

        The half-deductible portion of SE tax; excludes the Additional Medicare Tax (Form 8959).
        """
        if net_earnings <= 0:
            return 0.0
        taxable_se_income = net_earnings * self.se_income_factor
        # Social Security (capped at the wage base) + Medicare (no cap).
        ss_tax = min(taxable_se_income, self.se_wage_base) * self.se_social_security_rate
        medicare_tax = taxable_se_income * self.se_medicare_rate
        return ss_tax + medicare_tax

    def additional_medicare_tax(self, net_earnings: float) -> float:
        """Additional Medicare Tax (Form 8959): 0.9% on the 92.35% amount over the threshold.

        Not part of Schedule SE and not deductible.
        """
        if net_earnings <= 0:
            return 0.0
        taxable_se_income = net_earnings * self.se_income_factor
        if taxable_se_income <= self.se_additional_medicare_threshold:
            return 0.0
        return (
            taxable_se_income - self.se_additional_medicare_threshold
        ) * self.se_additional_medicare_rate

    def calculate_self_employment_tax(self, net_earnings: float) -> float:
        """Total self-employment tax: Schedule SE (SS + Medicare) + Additional Medicare."""
        return self.deductible_se_tax(net_earnings) + self.additional_medicare_tax(net_earnings)


def supported_states(tax_rates_dir: Path = TAX_RATES_DIR) -> list[dict[str, str]]:
    """Supported states as ``{"value", "label"}`` rows from ``state_tax_rules.csv`` (source of truth for the UI picker)."""
    csv_path = tax_rates_dir / "state_tax_rules.csv"
    return [
        {"value": row["state"], "label": row.get("label") or row["state"].title()}
        for row in _read_rows(csv_path)
        if row.get("state")
    ]


class TaxCalculator:
    """Calculate taxes based on categorized transactions."""

    def __init__(self, tax_rates_dir: Path = TAX_RATES_DIR, state: str = DEFAULT_STATE) -> None:
        self.categories: dict[str, IncomeCategory] = {}
        self.item_to_category: dict[str, str] = {}
        self.tax_rates = TaxRates(tax_rates_dir, state=state)
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

    def _get_category_total(self, rows: list[TransactionRow], category_name: str) -> float:
        """Get the sum of amounts for a specific category."""
        if category_name not in self.categories:
            return 0.0

        items = set(self.categories[category_name].items)
        if not items:
            return 0.0

        return sum(row.amount for row in rows if row.item in items)

    def get_uncategorized_items(self, rows: list[TransactionRow]) -> list[str]:
        """Get list of items that haven't been categorized."""
        all_items = {row.item for row in rows}
        return sorted(all_items - set(self.item_to_category))

    def get_category_for_item(self, item: str) -> str | None:
        """Get the category name for an item."""
        return self.item_to_category.get(item)

    def calculate_taxes(self, inputs: TaxInputs) -> TaxResults:
        """Core tax calculator given category totals (already aggregated)."""
        # Extract the sales tax bundled into sales_tax_bundled prices.
        sales_taxable = inputs.sales_tax_bundled / (1 + self.tax_rates.sales_tax_rate)
        sales_tax = inputs.sales_tax_bundled - sales_taxable

        # Business profit: sales-taxable + applied revenue - expenses - deductions.
        total_deductible = inputs.expenses + inputs.deductions
        business_profit = sales_taxable + inputs.sales_tax_applied - total_deductible
        profit = business_profit + inputs.all_tax_applied

        sole_proprietor_tax = self.tax_rates.calculate_self_employment_tax(business_profit)

        # Federal base: business profit - half the deductible SE tax (SS + Medicare;
        # excludes Additional Medicare; no standard deduction).
        se_tax_deduction = 0.5 * self.tax_rates.deductible_se_tax(business_profit)
        taxable_income = max(0.0, business_profit - se_tax_deduction)

        # State base: business profit - state SE deduction - standard deduction.
        state_taxable_income = max(
            0.0,
            business_profit
            - self.tax_rates.state_se_tax_deduction(business_profit)
            - self.tax_rates.rules.standard_deduction,
        )

        federal_income_tax = self.tax_rates.calculate_bracket_tax(
            taxable_income, self.tax_rates.federal_brackets
        )
        state_income_tax = self.tax_rates.calculate_bracket_tax(
            state_taxable_income, self.tax_rates.state_brackets
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

    def extract_period_totals(self, rows: list[TransactionRow]) -> TaxInputs:
        return TaxInputs(
            all_tax_applied=self._get_category_total(rows, CATEGORY_FREELANCE),
            sales_tax_bundled=self._get_category_total(rows, CATEGORY_REVENUE_SALES_TAX_BUNDLED),
            sales_tax_applied=self._get_category_total(rows, CATEGORY_REVENUE_SALES_TAX_APPLIED),
            expenses=abs(self._get_category_total(rows, CATEGORY_EXPENSES)),
            deductions=self.manual_deductions,
        )

    def generate_summary(self, rows: list[TransactionRow], months: int = 12) -> SummaryResult:
        """Generate a complete tax summary with optional annualization."""
        # Collect all the data needed for calculation
        tax_inputs = self.extract_period_totals(rows)

        # project those values for a year
        annual_inputs = tax_inputs.annualized(months)

        # calculate current and annualized taxes
        period_taxes = self.calculate_taxes(tax_inputs)
        annual_taxes = self.calculate_taxes(annual_inputs)

        uncategorized_count = len(self.get_uncategorized_items(rows))

        return SummaryResult(
            tax_inputs=tax_inputs,
            annual_inputs=annual_inputs,
            period_taxes=period_taxes,
            annual_taxes=annual_taxes,
            uncategorized_count=uncategorized_count,
        )
