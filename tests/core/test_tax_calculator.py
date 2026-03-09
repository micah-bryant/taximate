"""Tests for taximate.core.tax_calculator."""

from pathlib import Path

import pytest

from taximate.core.tax_calculator import (
    DisplayRow,
    SummaryResult,
    TaxCalculator,
    TaxInputs,
    TaxRates,
    TaxResults,
)

# ---------------------------------------------------------------------------
# TaxRates loading
# ---------------------------------------------------------------------------


def test_tax_rates_loads_without_error(tax_rates_dir: Path) -> None:
    rates = TaxRates(tax_rates_dir)
    assert len(rates.federal_brackets) > 0
    assert len(rates.state_brackets) > 0
    assert rates.sales_tax_rate > 0
    assert rates.se_social_security_rate > 0


def test_tax_rates_sales_tax_rate(tax_rates_dir: Path) -> None:
    rates = TaxRates(tax_rates_dir)
    assert rates.sales_tax_rate == pytest.approx(0.0775)


def test_tax_rates_se_wage_base(tax_rates_dir: Path) -> None:
    rates = TaxRates(tax_rates_dir)
    assert rates.se_wage_base == pytest.approx(176100)


# ---------------------------------------------------------------------------
# calculate_bracket_tax
# ---------------------------------------------------------------------------


def test_bracket_tax_zero_income(tax_rates_dir: Path) -> None:
    rates = TaxRates(tax_rates_dir)
    assert rates.calculate_bracket_tax(0, rates.federal_brackets) == 0.0


def test_bracket_tax_negative_income(tax_rates_dir: Path) -> None:
    rates = TaxRates(tax_rates_dir)
    assert rates.calculate_bracket_tax(-1000, rates.federal_brackets) == 0.0


def test_bracket_tax_below_first_bracket(tax_rates_dir: Path) -> None:
    """Income of $5,000 should be taxed at the first bracket rate (10%)."""
    rates = TaxRates(tax_rates_dir)
    # First federal bracket: 10% from $0 to $11,925
    tax = rates.calculate_bracket_tax(5000, rates.federal_brackets)
    assert tax == pytest.approx(5000 * 0.10, rel=1e-4)


def test_bracket_tax_spanning_brackets(tax_rates_dir: Path) -> None:
    """Income of $20,000 should span first two federal brackets."""
    rates = TaxRates(tax_rates_dir)
    # 10% on first $11,925 = $1,192.50; 12% on remainder = ($20,000 - $11,925) * 0.12
    tax = rates.calculate_bracket_tax(20000, rates.federal_brackets)
    expected = 11925 * 0.10 + (20000 - 11925) * 0.12
    assert tax == pytest.approx(expected, rel=1e-4)


def test_bracket_tax_top_bracket(tax_rates_dir: Path) -> None:
    """Very high income should hit the top bracket."""
    rates = TaxRates(tax_rates_dir)
    tax = rates.calculate_bracket_tax(700000, rates.federal_brackets)
    # Top bracket is 37%, so tax must be well above 37% of last chunk
    assert tax > 200000  # sanity: $700k generates substantial tax


# ---------------------------------------------------------------------------
# calculate_self_employment_tax
# ---------------------------------------------------------------------------


def test_se_tax_zero(tax_rates_dir: Path) -> None:
    rates = TaxRates(tax_rates_dir)
    assert rates.calculate_self_employment_tax(0) == 0.0


def test_se_tax_below_wage_base(tax_rates_dir: Path) -> None:
    """$50,000 net earnings: all subject to SS + medicare."""
    rates = TaxRates(tax_rates_dir)
    net = 50000.0
    taxable = net * rates.se_income_factor
    expected_ss = taxable * rates.se_social_security_rate
    expected_mc = taxable * rates.se_medicare_rate
    result = rates.calculate_self_employment_tax(net)
    assert result == pytest.approx(expected_ss + expected_mc, rel=1e-4)


def test_se_tax_above_wage_base(tax_rates_dir: Path) -> None:
    """$250,000 net earnings: SS portion capped at wage base."""
    rates = TaxRates(tax_rates_dir)
    net = 250000.0
    taxable = net * rates.se_income_factor
    ss_tax = rates.se_wage_base * rates.se_social_security_rate
    mc_tax = taxable * rates.se_medicare_rate
    result = rates.calculate_self_employment_tax(net)
    # result should be >= ss_tax + mc_tax (might have additional Medicare)
    assert result >= ss_tax + mc_tax - 0.01  # allow tiny float tolerance


