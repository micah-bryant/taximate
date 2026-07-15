"""Golden correctness tests with independently-derived expected values.

Unlike ``test_tax_calculator.py`` -- which recomputes each expectation from the
engine's own ``rates.*`` attributes and would therefore silently track a mistyped
rate -- every expected value here is derived BY HAND from a primary source and
hardcoded. A wrong number in the rate CSVs makes these fail.

When the rate CSVs are updated for a new tax year, RE-DERIVE these numbers from
the newly published schedule. Do not copy them from the engine's output; copying
the output back into the test would defeat the entire point of an independent
check.

Primary sources:
- Self-employment tax: 2026 Schedule SE / Form 8959 -- Social Security 12.4% up to
  the $184,500 wage base (SSA), Medicare 2.9% (uncapped), additional Medicare 0.9%
  on the 92.35% amount over $200,000 (single; statutory, not indexed), 92.35% factor.
- Federal income tax: 2026 single schedule (IRS Rev. Proc. 2025-32, reflecting OBBBA).
- California income tax: 2025 FTB single schedule (1%-13.3%, where the 1% surcharge
  over $1,000,000 makes the top effectively 13.3%); standard deduction $5,706
  (ftb.ca.gov). 2026 CA schedules are not yet published; 2025 is the latest.
- Massachusetts income tax: 2026 -- 5% flat + 4% surtax over $1,107,750; personal
  exemption $4,400; SE-tax deduction = full SE tax paid capped at $2,000 (mass.gov).
- Sales tax: San Diego combined 7.75%; Massachusetts 6.25% statewide (no local).
"""

from pathlib import Path

import pytest

from taximate.core.tax_calculator import TaxCalculator, TaxInputs, TaxRates

# Tighter than a cent. Float noise from these calculations is on the order of
# 1e-9, while a real rate error is dollars or more, so this catches regressions
# without ever flaking.
TOL = 1e-4


# ---------------------------------------------------------------------------
# Self-employment tax -- 2026 Schedule SE / Form 8959 (SS wage base $184,500)
# ---------------------------------------------------------------------------

# (net_earnings, expected_se_tax)
_SE_CASES: list[tuple[float, float]] = [
    # Zero (or negative) earnings owe nothing.
    (0.0, 0.0),
    # Below the wage base and below the additional-Medicare threshold:
    #   taxable 50000*.9235 = 46175; SS 46175*.124 = 5725.70;
    #   Medicare 46175*.029 = 1339.075.
    (50000.0, 7064.775),
    # Above the 2026 wage base ($184,500) but taxable (184700) still below the $200k
    # addl threshold: SS capped 184500*.124 = 22878.00; Medicare 184700*.029 = 5356.30.
    (200000.0, 28234.30),
    # Above BOTH the wage-base cap and the additional-Medicare threshold:
    #   SS 22878.00; Medicare 277050*.029 = 8034.45;
    #   additional (277050-200000)*.009 = 693.45.
    (300000.0, 31605.90),
]


@pytest.mark.parametrize(("net_earnings", "expected"), _SE_CASES)
def test_se_tax_golden(tax_rates_dir: Path, net_earnings: float, expected: float) -> None:
    rates = TaxRates(tax_rates_dir)
    assert rates.calculate_self_employment_tax(net_earnings) == pytest.approx(expected, abs=TOL)


# ---------------------------------------------------------------------------
# Federal income tax -- 2026 single schedule (IRS Rev. Proc. 2025-32)
# ---------------------------------------------------------------------------

# (taxable_income, expected_federal_tax)
_FEDERAL_CASES: list[tuple[float, float]] = [
    # 12400*.10 + 37600*.12 (50000 is within the 12% bracket, below 50400)
    (50000.0, 5752.00),
    # 12400*.10 + 38000*.12 + 49600*.22
    (100000.0, 16712.00),
    # All seven brackets, through the 37% top rate.
    (700000.0, 214957.25),
]


@pytest.mark.parametrize(("income", "expected"), _FEDERAL_CASES)
def test_federal_bracket_golden(tax_rates_dir: Path, income: float, expected: float) -> None:
    rates = TaxRates(tax_rates_dir)
    assert rates.calculate_bracket_tax(income, rates.federal_brackets) == pytest.approx(
        expected, abs=TOL
    )


# ---------------------------------------------------------------------------
# California income tax -- 2025 FTB single schedule
# ---------------------------------------------------------------------------

