"""Pure deduction calculation functions for Taximate.

These functions are intentionally free of GUI dependencies so they can be
unit-tested without Qt.
"""

from __future__ import annotations

STANDARD_MILEAGE_RATE: float = 0.70  # IRS rate per mile (update each tax year)


def home_office_deduction(
    rent: float,
    utilities: float,
    insurance: float,
    office_pct: float,
    months: int,
) -> float:
    """Calculate total home office deduction for the period.

    Args:
        rent: Monthly rent amount.
        utilities: Monthly utilities amount.
        insurance: Monthly insurance amount.
        office_pct: Office percentage (0.0-1.0).
        months: Number of months in the period.

    Returns:
        Total deduction for the period.
    """
    return (rent + utilities + insurance) * office_pct * months


def car_standard_mileage_deduction(business_miles: float) -> float:
    """Calculate car deduction using the IRS standard mileage rate.

    Args:
        business_miles: Miles driven for business purposes.

    Returns:
        Deduction amount.
    """
    return business_miles * STANDARD_MILEAGE_RATE


def car_actual_expense_deduction(
    business_miles: float,
    total_miles: float,
    car_cost: float,
) -> float:
    """Calculate car deduction using the actual expense method.

    Args:
        business_miles: Miles driven for business purposes.
        total_miles: Total miles driven (all purposes).
        car_cost: Total cost of the car.

    Returns:
        Deduction amount (0.0 if total_miles is zero).
    """
    if total_miles == 0:
        return 0.0
    return (business_miles / total_miles) * car_cost
