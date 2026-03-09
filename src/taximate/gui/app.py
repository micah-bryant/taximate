"""PySide6 GUI for Taximate tax calculation application.

This module provides the main graphical user interface for Taximate, featuring:
- Modern styled interface with color-coded buttons and hover effects
- Drag-and-drop CSV file loading
- Multi-file selection via file browser dialog
- Transaction item categorization with visual feedback
- Deduction calculators for home office and car expenses
- Real-time tax calculation with side-by-side period/annual comparison
- Version display from package metadata

The GUI uses a three-panel layout:
- Left: Transaction items list with category indicators
- Center: Category assignment controls and category contents
- Right: Tax calculation summary with deduction buttons and period/annualized columns

Styling:
    The interface uses a modern color scheme with:
    - Primary (blue): Default action buttons
    - Secondary (gray): Alternative actions
    - Success (green): Positive actions (assign, calculate)
    - Danger (red): Destructive actions (clear data)

Disclaimer:
    This application is for informational purposes only and does not constitute
    financial, tax, or legal advice. Consult a qualified tax professional.

Functions:
    get_version: Get package version from metadata.
    run_app: Create and launch the application.

Classes:
    DropZone: Drag-and-drop area for CSV files.
    HomeOfficeDeductionDialog: Calculator for home office deduction.
    CarDeductionDialog: Calculator for car/vehicle deduction.
    TaximateGUI: Main application window.
"""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, override

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from taximate.core.data_loader import get_unique_values, load_csvs_from_paths
from taximate.core.tax_calculator import SummaryResult, TaxCalculator
from taximate.gui._dialogs import CarDeductionDialog, HomeOfficeDeductionDialog
from taximate.gui._styles import COLORS, STYLESHEET

if TYPE_CHECKING:
    from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QMouseEvent


def get_version() -> str:
    """Get the package version, defaulting to 'dev' if not installed."""
    try:
        return version("taximate")
    except PackageNotFoundError:
        return "dev"


class DropZone(QLabel):
    """A label that accepts drag-and-drop of CSV files."""

    DEFAULT_STYLE = f"""
        QLabel {{
            background-color: {COLORS["surface"]};
            border: 2px dashed {COLORS["border"]};
            border-radius: 8px;
            color: {COLORS["text_muted"]};
            font-weight: 500;
        }}
    """

    HOVER_STYLE = f"""
        QLabel {{
            background-color: #eff6ff;
            border: 2px dashed {COLORS["primary"]};
            border-radius: 8px;
            color: {COLORS["primary"]};
            font-weight: 500;
        }}
    """

    def __init__(self, parent: TaximateGUI) -> None:
        super().__init__("Drop CSV files here\nor click Browse")
        self.parent_gui = parent
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(220, 56)
        self.setStyleSheet(self.DEFAULT_STYLE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @override
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accept drag events with file URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self.HOVER_STYLE)
            self.setText("Release to load files")

    @override
    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """Reset appearance when drag leaves."""
        del event  # unused
        self._reset_style()

    @override
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle dropped files."""
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".csv"):
                files.append(path)

        if files:
            self.parent_gui._load_files(files)
        else:
            QMessageBox.warning(self, "Warning", "No CSV files found in dropped items")

        self._reset_style()

    def _reset_style(self) -> None:
        """Reset to default appearance."""
        self.setText("Drop CSV files here\nor click Browse")
        self.setStyleSheet(self.DEFAULT_STYLE)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle click to browse files."""
        del event  # unused
        self.parent_gui._browse_files()


