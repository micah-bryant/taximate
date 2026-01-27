"""PySide6 GUI for Taximate tax calculation application.

This module provides the main graphical user interface for Taximate, featuring:
- Modern styled interface with color-coded buttons and hover effects
- Drag-and-drop CSV file loading
- Multi-file selection via file browser dialog
- Transaction item categorization with visual feedback
- Real-time tax calculation with side-by-side period/annual comparison
- Version display from package metadata

The GUI uses a three-panel layout:
- Left: Transaction items list with category indicators
- Center: Category assignment controls and category contents
- Right: Tax calculation summary with period and annualized columns

Styling:
    The interface uses a modern color scheme with:
    - Primary (blue): Default action buttons
    - Secondary (gray): Alternative actions
    - Success (green): Positive actions (assign, calculate)
    - Danger (red): Destructive actions (clear data)

Functions:
    get_version: Get package version from metadata.
    run_app: Create and launch the application.

Classes:
    DropZone: Drag-and-drop area for CSV files.
    TaximateGUI: Main application window.
"""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version

import pandas as pd


def get_version() -> str:
    """Get the package version, defaulting to 'dev' if not installed."""
    try:
        return version("taximate")
    except PackageNotFoundError:
        return "dev"


from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
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

from .data_loader import get_unique_values, load_csvs_from_paths
from .tax_calculator import TaxCalculator, TaxResults

# Modern color scheme based on Tailwind CSS color palette
COLORS: dict[str, str] = {
    "primary": "#2563eb",  # Blue
    "primary_hover": "#1d4ed8",
    "primary_pressed": "#1e40af",
    "secondary": "#64748b",  # Slate
    "secondary_hover": "#475569",
    "success": "#16a34a",  # Green
    "success_hover": "#15803d",
    "danger": "#dc2626",  # Red
    "background": "#f8fafc",
    "surface": "#ffffff",
    "border": "#e2e8f0",
    "text": "#1e293b",
    "text_muted": "#64748b",
}