# (taxable_income, expected_ca_tax)
_CALIFORNIA_CASES: list[tuple[float, float]] = [
    # 110.79 + 303.70 + 607.52 + 512.88
    (50000.0, 1534.89),
    # ...+ 965.40 + 1214.56 + 27276*.093
    (100000.0, 5738.638),
    # Crosses $1,000,000 into the effective 13.3% top rate.
    (1100000.0, 117136.608),
]


@pytest.mark.parametrize(("income", "expected"), _CALIFORNIA_CASES)
def test_california_bracket_golden(tax_rates_dir: Path, income: float, expected: float) -> None:
    rates = TaxRates(tax_rates_dir, state="california")
    assert rates.calculate_bracket_tax(income, rates.state_brackets) == pytest.approx(
        expected, abs=TOL
    )


# ---------------------------------------------------------------------------
# Massachusetts income tax -- 2026 (5% flat + 4% surtax over $1,107,750)
# ---------------------------------------------------------------------------

# (taxable_income, expected_ma_tax)
_MASSACHUSETTS_CASES: list[tuple[float, float]] = [
    # Flat 5% below the surtax threshold.
    (50000.0, 2500.00),
    # Exactly at the 2026 threshold: still flat 5%, no surtax yet.
    (1107750.0, 55387.50),
    # Above the threshold: 5% on all + 4% surtax on the excess
    #   1107750*.05 + 92250*.09 = 55387.50 + 8302.50
    (1200000.0, 63690.00),
]


@pytest.mark.parametrize(("income", "expected"), _MASSACHUSETTS_CASES)
def test_massachusetts_bracket_golden(tax_rates_dir: Path, income: float, expected: float) -> None:
    rates = TaxRates(tax_rates_dir, state="massachusetts")
    assert rates.calculate_bracket_tax(income, rates.state_brackets) == pytest.approx(
        expected, abs=TOL
    )


# ---------------------------------------------------------------------------
# Sales-tax back-calculation -- San Diego 7.75% / Massachusetts 6.25%
# ---------------------------------------------------------------------------


def test_sales_tax_backcalc_golden(tax_rates_dir: Path) -> None:
    """Bundled $10,775 at 7.75% -> $10,000 net + $775.00 tax (10000 * 1.0775 = 10775)."""
    calc = TaxCalculator(tax_rates_dir, state="california")
    results = calc.calculate_taxes(
        TaxInputs(
            all_tax_applied=0.0,
            sales_tax_bundled=10775.0,
            sales_tax_applied=0.0,
            expenses=0.0,
        )
    )
    assert results.sales_taxable == pytest.approx(10000.0, abs=TOL)
    assert results.sales_tax == pytest.approx(775.0, abs=TOL)
    assert results.sales_tax_rate == pytest.approx(0.0775, abs=TOL)


def test_massachusetts_sales_tax_backcalc_golden(tax_rates_dir: Path) -> None:
    """Bundled $10,625 at MA 6.25% -> $10,000 net + $625.00 tax (10000 * 1.0625 = 10625)."""
    calc = TaxCalculator(tax_rates_dir, state="massachusetts")
    results = calc.calculate_taxes(
        TaxInputs(
            all_tax_applied=0.0,
            sales_tax_bundled=10625.0,
            sales_tax_applied=0.0,
            expenses=0.0,
        )
    )
    assert results.sales_tax_rate == pytest.approx(0.0625, abs=TOL)
    assert results.sales_taxable == pytest.approx(10000.0, abs=TOL)
    assert results.sales_tax == pytest.approx(625.0, abs=TOL)


# ---------------------------------------------------------------------------
# End-to-end composition -- California
# ---------------------------------------------------------------------------