# ---------------------------------------------------------------------------
# TaxInputs.annualized
# ---------------------------------------------------------------------------


def test_tax_inputs_annualized_12_months() -> None:
    """12 months → no change."""
    inputs = TaxInputs(
        all_tax_applied=1000.0,
        sales_tax_bundled=2000.0,
        sales_tax_applied=500.0,
        expenses=300.0,
        deductions=100.0,
    )
    ann = inputs.annualized(12)
    assert ann.all_tax_applied == pytest.approx(1000.0)
    assert ann.sales_tax_bundled == pytest.approx(2000.0)
    assert ann.expenses == pytest.approx(300.0)


def test_tax_inputs_annualized_6_months() -> None:
    """6 months → values doubled."""
    inputs = TaxInputs(
        all_tax_applied=1000.0,
        sales_tax_bundled=2000.0,
        sales_tax_applied=500.0,
        expenses=300.0,
        deductions=100.0,
    )
    ann = inputs.annualized(6)
    assert ann.all_tax_applied == pytest.approx(2000.0)
    assert ann.sales_tax_bundled == pytest.approx(4000.0)
    assert ann.deductions == pytest.approx(200.0)


def test_tax_inputs_annualized_3_months() -> None:
    """3 months → values multiplied by 4."""
    inputs = TaxInputs(
        all_tax_applied=1000.0,
        sales_tax_bundled=0.0,
        sales_tax_applied=0.0,
        expenses=600.0,
    )
    ann = inputs.annualized(3)
    assert ann.all_tax_applied == pytest.approx(4000.0)
    assert ann.expenses == pytest.approx(2400.0)


# ---------------------------------------------------------------------------
# TaxCalculator end-to-end
# ---------------------------------------------------------------------------


def test_tax_calculator_calculate_taxes_zero_income(tax_rates_dir: Path) -> None:
    calc = TaxCalculator(tax_rates_dir)
    inputs = TaxInputs(
        all_tax_applied=0.0,
        sales_tax_bundled=0.0,
        sales_tax_applied=0.0,
        expenses=0.0,
    )
    results = calc.calculate_taxes(inputs)
    assert results.sole_proprietor_tax == 0.0
    assert results.federal_income_tax == 0.0
    assert results.state_income_tax == 0.0
    assert results.total_tax == 0.0


def test_tax_calculator_calculate_taxes_known_inputs(tax_rates_dir: Path) -> None:
    """Provide fixed inputs and verify output fields are consistent."""
    calc = TaxCalculator(tax_rates_dir)
    inputs = TaxInputs(
        all_tax_applied=5000.0,
        sales_tax_bundled=10770.0,  # ~$10k + bundled sales tax
        sales_tax_applied=0.0,
        expenses=2000.0,
    )
    results = calc.calculate_taxes(inputs)
    assert isinstance(results, TaxResults)
    assert results.sole_proprietor_tax > 0
    assert results.federal_income_tax > 0
    assert results.state_income_tax > 0
    assert results.total_income_tax == pytest.approx(
        results.sole_proprietor_tax + results.federal_income_tax + results.state_income_tax
    )
    assert results.total_tax == pytest.approx(results.total_income_tax + results.sales_tax)
    assert results.sales_tax_rate == pytest.approx(0.0775)


def test_tax_calculator_calculate_taxes_expenses_reduce_tax(tax_rates_dir: Path) -> None:
    """Higher expenses should result in lower taxes."""
    calc = TaxCalculator(tax_rates_dir)
    base_inputs = TaxInputs(
        all_tax_applied=0.0,
        sales_tax_bundled=0.0,
        sales_tax_applied=50000.0,
        expenses=0.0,
    )
    high_expense_inputs = TaxInputs(
        all_tax_applied=0.0,
        sales_tax_bundled=0.0,
        sales_tax_applied=50000.0,
        expenses=10000.0,
    )
    base_result = calc.calculate_taxes(base_inputs)
    high_result = calc.calculate_taxes(high_expense_inputs)
    assert high_result.total_income_tax < base_result.total_income_tax