class TaximateGUI(QWidget):
    """Main GUI window for the Taximate application.

    Provides a graphical interface for loading CSV transaction files,
    categorizing items into income/expense types, and calculating
    self-employment taxes with annual projections.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Taximate - Tax Calculator")
        self.resize(1250, 750)

        self.df: pd.DataFrame | None = None
        self.calculator = TaxCalculator()
        self.loaded_files: list[str] = []

        self._create_widgets()
        self._on_category_selected()

    def _create_widgets(self) -> None:
        """Create all GUI widgets."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Top bar - Drop zone and buttons
        top_layout = QHBoxLayout()

        self.drop_zone = DropZone(self)
        top_layout.addWidget(self.drop_zone)

        self.browse_btn = QPushButton("Browse Files")
        self.browse_btn.setObjectName("secondaryButton")
        self.browse_btn.clicked.connect(self._browse_files)
        top_layout.addWidget(self.browse_btn)

        self.clear_btn = QPushButton("Clear Data")
        self.clear_btn.setObjectName("dangerButton")
        self.clear_btn.clicked.connect(self._clear_data)
        top_layout.addWidget(self.clear_btn)

        self.status_label = QLabel("No data loaded")
        top_layout.addWidget(self.status_label)
        top_layout.addStretch()

        main_layout.addLayout(top_layout)

        # Main content area - three panels
        content_layout = QHBoxLayout()

        # Left panel - Items list
        left_group = QGroupBox("Transaction Items")
        left_layout = QVBoxLayout(left_group)

        self.items_list = QListWidget()
        self.items_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.items_list.setMinimumWidth(320)
        left_layout.addWidget(self.items_list)

        content_layout.addWidget(left_group)

        # Middle panel - Category assignment
        middle_layout = QVBoxLayout()

        cat_group = QGroupBox("Assign to Category")
        cat_layout = QVBoxLayout(cat_group)

        self.category_combo = QComboBox()
        self.category_combo.addItems(list(self.calculator.categories.keys()))
        self.category_combo.currentTextChanged.connect(self._on_category_selected)
        cat_layout.addWidget(self.category_combo)

        self.category_desc_label = QLabel()
        self.category_desc_label.setWordWrap(True)
        self.category_desc_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        self.category_desc_label.setMaximumWidth(280)
        cat_layout.addWidget(self.category_desc_label)

        self.assign_btn = QPushButton("Assign Selected Items")
        self.assign_btn.setObjectName("successButton")
        self.assign_btn.clicked.connect(self._assign_items)
        cat_layout.addWidget(self.assign_btn)

        self.unassign_btn = QPushButton("Remove from Category")
        self.unassign_btn.setObjectName("secondaryButton")
        self.unassign_btn.clicked.connect(self._unassign_items)
        cat_layout.addWidget(self.unassign_btn)

        middle_layout.addWidget(cat_group)

        # Category contents
        contents_group = QGroupBox("Category Contents")
        contents_layout = QVBoxLayout(contents_group)

        self.category_contents = QTextEdit()
        self.category_contents.setReadOnly(True)
        self.category_contents.setMinimumWidth(280)
        contents_layout.addWidget(self.category_contents)

        middle_layout.addWidget(contents_group, 1)
        content_layout.addLayout(middle_layout)

        # Right panel - Results
        right_group = QGroupBox("Tax Summary")
        right_layout = QVBoxLayout(right_group)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["", "Period", "Annual"])
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.results_table.setMinimumWidth(480)
        self.results_table.verticalHeader().setVisible(False)
        # All columns stretch to fill available space
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.results_table)

        # Uncategorized items display
        self.uncategorized_label = QLabel()
        self.uncategorized_label.setWordWrap(True)
        self.uncategorized_label.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 8px;")
        right_layout.addWidget(self.uncategorized_label)

        # Deductions buttons
        deductions_layout = QHBoxLayout()

        self.home_office_btn = QPushButton("Home Office...")
        self.home_office_btn.setObjectName("secondaryButton")
        self.home_office_btn.clicked.connect(self._show_home_office_dialog)
        deductions_layout.addWidget(self.home_office_btn)

        self.car_deduction_btn = QPushButton("Car Deduction...")
        self.car_deduction_btn.setObjectName("secondaryButton")
        self.car_deduction_btn.clicked.connect(self._show_car_deduction_dialog)
        deductions_layout.addWidget(self.car_deduction_btn)

        deductions_layout.addStretch()
        right_layout.addLayout(deductions_layout)

        # Deduction display label
        self.deduction_label = QLabel("No deductions applied")
        self.deduction_label.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 4px;")
        right_layout.addWidget(self.deduction_label)

        # Months input and calculate button
        calc_layout = QHBoxLayout()

        calc_layout.addWidget(QLabel("Months of data:"))

        self.months_spinbox = QSpinBox()
        self.months_spinbox.setRange(1, 12)
        self.months_spinbox.setValue(12)
        self.months_spinbox.setFixedWidth(55)
        calc_layout.addWidget(self.months_spinbox)

        self.calc_btn = QPushButton("Calculate Taxes")
        self.calc_btn.setObjectName("successButton")
        self.calc_btn.clicked.connect(self._calculate_taxes)
        calc_layout.addWidget(self.calc_btn)

        calc_layout.addStretch()
        right_layout.addLayout(calc_layout)

        content_layout.addWidget(right_group, 1)

        main_layout.addLayout(content_layout, 1)

        # Version label at bottom
        version_label = QLabel(f"Taximate v{get_version()}")
        version_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(version_label)

    def _browse_files(self) -> None:
        """Open file dialog to select CSV files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select CSV Files",
            "",
            "CSV Files (*.csv);;All Files (*.*)",
        )
        if files:
            self._load_files(files)

    def _load_files(self, file_paths: list[str]) -> None:
        """Load CSV files from the given paths."""
        try:
            new_df = load_csvs_from_paths(file_paths)

            if self.df is not None:
                existing_sources = set(self.df["source_file"].unique())
                new_sources = set(new_df["source_file"].unique())
                truly_new = new_sources - existing_sources

                if truly_new:
                    new_rows = new_df[new_df["source_file"].isin(truly_new)]
                    self.df = pd.concat([self.df, new_rows], ignore_index=True)
                    self.loaded_files.extend(
                        [f for f in file_paths if any(s in f for s in truly_new)]
                    )
            else:
                self.df = new_df
                self.loaded_files = list(file_paths)

            self._update_items_list()
            self._update_status()

        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")

    def _clear_data(self) -> None:
        """Clear all loaded data."""
        self.df = None
        self.loaded_files = []
        self.items_list.clear()
        self.status_label.setText("No data loaded")
        self.drop_zone._reset_style()

    def _update_items_list(self) -> None:
        """Update the items list with current data."""
        if self.df is None:
            return

        items = get_unique_values(self.df, "Item")
        self.items_list.clear()

        for item in items:
            category = self.calculator.get_category_for_item(item)
            display_text = f"{item} [{category}]" if category else item
            self.items_list.addItem(QListWidgetItem(display_text))

    def _update_status(self) -> None:
        """Update the status label with current data info."""
        if self.df is None:
            self.status_label.setText("No data loaded")
            return

        row_count = len(self.df)
        file_count = len(self.loaded_files)
        items = get_unique_values(self.df, "Item")
        self.status_label.setText(
            f"Loaded {file_count} file(s), {row_count} transactions, {len(items)} unique items"
        )

    def _assign_items(self) -> None:
        """Assign selected items to the chosen category."""
        selected_items = self.items_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select items to assign")
            return

        category = self.category_combo.currentText()
        if not category:
            QMessageBox.warning(self, "Warning", "Please select a category")
            return

        for list_item in selected_items:
            item = list_item.text()
            if " [" in item:
                item = item.rsplit(" [", 1)[0]
            self.calculator.assign_item_to_category(item, category)

        self._update_category_contents()
        self._update_items_list()

    def _unassign_items(self) -> None:
        """Remove selected items from their categories."""
        selected_items = self.items_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select items to remove")
            return

        for list_item in selected_items:
            item = list_item.text()
            if " [" in item:
                item = item.rsplit(" [", 1)[0]
            self.calculator.remove_item_from_category(item)

        self._update_category_contents()
        self._update_items_list()

    def _on_category_selected(self) -> None:
        """Handle category selection - update description and contents."""
        category = self.category_combo.currentText()
        if category and category in self.calculator.categories:
            desc = self.calculator.categories[category].description
            self.category_desc_label.setText(desc)
        else:
            self.category_desc_label.setText("")
        self._update_category_contents()

    def _update_category_contents(self) -> None:
        """Update the category contents display."""
        category = self.category_combo.currentText()
        if not category or category not in self.calculator.categories:
            return

        cat = self.calculator.categories[category]
        self.category_contents.clear()

        if cat.items:
            self.category_contents.append(f"Items in {category}:\n")
            for item in cat.items:
                self.category_contents.append(f"  - {item}")
        else:
            self.category_contents.setPlainText("No items assigned")

    def _show_home_office_dialog(self) -> None:
        """Show the home office deduction calculator dialog."""
        months = self.months_spinbox.value()
        dialog = HomeOfficeDeductionDialog(self, months)

        if dialog.exec():
            self.calculator.home_office_deduction = dialog.get_deduction()
            self._update_deduction_label()

    def _show_car_deduction_dialog(self) -> None:
        """Show the car deduction calculator dialog."""
        months = self.months_spinbox.value()
        dialog = CarDeductionDialog(self, months)

        if dialog.exec():
            self.calculator.car_deduction = dialog.get_deduction()
            self._update_deduction_label()

    def _update_deduction_label(self) -> None:
        """Update the deduction label with current deductions."""
        deductions = []
        if self.calculator.home_office_deduction > 0:
            deductions.append(f"Home Office: ${self.calculator.home_office_deduction:,.2f}")
        if self.calculator.car_deduction > 0:
            deductions.append(f"Car: ${self.calculator.car_deduction:,.2f}")

        if deductions:
            total = self.calculator.manual_deductions
            text = " | ".join(deductions)
            if len(deductions) > 1:
                text += f" | Total: ${total:,.2f}"
            self.deduction_label.setText(text)
            self.deduction_label.setStyleSheet(
                f"color: {COLORS['success']}; font-weight: 500; padding: 4px;"
            )
        else:
            self.deduction_label.setText("No deductions applied")
            self.deduction_label.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 4px;")

    def _calculate_taxes(self) -> None:
        """Calculate and display tax summary in table format."""
        if self.df is None:
            QMessageBox.warning(self, "Warning", "Please load data first")
            return

        months = self.months_spinbox.value()

        summary: SummaryResult = self.calculator.generate_summary(self.df, months)
        period_rows = summary.period_taxes.display_rows()
        annual_rows = summary.annual_taxes.display_rows()

        # Update header labels with months
        self.results_table.setHorizontalHeaderLabels(
            ["", f"Period ({months} mo)", "Annual (12 mo)"]
        )

        self.results_table.setRowCount(len(period_rows))

        for row_idx, (p_row, a_row) in enumerate(zip(period_rows, annual_rows, strict=True)):
            # Label column
            label_item = QTableWidgetItem(p_row.label)
            if p_row.is_section_header:
                label_item.setBackground(self.results_table.palette().alternateBase())
                font = label_item.font()
                font.setBold(True)
                label_item.setFont(font)
            elif p_row.bold:
                font = label_item.font()
                font.setBold(True)
                label_item.setFont(font)
            self.results_table.setItem(row_idx, 0, label_item)

            if not p_row.is_section_header:
                # Period column
                p_val = -p_row.value if p_row.negate else p_row.value
                period_item = QTableWidgetItem(f"${p_val:,.2f}")
                period_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                if p_row.bold:
                    font = period_item.font()
                    font.setBold(True)
                    period_item.setFont(font)
                self.results_table.setItem(row_idx, 1, period_item)

                # Annual column
                a_val = -a_row.value if a_row.negate else a_row.value
                annual_item = QTableWidgetItem(f"${a_val:,.2f}")
                annual_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                if a_row.bold:
                    font = annual_item.font()
                    font.setBold(True)
                    annual_item.setFont(font)
                self.results_table.setItem(row_idx, 2, annual_item)

        # Show uncategorized items
        uncategorized = self.calculator.get_uncategorized_items(self.df)
        if uncategorized:
            items_text = ", ".join(uncategorized[:6])
            if len(uncategorized) > 6:
                items_text += f", +{len(uncategorized) - 6} more"
            self.uncategorized_label.setText(f"Uncategorized ({len(uncategorized)}): {items_text}")
        else:
            self.uncategorized_label.setText("")


def run_app() -> None:
    """Create and run the application."""
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = TaximateGUI()
    window.show()
    sys.exit(app.exec())
