"""Deduction calculator dialogs for the Taximate GUI."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from taximate.core.deductions import (
    STANDARD_MILEAGE_RATE,
    car_actual_expense_deduction,
    car_standard_mileage_deduction,
    home_office_deduction,
)
from taximate.gui._styles import COLORS


class HomeOfficeDeductionDialog(QDialog):
    """Dialog for calculating home office deduction."""

    def __init__(self, parent: QWidget | None = None, months: int = 12) -> None:
        super().__init__(parent)
        self.setWindowTitle("Home Office Deduction Calculator")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.months = months
        self._calculated_deduction: float = 0.0

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Description
        desc_label = QLabel(
            "Calculate your home office deduction based on the percentage of "
            "your home used for business and your monthly housing expenses."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(desc_label)

        # Form layout for inputs
        form_group = QGroupBox("Monthly Expenses")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(16, 20, 16, 16)

        # Office percentage
        self.percentage_spinbox = QDoubleSpinBox()
        self.percentage_spinbox.setRange(0, 100)
        self.percentage_spinbox.setValue(10)
        self.percentage_spinbox.setSuffix("%")
        self.percentage_spinbox.setDecimals(1)
        self.percentage_spinbox.setMinimumHeight(32)
        self.percentage_spinbox.valueChanged.connect(self._update_calculation)
        form_layout.addRow("Office Space Percentage:", self.percentage_spinbox)

        # Monthly rent
        self.rent_spinbox = QDoubleSpinBox()
        self.rent_spinbox.setRange(0, 99999.99)
        self.rent_spinbox.setPrefix("$")
        self.rent_spinbox.setDecimals(2)
        self.rent_spinbox.setMinimumHeight(32)
        self.rent_spinbox.valueChanged.connect(self._update_calculation)
        form_layout.addRow("Monthly Rent:", self.rent_spinbox)

        # Monthly utilities
        self.utilities_spinbox = QDoubleSpinBox()
        self.utilities_spinbox.setRange(0, 9999.99)
        self.utilities_spinbox.setPrefix("$")
        self.utilities_spinbox.setDecimals(2)
        self.utilities_spinbox.setMinimumHeight(32)
        self.utilities_spinbox.valueChanged.connect(self._update_calculation)
        form_layout.addRow("Monthly Utilities:", self.utilities_spinbox)

        # Monthly insurance
        self.insurance_spinbox = QDoubleSpinBox()
        self.insurance_spinbox.setRange(0, 9999.99)
        self.insurance_spinbox.setPrefix("$")
        self.insurance_spinbox.setDecimals(2)
        self.insurance_spinbox.setMinimumHeight(32)
        self.insurance_spinbox.valueChanged.connect(self._update_calculation)
        form_layout.addRow("Monthly Insurance:", self.insurance_spinbox)

        layout.addWidget(form_group)

        # Calculation result display
        self.result_label = QLabel()
        self.result_label.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {COLORS['primary']}; "
            "padding: 16px; background-color: #eff6ff; border-radius: 6px;"
        )
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setMinimumHeight(60)
        layout.addWidget(self.result_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("Apply Deduction")
        apply_btn.setObjectName("successButton")
        apply_btn.setMinimumWidth(120)
        apply_btn.clicked.connect(self.accept)
        button_layout.addWidget(apply_btn)

        layout.addLayout(button_layout)

        self._update_calculation()

    def _update_calculation(self) -> None:
        """Update the calculated deduction based on current inputs."""
        office_pct = self.percentage_spinbox.value() / 100
        rent = self.rent_spinbox.value()
        utilities = self.utilities_spinbox.value()
        insurance = self.insurance_spinbox.value()
        monthly_deduction = (rent + utilities + insurance) * office_pct
        self._calculated_deduction = home_office_deduction(
            rent, utilities, insurance, office_pct, self.months
        )

        self.result_label.setText(
            f"Monthly Deduction: ${monthly_deduction:,.2f}\n"
            f"Period Deduction ({self.months} mo): ${self._calculated_deduction:,.2f}"
        )

    def get_deduction(self) -> float:
        """Return the calculated deduction amount."""
        return self._calculated_deduction


class CarDeductionDialog(QDialog):
    """Dialog for calculating car/vehicle deduction."""

    def __init__(self, parent: QWidget | None = None, months: int = 12) -> None:
        super().__init__(parent)
        self.setWindowTitle("Car Deduction Calculator")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.months = months
        self._calculated_deduction: float = 0.0

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Description
        desc_label = QLabel(
            "Choose a deduction method: Standard Mileage Rate "
            f"(${STANDARD_MILEAGE_RATE:.2f}/mile) or Actual Expenses "
            "(business use percentage of car cost)."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(desc_label)

        # Method selection with radio buttons
        self.method_group = QButtonGroup(self)

        # Standard mileage option
        self.standard_group = QGroupBox()
        standard_header = QVBoxLayout(self.standard_group)
        standard_header.setContentsMargins(16, 16, 16, 16)
        standard_header.setSpacing(16)

        self.standard_radio = QRadioButton("Standard Mileage Rate")
        self.standard_radio.setChecked(True)
        self.standard_radio.setStyleSheet("font-weight: 600;")
        self.method_group.addButton(self.standard_radio, 0)
        standard_header.addWidget(self.standard_radio)

        standard_form = QFormLayout()
        standard_form.setSpacing(12)
        self.business_miles_spinbox = QDoubleSpinBox()
        self.business_miles_spinbox.setRange(0, 999999)
        self.business_miles_spinbox.setSuffix(" miles")
        self.business_miles_spinbox.setDecimals(0)
        self.business_miles_spinbox.setMinimumHeight(32)
        self.business_miles_spinbox.valueChanged.connect(self._update_calculation)
        standard_form.addRow("Business Miles Driven:", self.business_miles_spinbox)
        standard_header.addLayout(standard_form)

        layout.addWidget(self.standard_group)

        # Actual expense option
        self.actual_group = QGroupBox()
        actual_header = QVBoxLayout(self.actual_group)
        actual_header.setContentsMargins(16, 16, 16, 16)
        actual_header.setSpacing(16)

        self.actual_radio = QRadioButton("Actual Expenses")
        self.actual_radio.setStyleSheet("font-weight: 600;")
        self.method_group.addButton(self.actual_radio, 1)
        actual_header.addWidget(self.actual_radio)

        actual_form = QFormLayout()
        actual_form.setSpacing(12)

        self.total_miles_spinbox = QDoubleSpinBox()
        self.total_miles_spinbox.setRange(0, 999999)
        self.total_miles_spinbox.setSuffix(" miles")
        self.total_miles_spinbox.setDecimals(0)
        self.total_miles_spinbox.setMinimumHeight(32)
        self.total_miles_spinbox.valueChanged.connect(self._update_calculation)
        actual_form.addRow("Total Miles Driven:", self.total_miles_spinbox)

        self.actual_business_miles_spinbox = QDoubleSpinBox()
        self.actual_business_miles_spinbox.setRange(0, 999999)
        self.actual_business_miles_spinbox.setSuffix(" miles")
        self.actual_business_miles_spinbox.setDecimals(0)
        self.actual_business_miles_spinbox.setMinimumHeight(32)
        self.actual_business_miles_spinbox.valueChanged.connect(self._update_calculation)
        actual_form.addRow("Business Miles Driven:", self.actual_business_miles_spinbox)

        self.car_cost_spinbox = QDoubleSpinBox()
        self.car_cost_spinbox.setRange(0, 999999.99)
        self.car_cost_spinbox.setPrefix("$")
        self.car_cost_spinbox.setDecimals(2)
        self.car_cost_spinbox.setMinimumHeight(32)
        self.car_cost_spinbox.valueChanged.connect(self._update_calculation)
        actual_form.addRow("Cost of Car:", self.car_cost_spinbox)

        actual_header.addLayout(actual_form)
        layout.addWidget(self.actual_group)

        # Connect radio buttons
        self.standard_radio.toggled.connect(self._on_method_changed)
        self.actual_radio.toggled.connect(self._on_method_changed)

        # Calculation result display
        self.result_label = QLabel()
        self.result_label.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {COLORS['primary']}; "
            "padding: 16px; background-color: #eff6ff; border-radius: 6px;"
        )
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setMinimumHeight(60)
        layout.addWidget(self.result_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("Apply Deduction")
        apply_btn.setObjectName("successButton")
        apply_btn.setMinimumWidth(120)
        apply_btn.clicked.connect(self.accept)
        button_layout.addWidget(apply_btn)

        layout.addLayout(button_layout)

        self._on_method_changed()
        self._update_calculation()

    def _on_method_changed(self) -> None:
        """Handle method selection change - enable/disable input groups."""
        is_standard = self.standard_radio.isChecked()
        self.business_miles_spinbox.setEnabled(is_standard)
        self.total_miles_spinbox.setEnabled(not is_standard)
        self.actual_business_miles_spinbox.setEnabled(not is_standard)
        self.car_cost_spinbox.setEnabled(not is_standard)
        self._update_calculation()

    def _update_calculation(self) -> None:
        """Update the calculated deduction based on current inputs."""
        if self.standard_radio.isChecked():
            business_miles = self.business_miles_spinbox.value()
            self._calculated_deduction = car_standard_mileage_deduction(business_miles)
            self.result_label.setText(
                f"{business_miles:,.0f} miles * ${STANDARD_MILEAGE_RATE:.2f}/mile\n"
                f"Deduction: ${self._calculated_deduction:,.2f}"
            )
        else:
            total_miles = self.total_miles_spinbox.value()
            business_miles = self.actual_business_miles_spinbox.value()
            car_cost = self.car_cost_spinbox.value()
            self._calculated_deduction = car_actual_expense_deduction(
                business_miles, total_miles, car_cost
            )

            if total_miles > 0:
                business_percentage = business_miles / total_miles
                self.result_label.setText(
                    f"Business Use: {business_percentage * 100:.1f}% "
                    f"({business_miles:,.0f} / {total_miles:,.0f} miles)\n"
                    f"Deduction: ${self._calculated_deduction:,.2f}"
                )
            else:
                self.result_label.setText("Enter total miles to calculate")

    def get_deduction(self) -> float:
        """Return the calculated deduction amount."""
        return self._calculated_deduction