def test_tax_calculator_generate_summary_returns_summary_result(tax_rates_dir: Path) -> None:
    """generate_summary returns a SummaryResult with correct typed attributes."""

    from taximate.core.data_loader import load_csvs_from_paths
    from taximate.core.tax_calculator import CATEGORY_REVENUE_SALES_TAX_APPLIED

    data_dir = tax_rates_dir.parent / "data"
    csv_files = list(data_dir.glob("*.csv"))
    assert csv_files

    df = load_csvs_from_paths(csv_files)
    calc = TaxCalculator(tax_rates_dir)

    items = df["Item"].unique()[:2].tolist()
    for item in items:
        calc.assign_item_to_category(item, CATEGORY_REVENUE_SALES_TAX_APPLIED)

    summary = calc.generate_summary(df, months=12)
    assert isinstance(summary, SummaryResult)
    assert isinstance(summary.tax_inputs, TaxInputs)
    assert isinstance(summary.annual_inputs, TaxInputs)
    assert isinstance(summary.period_taxes, TaxResults)
    assert isinstance(summary.annual_taxes, TaxResults)
    assert isinstance(summary.uncategorized_count, int)


# ---------------------------------------------------------------------------
# TaxResults.display_rows
# ---------------------------------------------------------------------------


def test_display_rows_returns_list_of_display_row(tax_rates_dir: Path) -> None:
    calc = TaxCalculator(tax_rates_dir)
    inputs = TaxInputs(
        all_tax_applied=1000.0,
        sales_tax_bundled=2000.0,
        sales_tax_applied=500.0,
        expenses=300.0,
    )
    results = calc.calculate_taxes(inputs)
    rows = results.display_rows()
    assert isinstance(rows, list)
    assert all(isinstance(r, DisplayRow) for r in rows)


def test_display_rows_count(tax_rates_dir: Path) -> None:
    calc = TaxCalculator(tax_rates_dir)
    inputs = TaxInputs(
        all_tax_applied=0.0, sales_tax_bundled=0.0, sales_tax_applied=10000.0, expenses=0.0
    )
    rows = calc.calculate_taxes(inputs).display_rows()
    assert len(rows) == 21


def test_display_rows_section_headers_present(tax_rates_dir: Path) -> None:
    calc = TaxCalculator(tax_rates_dir)
    inputs = TaxInputs(
        all_tax_applied=0.0, sales_tax_bundled=0.0, sales_tax_applied=10000.0, expenses=0.0
    )
    rows = calc.calculate_taxes(inputs).display_rows()
    header_sections = {r.section for r in rows if r.is_section_header}
    assert header_sections == {"INCOME", "PROFIT", "TAXES", "SUMMARY"}


def test_display_rows_take_home_is_bold(tax_rates_dir: Path) -> None:
    calc = TaxCalculator(tax_rates_dir)
    inputs = TaxInputs(
        all_tax_applied=0.0, sales_tax_bundled=0.0, sales_tax_applied=10000.0, expenses=0.0
    )
    rows = calc.calculate_taxes(inputs).display_rows()
    take_home = next(r for r in rows if r.label == "TAKE HOME")
    assert take_home.bold is True


def test_display_rows_expenses_negate_flag(tax_rates_dir: Path) -> None:
    calc = TaxCalculator(tax_rates_dir)
    inputs = TaxInputs(
        all_tax_applied=0.0, sales_tax_bundled=0.0, sales_tax_applied=10000.0, expenses=500.0
    )
    rows = calc.calculate_taxes(inputs).display_rows()
    expenses_row = next(r for r in rows if "Expenses" in r.label)
    assert expenses_row.negate is True
    assert expenses_row.value > 0


def test_tax_calculator_period_vs_annual(tax_rates_dir: Path) -> None:
    """For 6-month data, annual taxes should be ~2x period taxes."""
    calc = TaxCalculator(tax_rates_dir)
    inputs = TaxInputs(
        all_tax_applied=0.0,
        sales_tax_bundled=0.0,
        sales_tax_applied=30000.0,
        expenses=5000.0,
    )
    ann_inputs = inputs.annualized(6)
    period_results = calc.calculate_taxes(inputs)
    annual_results = calc.calculate_taxes(ann_inputs)
    # Annual income is 2x, so taxes should be higher (not necessarily 2x due to brackets)
    assert annual_results.total_income_tax > period_results.total_income_tax
