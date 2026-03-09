"""Color scheme and Qt stylesheet for the Taximate GUI."""

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
