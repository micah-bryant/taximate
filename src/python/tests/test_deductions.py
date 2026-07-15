"""Tests for taximate.core.deductions."""

import pytest

from taximate.core.deductions import (
    STANDARD_MILEAGE_RATE,
    car_actual_expense_deduction,
    car_standard_mileage_deduction,
    home_office_deduction,
    home_office_deduction_simplified,
)

# ---------------------------------------------------------------------------
# home_office_deduction
# ---------------------------------------------------------------------------


def test_home_office_deduction_basic() -> None:
    """Standard inputs produce the expected deduction."""
    result = home_office_deduction(
        rent=2000.0, utilities=100.0, insurance=50.0, office_pct=0.10, months=12
    )
    assert result == pytest.approx((2000.0 + 100.0 + 50.0) * 0.10 * 12)


def test_home_office_deduction_zero_pct() -> None:
    """Zero office percentage yields zero deduction."""
    result = home_office_deduction(
        rent=2000.0, utilities=100.0, insurance=50.0, office_pct=0.0, months=12
    )
    assert result == 0.0


def test_home_office_deduction_partial_year() -> None:
    """Deduction scales linearly with months."""
    full_year = home_office_deduction(
        rent=1500.0, utilities=200.0, insurance=100.0, office_pct=0.15, months=12
    )
    half_year = home_office_deduction(
        rent=1500.0, utilities=200.0, insurance=100.0, office_pct=0.15, months=6
    )
    assert full_year == pytest.approx(half_year * 2)


def test_home_office_simplified_basic() -> None:
    """$5/sq ft for a full year."""
    assert home_office_deduction_simplified(200.0, months=12) == pytest.approx(1000.0)


def test_home_office_simplified_caps_at_300_sqft() -> None:
    """Above 300 sq ft caps at the $1,500/yr maximum."""
    assert home_office_deduction_simplified(400.0, months=12) == pytest.approx(1500.0)


def test_home_office_simplified_prorates_by_months() -> None:
    """Prorated to the loaded period (annualizes back to the full-year value)."""
    assert home_office_deduction_simplified(300.0, months=6) == pytest.approx(750.0)


def test_home_office_simplified_negative_sqft() -> None:
    """Negative square footage yields zero."""
    assert home_office_deduction_simplified(-50.0, months=12) == 0.0


# ---------------------------------------------------------------------------
# car_standard_mileage_deduction
# ---------------------------------------------------------------------------


def test_car_standard_mileage_deduction_zero() -> None:
    """Zero miles yields zero deduction."""
    assert car_standard_mileage_deduction(0.0) == 0.0


def test_car_standard_mileage_deduction_known_value() -> None:
    """1,000 miles at the standard rate."""
    result = car_standard_mileage_deduction(1000.0)
    assert result == pytest.approx(1000.0 * STANDARD_MILEAGE_RATE)


# ---------------------------------------------------------------------------
# car_actual_expense_deduction
# ---------------------------------------------------------------------------


def test_car_actual_expense_deduction_zero_total_miles() -> None:
    """Zero total miles returns 0.0 without division error."""
    result = car_actual_expense_deduction(business_miles=500.0, total_miles=0.0, car_cost=30000.0)
    assert result == 0.0


def test_car_actual_expense_deduction_full_business_use() -> None:
    """100% business use deducts the full car cost."""
    result = car_actual_expense_deduction(
        business_miles=10000.0, total_miles=10000.0, car_cost=25000.0
    )
    assert result == pytest.approx(25000.0)


def test_car_actual_expense_deduction_half_business_use() -> None:
    """50% business use deducts half the car cost."""
    result = car_actual_expense_deduction(
        business_miles=5000.0, total_miles=10000.0, car_cost=20000.0
    )
    assert result == pytest.approx(10000.0)
