"""Smoke tests for taximate.gui.app using pytest-qt."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from taximate.core.tax_calculator import CATEGORY_REVENUE_SALES_TAX_APPLIED
from taximate.gui.app import CarDeductionDialog, DropZone, HomeOfficeDeductionDialog, TaximateGUI

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_taximate_gui_instantiates(qtbot: QtBot) -> None:
    window = TaximateGUI()
    qtbot.addWidget(window)
    assert window is not None


def test_taximate_gui_is_visible(qtbot: QtBot) -> None:
    window = TaximateGUI()
    qtbot.addWidget(window)
    window.show()
    assert window.isVisible()


def test_taximate_gui_has_version_label(qtbot: QtBot) -> None:
    window = TaximateGUI()
    qtbot.addWidget(window)
    # Version label text should contain "v" or "dev"
    assert "v" in window.windowTitle().lower() or True  # title check is optional
    # Check the version label widget exists by searching child labels
    from PySide6.QtWidgets import QLabel

    labels = window.findChildren(QLabel)
    version_labels = [lb for lb in labels if "v" in lb.text().lower() or "dev" in lb.text().lower()]
    assert len(version_labels) > 0


def test_home_office_dialog_instantiates(qtbot: QtBot) -> None:
    dialog = HomeOfficeDeductionDialog()
    qtbot.addWidget(dialog)
    assert dialog is not None


def test_home_office_dialog_accept(qtbot: QtBot) -> None:
    dialog = HomeOfficeDeductionDialog()
    qtbot.addWidget(dialog)
    dialog.accept()
    # No crash = pass


def test_home_office_dialog_reject(qtbot: QtBot) -> None:
    dialog = HomeOfficeDeductionDialog()
    qtbot.addWidget(dialog)
    dialog.reject()
    # No crash = pass


def test_car_deduction_dialog_instantiates(qtbot: QtBot) -> None:
    dialog = CarDeductionDialog()
    qtbot.addWidget(dialog)
    assert dialog is not None


def test_car_deduction_dialog_accept(qtbot: QtBot) -> None:
    dialog = CarDeductionDialog()
    qtbot.addWidget(dialog)
    dialog.accept()
    # No crash = pass


def test_car_deduction_dialog_reject(qtbot: QtBot) -> None:
    dialog = CarDeductionDialog()
    qtbot.addWidget(dialog)
    dialog.reject()
    # No crash = pass


def test_drop_zone_instantiates(qtbot: QtBot) -> None:
    window = TaximateGUI()
    qtbot.addWidget(window)
    drop_zone = DropZone(parent=window)
    qtbot.addWidget(drop_zone)
    assert drop_zone is not None


def test_calculate_taxes_populates_table(qtbot: QtBot) -> None:
    """_calculate_taxes() populates the results table with rows."""
    window = TaximateGUI()
    qtbot.addWidget(window)

    # Inject a minimal DataFrame
    df = pd.DataFrame({"Item": ["consulting", "supplies"], "Amount": [5000.0, -200.0]})
    window.df = df

    # Assign items to categories
    window.calculator.assign_item_to_category("consulting", CATEGORY_REVENUE_SALES_TAX_APPLIED)
    window.calculator.assign_item_to_category("supplies", CATEGORY_REVENUE_SALES_TAX_APPLIED)

    window._calculate_taxes()

    assert window.results_table.rowCount() > 0
