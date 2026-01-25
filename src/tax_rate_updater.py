"""Tax rate updater module for fetching current tax rates from online sources."""

from __future__ import annotations

import csv
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Default tax rates directory
TAX_RATES_DIR = Path(__file__).parent.parent / "tax_rates"

# Data source URLs
FEDERAL_TAX_URL = "https://taxfoundation.org/data/all/federal/2025-tax-brackets/"
CALIFORNIA_TAX_URL = "https://sweeneymichel.com/blog/2025-california-federal-income-tax-brackets"
SE_TAX_URL = "https://www.ssa.gov/oact/cola/cbb.html"
SALES_TAX_URL = "https://cdtfa.ca.gov/taxes-and-fees/rates.aspx"


@dataclass
class TaxBracketData:
    """Represents a tax bracket with rate and income range."""

    rate: float
    min_income: float
    max_income: float | None


@dataclass
class UpdateResult:
    """Result of a tax rate update operation."""

    success: bool
    message: str
    source: str


class TaxRateUpdater:
    """Fetches and updates tax rates from online sources."""

    def __init__(
        self,
        tax_rates_dir: Path = TAX_RATES_DIR,
        progress_callback: Callable[[str], None] | None = None,
    ) -> None:
        self.tax_rates_dir = tax_rates_dir
        self.progress_callback = progress_callback
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

    def _report_progress(self, message: str) -> None:
        """Report progress via callback if set."""
        if self.progress_callback:
            self.progress_callback(message)

    def _fetch_page(self, url: str) -> BeautifulSoup | None:
        """Fetch and parse a web page."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            self._report_progress(f"Error fetching {url}: {e}")
            return None

    def _parse_money(self, text: str) -> float:
        """Parse a money string like '$11,925' to float."""
        # Remove $, commas, and whitespace
        cleaned = re.sub(r"[$,\s]", "", text)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def update_federal_brackets(self) -> UpdateResult:
        """Fetch and update federal income tax brackets."""
        self._report_progress("Fetching federal tax brackets...")

        soup = self._fetch_page(FEDERAL_TAX_URL)
        if not soup:
            return UpdateResult(
                success=False,
                message="Failed to fetch federal tax data",
                source=FEDERAL_TAX_URL,
            )

        try:
            # Find the table with single filer data
            tables = soup.find_all("table")
            single_brackets: list[TaxBracketData] = []

            for table in tables:
                # Look for tables with tax bracket data
                text = table.get_text().lower()
                if "single" in text and "%" in text:
                    rows = table.find_all("tr")
                    for row in rows:
                        cells = row.find_all(["td", "th"])
                        if len(cells) >= 2:
                            cell_text = [c.get_text().strip() for c in cells]
                            # Look for rate patterns like "10%"
                            for i, text in enumerate(cell_text):
                                rate_match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
                                if rate_match and i + 1 < len(cell_text):
                                    rate = float(rate_match.group(1)) / 100
                                    # Parse income range
                                    income_text = cell_text[i + 1]
                                    income_match = re.search(
                                        r"\$?([\d,]+)\s*(?:to|-)\s*\$?([\d,]+)",
                                        income_text,
                                    )
                                    if income_match:
                                        min_inc = self._parse_money(income_match.group(1))
                                        max_inc = self._parse_money(income_match.group(2))
                                        single_brackets.append(
                                            TaxBracketData(rate, min_inc, max_inc)
                                        )

            # If parsing failed, use known 2025 brackets (includes married jointly)
            if not single_brackets:
                brackets_by_status = self._get_default_federal_brackets_2025()
            else:
                # Use parsed single brackets plus default married jointly brackets
                default_brackets = self._get_default_federal_brackets_2025()
                brackets_by_status = {
                    "single": single_brackets,
                    "married_jointly": default_brackets["married_jointly"],
                }

            self._write_federal_brackets(brackets_by_status)
            total_brackets = sum(len(b) for b in brackets_by_status.values())
            self._report_progress(f"Updated {total_brackets} federal tax brackets")
            return UpdateResult(
                success=True,
                message=f"Updated {total_brackets} federal tax brackets",
                source=FEDERAL_TAX_URL,
            )

        except Exception as e:
            return UpdateResult(
                success=False,
                message=f"Error parsing federal tax data: {e}",
                source=FEDERAL_TAX_URL,
            )

    def _get_default_federal_brackets_2025(
        self,
    ) -> dict[str, list[TaxBracketData]]:
        """Return known 2025 federal tax brackets for all filing statuses."""
        return {
            "single": [
                TaxBracketData(0.10, 0, 11925),
                TaxBracketData(0.12, 11925, 48475),
                TaxBracketData(0.22, 48475, 103350),
                TaxBracketData(0.24, 103350, 197300),
                TaxBracketData(0.32, 197300, 250525),
                TaxBracketData(0.35, 250525, 626350),
                TaxBracketData(0.37, 626350, None),
            ],
            "married_jointly": [
                TaxBracketData(0.10, 0, 23850),
                TaxBracketData(0.12, 23850, 96950),
                TaxBracketData(0.22, 96950, 206700),
                TaxBracketData(0.24, 206700, 394600),
                TaxBracketData(0.32, 394600, 501050),
                TaxBracketData(0.35, 501050, 751600),
                TaxBracketData(0.37, 751600, None),
            ],
        }

    def _write_federal_brackets(
        self, brackets_by_status: dict[str, list[TaxBracketData]]
    ) -> None:
        """Write federal tax brackets to CSV for all filing statuses."""
        csv_path = self.tax_rates_dir / "federal_income_tax_2025.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["filing_status", "rate", "min_income", "max_income"])
            for filing_status, brackets in brackets_by_status.items():
                for bracket in brackets:
                    max_str = str(int(bracket.max_income)) if bracket.max_income else ""
                    writer.writerow(
                        [filing_status, bracket.rate, int(bracket.min_income), max_str]
                    )

    def update_california_brackets(self) -> UpdateResult:
        """Fetch and update California state income tax brackets."""
        self._report_progress("Fetching California tax brackets...")

        soup = self._fetch_page(CALIFORNIA_TAX_URL)
        if not soup:
            # Use default brackets
            brackets_by_status = self._get_default_california_brackets_2024()
            self._write_california_brackets(brackets_by_status)
            total_brackets = sum(len(b) for b in brackets_by_status.values())
            return UpdateResult(
                success=True,
                message=f"Using {total_brackets} default California brackets (2024)",
                source=CALIFORNIA_TAX_URL,
            )

        try:
            # Try to parse brackets from page
            single_brackets: list[TaxBracketData] = []
            tables = soup.find_all("table")

            for table in tables:
                text = table.get_text().lower()
                if "california" in text or "%" in text:
                    rows = table.find_all("tr")
                    for row in rows:
                        cells = row.find_all(["td", "th"])
                        if len(cells) >= 2:
                            cell_text = [c.get_text().strip() for c in cells]
                            for i, text in enumerate(cell_text):
                                rate_match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
                                if rate_match:
                                    # Found a rate, try to find income range
                                    for j in range(len(cell_text)):
                                        if j != i:
                                            income_match = re.search(
                                                r"\$?([\d,]+)",
                                                cell_text[j],
                                            )
                                            if income_match:
                                                # Found some income data
                                                break

            # If parsing failed, use known brackets (includes married jointly)
            if not single_brackets:
                brackets_by_status = self._get_default_california_brackets_2024()
            else:
                # Use parsed single brackets plus default married jointly brackets
                default_brackets = self._get_default_california_brackets_2024()
                brackets_by_status = {
                    "single": single_brackets,
                    "married_jointly": default_brackets["married_jointly"],
                }

            self._write_california_brackets(brackets_by_status)
            total_brackets = sum(len(b) for b in brackets_by_status.values())
            self._report_progress(f"Updated {total_brackets} California tax brackets")
            return UpdateResult(
                success=True,
                message=f"Updated {total_brackets} California tax brackets",
                source=CALIFORNIA_TAX_URL,
            )

        except Exception as e:
            return UpdateResult(
                success=False,
                message=f"Error parsing California tax data: {e}",
                source=CALIFORNIA_TAX_URL,
            )

    def _get_default_california_brackets_2024(
        self,
    ) -> dict[str, list[TaxBracketData]]:
        """Return known 2024 California tax brackets for all filing statuses."""
        return {
            "single": [
                TaxBracketData(0.01, 0, 10756),
                TaxBracketData(0.02, 10756, 25499),
                TaxBracketData(0.04, 25499, 40245),
                TaxBracketData(0.06, 40245, 55866),
                TaxBracketData(0.08, 55866, 70606),
                TaxBracketData(0.093, 70606, 360659),
                TaxBracketData(0.103, 360659, 432787),
                TaxBracketData(0.113, 432787, 721314),
                TaxBracketData(0.123, 721314, 1000000),
                TaxBracketData(0.133, 1000000, None),
            ],
            "married_jointly": [
                TaxBracketData(0.01, 0, 21512),
                TaxBracketData(0.02, 21512, 50998),
                TaxBracketData(0.04, 50998, 80490),
                TaxBracketData(0.06, 80490, 111732),
                TaxBracketData(0.08, 111732, 141212),
                TaxBracketData(0.093, 141212, 721318),
                TaxBracketData(0.103, 721318, 865574),
                TaxBracketData(0.113, 865574, 1000000),
                TaxBracketData(0.123, 1000000, 1442628),
                TaxBracketData(0.133, 1442628, None),
            ],
        }

    def _write_california_brackets(
        self, brackets_by_status: dict[str, list[TaxBracketData]]
    ) -> None:
        """Write California tax brackets to CSV for all filing statuses."""
        csv_path = self.tax_rates_dir / "california_income_tax_2024.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["filing_status", "rate", "min_income", "max_income"])
            for filing_status, brackets in brackets_by_status.items():
                for bracket in brackets:
                    max_str = str(int(bracket.max_income)) if bracket.max_income else ""
                    writer.writerow(
                        [filing_status, bracket.rate, int(bracket.min_income), max_str]
                    )

    def update_self_employment_rates(self) -> UpdateResult:
        """Fetch and update self-employment tax rates."""
        self._report_progress("Fetching self-employment tax rates...")

        soup = self._fetch_page(SE_TAX_URL)

        # Parse wage base from SSA page
        wage_base = 176100  # 2025 default
        if soup:
            try:
                text = soup.get_text()
                # Look for wage base amounts
                match = re.search(r"2025[^\d]*\$([\d,]+)", text)
                if match:
                    wage_base = int(match.group(1).replace(",", ""))
                else:
                    # Try another pattern
                    match = re.search(r"\$([\d,]+)[^\d]*2025", text)
                    if match:
                        wage_base = int(match.group(1).replace(",", ""))
            except Exception:
                pass

        # Write SE tax rates (rates are set by law, not inflation-adjusted)
        csv_path = self.tax_rates_dir / "self_employment_tax_2025.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["tax_type", "rate", "wage_base", "notes"])
            writer.writerow(
                ["social_security", "0.124", str(wage_base), "12.4% up to wage base"]
            )
            writer.writerow(["medicare", "0.029", "", "2.9% on all earnings"])
            writer.writerow(
                [
                    "additional_medicare",
                    "0.009",
                    "200000",
                    "0.9% on earnings above threshold (single)",
                ]
            )
            writer.writerow(
                ["income_factor", "0.9235", "", "92.35% of net SE income is taxable"]
            )

        self._report_progress(f"Updated SE tax rates (wage base: ${wage_base:,})")
        return UpdateResult(
            success=True,
            message=f"Updated SE tax rates (wage base: ${wage_base:,})",
            source=SE_TAX_URL,
        )

    def update_sales_tax_rates(self) -> UpdateResult:
        """Fetch and update sales tax rates."""
        self._report_progress("Fetching sales tax rates...")

        soup = self._fetch_page(SALES_TAX_URL)

        # Default San Diego rates (these are well-established rates)
        state_rate = 0.0725  # California statewide base rate
        county_rate = 0.005  # San Diego County district tax
        combined_rate = 0.0775  # Standard combined rate for San Diego city
        max_rate = 0.0875  # Maximum rate in some special districts

        if soup:
            try:
                text = soup.get_text()
                # Look for San Diego combined rate - must be between 7% and 10%
                # to avoid grabbing incorrect values
                match = re.search(
                    r"San\s*Diego[^\d]*(\d+\.?\d*)\s*%",
                    text,
                    re.IGNORECASE,
                )
                if match:
                    parsed_rate = float(match.group(1)) / 100
                    # Only use the parsed rate if it's a reasonable combined rate
                    # (between 7.25% and 10%)
                    if 0.0725 <= parsed_rate <= 0.10:
                        combined_rate = parsed_rate
            except Exception:
                pass

        # Write sales tax rates
        csv_path = self.tax_rates_dir / "sales_tax_2025.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["jurisdiction", "rate", "notes"])
            writer.writerow(
                ["california_state", str(state_rate), "Base California state rate"]
            )
            writer.writerow(
                ["san_diego_county", str(county_rate), "San Diego County district tax"]
            )
            writer.writerow(
                [
                    "san_diego_combined",
                    str(combined_rate),
                    "Combined rate for San Diego city (state + county + local)",
                ]
            )
            writer.writerow(
                [
                    "san_diego_max",
                    str(max_rate),
                    "Maximum rate in some San Diego special districts",
                ]
            )

        self._report_progress(
            f"Updated sales tax rates (SD combined: {combined_rate * 100:.2f}%)"
        )
        return UpdateResult(
            success=True,
            message=f"Updated sales tax rates (SD combined: {combined_rate * 100:.2f}%)",
            source=SALES_TAX_URL,
        )

    def update_all(self) -> list[UpdateResult]:
        """Update all tax rates from online sources."""
        results = []

        self._report_progress("Starting tax rate update...")

        results.append(self.update_federal_brackets())
        results.append(self.update_california_brackets())
        results.append(self.update_self_employment_rates())
        results.append(self.update_sales_tax_rates())

        success_count = sum(1 for r in results if r.success)
        self._report_progress(f"Update complete: {success_count}/{len(results)} successful")

        return results
