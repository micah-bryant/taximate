"""Deduction formulas: home office (regular + simplified) and car (standard-mileage, actual-expense)."""

from __future__ import annotations

STANDARD_MILEAGE_RATE: float = 0.725  # 2026 IRS business rate per mile (update each tax year)

# IRS simplified home-office method: $5/sq ft, up to 300 sq ft ($1,500/yr max).
SIMPLIFIED_HOME_OFFICE_RATE: float = 5.0
SIMPLIFIED_HOME_OFFICE_MAX_SQFT: float = 300.0


def home_office_deduction(
    rent: float,
    utilities: float,
    insurance: float,
    office_pct: float,
    months: int,
) -> float:
    """Regular home-office deduction for the period: (rent + utilities + insurance) x office_pct x months.

    Monthly amounts; ``office_pct`` is 0.0-1.0.
    """
    return (rent + utilities + insurance) * office_pct * months


def home_office_deduction_simplified(square_feet: float, months: int = 12) -> float:
    """Simplified home-office deduction, prorated to the period.

    $5/sq ft up to 300 sq ft ($1,500/yr max), times ``months / 12`` for a partial period.
    """
    capped_sqft = min(max(square_feet, 0.0), SIMPLIFIED_HOME_OFFICE_MAX_SQFT)
    return capped_sqft * SIMPLIFIED_HOME_OFFICE_RATE * months / 12


def car_standard_mileage_deduction(business_miles: float) -> float:
    """Car deduction via the IRS standard mileage rate."""
    return business_miles * STANDARD_MILEAGE_RATE


def car_actual_expense_deduction(
    business_miles: float,
    total_miles: float,
    car_cost: float,
) -> float:
    """Car deduction via the actual-expense method: business share of total car cost. 0.0 if total_miles is 0."""
    if total_miles == 0:
        return 0.0
    return (business_miles / total_miles) * car_cost