# Qt stylesheet for modern widget appearance with hover/pressed states
STYLESHEET: str = f"""
    QWidget {{
        background-color: {COLORS["background"]};
        color: {COLORS["text"]};
        font-family: "Segoe UI", "SF Pro Display", system-ui, sans-serif;
        font-size: 13px;
    }}

    QPushButton {{
        background-color: {COLORS["primary"]};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
    }}

    QPushButton:hover {{
        background-color: {COLORS["primary_hover"]};
    }}

    QPushButton:pressed {{
        background-color: {COLORS["primary_pressed"]};
    }}

    QPushButton:disabled {{
        background-color: {COLORS["border"]};
        color: {COLORS["text_muted"]};
    }}

    QPushButton#secondaryButton {{
        background-color: {COLORS["surface"]};
        color: {COLORS["text"]};
        border: 1px solid {COLORS["border"]};
    }}

    QPushButton#secondaryButton:hover {{
        background-color: {COLORS["background"]};
        border-color: {COLORS["secondary"]};
    }}

    QPushButton#dangerButton {{
        background-color: {COLORS["danger"]};
    }}

    QPushButton#dangerButton:hover {{
        background-color: #b91c1c;
    }}

    QPushButton#successButton {{
        background-color: {COLORS["success"]};
    }}

    QPushButton#successButton:hover {{
        background-color: {COLORS["success_hover"]};
    }}

    QGroupBox {{
        background-color: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        margin-top: 12px;
        padding: 12px;
        font-weight: 600;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0 8px;
        color: {COLORS["text"]};
        background-color: {COLORS["surface"]};
    }}

    QListWidget {{
        background-color: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        padding: 4px;
        outline: none;
    }}

    QListWidget::item {{
        padding: 8px 12px;
        border-radius: 4px;
        margin: 2px 0;
    }}

    QListWidget::item:hover {{
        background-color: {COLORS["background"]};
    }}

    QListWidget::item:selected {{
        background-color: {COLORS["primary"]};
        color: white;
    }}

    QComboBox {{
        background-color: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        padding: 8px 12px;
        min-width: 200px;
    }}

    QComboBox:hover {{
        border-color: {COLORS["primary"]};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {COLORS["secondary"]};
        margin-right: 8px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        selection-background-color: {COLORS["primary"]};
        selection-color: white;
        padding: 4px;
    }}

    QTextEdit {{
        background-color: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        padding: 8px;
        selection-background-color: {COLORS["primary"]};
        selection-color: white;
    }}

    QTableWidget {{
        background-color: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        gridline-color: {COLORS["border"]};
    }}

    QTableWidget::item {{
        padding: 6px 8px;
    }}

    QTableWidget::item:selected {{
        background-color: {COLORS["primary"]};
        color: white;
    }}

    QHeaderView::section {{
        background-color: {COLORS["background"]};
        color: {COLORS["text"]};
        font-weight: 600;
        padding: 8px;
        border: none;
        border-bottom: 1px solid {COLORS["border"]};
    }}

    QSpinBox {{
        background-color: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        padding: 6px 8px;
    }}

    QSpinBox:hover {{
        border-color: {COLORS["primary"]};
    }}

    QSpinBox::up-button, QSpinBox::down-button {{
        border: none;
        width: 20px;
    }}

    QLabel {{
        background-color: transparent;
    }}

    QScrollBar:vertical {{
        background-color: {COLORS["background"]};
        width: 12px;
        border-radius: 6px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {COLORS["border"]};
        border-radius: 6px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS["secondary"]};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QMessageBox {{
        background-color: {COLORS["surface"]};
    }}

    QMessageBox QPushButton {{
        min-width: 80px;
    }}
"""


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

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accept drag events with file URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self.HOVER_STYLE)
            self.setText("Release to load files")

    def dragLeaveEvent(self, _event: QDragEnterEvent) -> None:
        """Reset appearance when drag leaves."""
        self._reset_style()

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
            QMessageBox.warning(
                self, "Warning", "No CSV files found in dropped items"
            )

        self._reset_style()

    def _reset_style(self) -> None:
        """Reset to default appearance."""
        self.setText("Drop CSV files here\nor click Browse")
        self.setStyleSheet(self.DEFAULT_STYLE)

    def mousePressEvent(self, _event: QDragEnterEvent) -> None:
        """Handle click to browse files."""
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

    def _calculate_taxes(self) -> None:
        """Calculate and display tax summary in table format."""
        if self.df is None:
            QMessageBox.warning(self, "Warning", "Please load data first")
            return

        months = self.months_spinbox.value()

        summary = self.calculator.generate_summary(self.df, months)
        period: TaxResults = summary["period_taxes"]  # type: ignore[assignment]
        annual: TaxResults = summary["annual_taxes"]  # type: ignore[assignment]

        # Update header labels with months
        self.results_table.setHorizontalHeaderLabels(
            ["", f"Period ({months} mo)", "Annual (12 mo)"]
        )

        # Build rows data: (label, period_value, annual_value, is_section_header, is_highlight)
        rows: list[tuple[str, float | None, float | None, bool, bool]] = [
            # Income section
            ("INCOME", None, None, True, False),
            ("Freelance (Tax Already Paid)", period.all_tax_applied, annual.all_tax_applied, False, False),
            ("Revenue (Sales Tax Bundled)", period.sales_tax_bundled, annual.sales_tax_bundled, False, False),
            ("Revenue (Sales Tax Applied)", period.sales_tax_applied, annual.sales_tax_applied, False, False),
            ("Business Expenses", -period.expenses, -annual.expenses, False, False),
            # Profit section
            ("PROFIT", None, None, True, False),
            ("Gross Revenue", period.gross_revenue, annual.gross_revenue, False, False),
            ("Business Profit", period.business_profit, annual.business_profit, False, False),
            ("Total Profit", period.profit, annual.profit, False, False),
            ("Sales Taxable Income", period.sales_taxable, annual.sales_taxable, False, False),
            ("Taxable Income", period.taxable_income, annual.taxable_income, False, False),
            # Taxes section
            ("TAXES", None, None, True, False),
            (f"Sales Tax ({period.sales_tax_rate * 100:.2f}%)", period.sales_tax, annual.sales_tax, False, False),
            ("Self-Employment Tax", period.sole_proprietor_tax, annual.sole_proprietor_tax, False, False),
            ("Federal Income Tax", period.federal_income_tax, annual.federal_income_tax, False, False),
            ("State Income Tax", period.state_income_tax, annual.state_income_tax, False, False),
            ("Total Income Tax", period.total_income_tax, annual.total_income_tax, False, False),
            ("Total Tax", period.total_tax, annual.total_tax, False, False),
            # Summary section
            ("SUMMARY", None, None, True, False),
            ("TAKE HOME", period.take_home, annual.take_home, False, True),
        ]

        self.results_table.setRowCount(len(rows))

        for row_idx, (label, period_val, annual_val, is_header, is_highlight) in enumerate(rows):
            # Label column
            label_item = QTableWidgetItem(label)
            if is_header:
                label_item.setBackground(self.results_table.palette().alternateBase())
                font = label_item.font()
                font.setBold(True)
                label_item.setFont(font)
            elif is_highlight:
                font = label_item.font()
                font.setBold(True)
                label_item.setFont(font)
            self.results_table.setItem(row_idx, 0, label_item)

            # Period column
            if period_val is not None:
                period_item = QTableWidgetItem(f"${period_val:,.2f}")
                period_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if is_highlight:
                    font = period_item.font()
                    font.setBold(True)
                    period_item.setFont(font)
                self.results_table.setItem(row_idx, 1, period_item)

            # Annual column
            if annual_val is not None:
                annual_item = QTableWidgetItem(f"${annual_val:,.2f}")
                annual_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if is_highlight:
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
            self.uncategorized_label.setText(
                f"Uncategorized ({len(uncategorized)}): {items_text}"
            )
        else:
            self.uncategorized_label.setText("")


def run_app() -> None:
    """Create and run the application."""
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = TaximateGUI()
    window.show()
    sys.exit(app.exec())