def test_end_to_end_california_golden(tax_rates_dir: Path) -> None:
    """Full pipeline, hand-derived end to end.

    Inputs: $100,000 of sales-tax-applied revenue and $20,000 of expenses (no
    bundled revenue, no freelance income, no manual deductions). The CA state
    base subtracts CA's 2025 standard deduction ($5,706); the federal base does not.

        business_profit  = 100000 - 20000                          = 80,000.00
        SE tax on 80000  : taxable 73880; SS 9161.12; MC 2142.52   = 11,303.64
        federal taxable  = 80000 - 11303.64/2                      = 74,348.18
        federal (2026)   = 1240.00 + 4560.00 + 23948.18*.22        = 11,068.5996
        CA state taxable = 80000 - 11303.64/2 - 5706               = 68,642.18
        california (2025)= 110.79+303.70+607.52+965.40+11100.18*.08 = 2,875.4244
        total_income_tax = 11303.64 + 11068.5996 + 2875.4244       = 25,247.664
        take_home        = 80000 - 25247.664                       = 54,752.336
    """
    calc = TaxCalculator(tax_rates_dir, state="california")
    results = calc.calculate_taxes(
        TaxInputs(
            all_tax_applied=0.0,
            sales_tax_bundled=0.0,
            sales_tax_applied=100000.0,
            expenses=20000.0,
        )
    )
    assert results.business_profit == pytest.approx(80000.0, abs=TOL)
    assert results.sole_proprietor_tax == pytest.approx(11303.64, abs=TOL)
    assert results.taxable_income == pytest.approx(74348.18, abs=TOL)
    assert results.federal_income_tax == pytest.approx(11068.5996, abs=TOL)
    assert results.state_income_tax == pytest.approx(2875.4244, abs=TOL)
    assert results.total_tax == pytest.approx(25247.664, abs=TOL)
    assert results.take_home == pytest.approx(54752.336, abs=TOL)


# ---------------------------------------------------------------------------
# End-to-end composition -- California high earner (additional-Medicare split)
# ---------------------------------------------------------------------------


def test_end_to_end_california_high_earner_golden(tax_rates_dir: Path) -> None:
    """High earner (>$216.6k SE profit): the 0.9% Additional Medicare Tax is charged
    but is NOT deductible, so the half-SE deduction uses only the Schedule SE tax
    (SS + Medicare). Cross-checked against OpenTaxSolver / PolicyEngine.

        SE tax total     = 22878.00 + 8034.45 + 693.45            = 31,605.90
        deductible SE    = 22878.00 + 8034.45                     = 30,912.45
        federal taxable  = 300000 - 30912.45/2                    = 284,543.775
        federal (2026)   = ...(top span 28318.775*.35)            = 68,359.57125
        CA state taxable = 284543.775 - 5706                       = 278,837.775
        california (2025)= 3201.97 + 206113.775*.093              = 22,370.551075
        take_home        = 300000 - (31605.90+68359.57125+22370.55) = 177,663.977675
    """
    calc = TaxCalculator(tax_rates_dir, state="california")
    results = calc.calculate_taxes(
        TaxInputs(
            all_tax_applied=0.0,
            sales_tax_bundled=0.0,
            sales_tax_applied=300000.0,
            expenses=0.0,
        )
    )
    assert results.business_profit == pytest.approx(300000.0, abs=TOL)
    assert results.sole_proprietor_tax == pytest.approx(31605.90, abs=TOL)
    assert results.taxable_income == pytest.approx(284543.775, abs=TOL)
    assert results.federal_income_tax == pytest.approx(68359.57125, abs=TOL)
    assert results.state_income_tax == pytest.approx(22370.551075, abs=TOL)
    assert results.take_home == pytest.approx(177663.977675, abs=TOL)


# ---------------------------------------------------------------------------
# End-to-end composition -- Massachusetts
# ---------------------------------------------------------------------------


def test_end_to_end_massachusetts_golden(tax_rates_dir: Path) -> None:
    """Same inputs as the California end-to-end case, but with the MA base.

    Federal figures (SE tax, federal taxable, federal tax) are state-independent
    and identical to the California case; only the state base + rate differ:

        MA state taxable = 80000 - min(11303.64, 2000) - 4400     = 73,600.00
        massachusetts    = 73600 * .05                            =  3,680.00
        total_income_tax = 11303.64 + 11068.5996 + 3680.00        = 26,052.2396
        take_home        = 80000 - 26052.2396                     = 53,947.7604
    """
    calc = TaxCalculator(tax_rates_dir, state="massachusetts")
    results = calc.calculate_taxes(
        TaxInputs(
            all_tax_applied=0.0,
            sales_tax_bundled=0.0,
            sales_tax_applied=100000.0,
            expenses=20000.0,
        )
    )
    assert results.sole_proprietor_tax == pytest.approx(11303.64, abs=TOL)
    assert results.taxable_income == pytest.approx(74348.18, abs=TOL)
    assert results.federal_income_tax == pytest.approx(11068.5996, abs=TOL)
    assert results.state_income_tax == pytest.approx(3680.00, abs=TOL)
    assert results.total_tax == pytest.approx(26052.2396, abs=TOL)
    assert results.take_home == pytest.approx(53947.7604, abs=TOL)
