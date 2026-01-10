"""
Tema Glassmorphism para PyQt6.
Define cores e stylesheet QSS.
"""


class Theme:
    """Constantes de tema."""

    # Cores base
    BG_DARK = "#0a0a0f"
    BG_DARKER = "#050508"
    BG_PRIMARY = "#0a0a0f"  # Alias para BG_DARK
    BG_GLASS = "#1a1a2e"
    BG_GLASS_LIGHT = "#252542"
    BG_GLASS_LIGHTER = "#2d2d4a"

    # Bordas
    GLASS_BORDER = "#4a4a6c"
    GLASS_BORDER_LIGHT = "#5a5a8c"

    # Accent
    ACCENT_PRIMARY = "#6366f1"
    ACCENT_PRIMARY_HOVER = "#818cf8"
    ACCENT_SECONDARY = "#8b5cf6"

    # Semânticas
    SUCCESS = "#10b981"
    SUCCESS_LIGHT = "#34d399"
    WARNING = "#f59e0b"
    DANGER = "#ef4444"
    DANGER_LIGHT = "#f87171"

    # Texto
    TEXT_PRIMARY = "#f8fafc"
    TEXT_SECONDARY = "#a8b8d1"
    TEXT_MUTED = "#8b9bb8"

    # Status
    STATUS_RUNNING = "#10b981"
    STATUS_STOPPED = "#94a3b8"

    # Dimensões
    SIDEBAR_WIDTH = 200
    ROW_HEIGHT = 28


def get_stylesheet() -> str:
    """Retorna stylesheet QSS completo."""
    return f"""
    /* === GLOBAL === */
    QWidget {{
        background-color: {Theme.BG_DARK};
        color: {Theme.TEXT_PRIMARY};
        font-family: "Segoe UI", sans-serif;
        font-size: 12px;
    }}

    QMainWindow {{
        background-color: {Theme.BG_DARK};
    }}

    /* === SCROLLBAR === */
    QScrollBar:vertical {{
        background: {Theme.BG_DARKER};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {Theme.GLASS_BORDER};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {Theme.GLASS_BORDER_LIGHT};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {Theme.BG_DARKER};
        height: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {Theme.GLASS_BORDER};
        border-radius: 4px;
        min-width: 30px;
    }}

    /* === SIDEBAR === */
    #sidebar {{
        background-color: {Theme.BG_GLASS};
        border-right: 1px solid {Theme.GLASS_BORDER};
    }}

    #sidebar QPushButton {{
        text-align: left;
        padding: 10px 16px;
        border: none;
        border-radius: 6px;
        margin: 2px 8px;
        color: {Theme.TEXT_SECONDARY};
        background: transparent;
    }}
    #sidebar QPushButton:hover {{
        background: {Theme.BG_GLASS_LIGHT};
        color: {Theme.TEXT_PRIMARY};
    }}
    #sidebar QPushButton:checked {{
        background: {Theme.ACCENT_PRIMARY};
        color: {Theme.TEXT_PRIMARY};
    }}

    #sidebar_title {{
        font-size: 16px;
        font-weight: bold;
        color: {Theme.TEXT_PRIMARY};
        padding: 16px;
    }}

    /* === PANELS === */
    .glass-panel {{
        background-color: {Theme.BG_GLASS};
        border: 1px solid {Theme.GLASS_BORDER};
        border-radius: 8px;
    }}

    .panel-title {{
        font-size: 13px;
        font-weight: bold;
        color: {Theme.TEXT_PRIMARY};
        padding: 8px 12px;
        border-bottom: 1px solid {Theme.GLASS_BORDER};
    }}

    /* === BUTTONS === */
    QPushButton {{
        background-color: {Theme.BG_GLASS_LIGHT};
        border: 1px solid {Theme.GLASS_BORDER};
        border-radius: 4px;
        padding: 6px 12px;
        color: {Theme.TEXT_PRIMARY};
    }}
    QPushButton:hover {{
        background-color: {Theme.BG_GLASS_LIGHTER};
        border-color: {Theme.GLASS_BORDER_LIGHT};
    }}
    QPushButton:pressed {{
        background-color: {Theme.BG_GLASS};
    }}

    QPushButton[variant="primary"] {{
        background-color: {Theme.ACCENT_PRIMARY};
        border: none;
    }}
    QPushButton[variant="primary"]:hover {{
        background-color: {Theme.ACCENT_PRIMARY_HOVER};
    }}

    QPushButton[variant="success"] {{
        background-color: {Theme.SUCCESS};
        border: none;
    }}
    QPushButton[variant="success"]:hover {{
        background-color: {Theme.SUCCESS_LIGHT};
    }}

    QPushButton[variant="danger"] {{
        background-color: {Theme.DANGER};
        border: none;
    }}
    QPushButton[variant="danger"]:hover {{
        background-color: {Theme.DANGER_LIGHT};
    }}

    QPushButton[variant="ghost"] {{
        background: transparent;
        border: none;
        color: {Theme.TEXT_SECONDARY};
    }}
    QPushButton[variant="ghost"]:hover {{
        background: {Theme.BG_GLASS_LIGHT};
        color: {Theme.TEXT_PRIMARY};
    }}

    /* === INPUTS === */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {Theme.BG_GLASS_LIGHT};
        border: 1px solid {Theme.GLASS_BORDER};
        border-radius: 4px;
        padding: 4px 8px;
        color: {Theme.TEXT_PRIMARY};
        selection-background-color: {Theme.ACCENT_PRIMARY};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {Theme.ACCENT_PRIMARY};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {Theme.TEXT_SECONDARY};
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {Theme.BG_GLASS};
        border: 1px solid {Theme.GLASS_BORDER};
        selection-background-color: {Theme.ACCENT_PRIMARY};
    }}

    /* === TABLE/LIST === */
    QTableWidget, QListWidget {{
        background-color: transparent;
        border: none;
        gridline-color: {Theme.GLASS_BORDER};
    }}
    QTableWidget::item, QListWidget::item {{
        padding: 4px;
    }}
    QTableWidget::item:selected, QListWidget::item:selected {{
        background-color: {Theme.ACCENT_PRIMARY};
    }}
    QTableWidget::item:hover, QListWidget::item:hover {{
        background-color: {Theme.BG_GLASS_LIGHT};
    }}
    QHeaderView::section {{
        background-color: {Theme.BG_GLASS};
        border: none;
        border-bottom: 1px solid {Theme.GLASS_BORDER};
        padding: 6px;
        color: {Theme.TEXT_SECONDARY};
        font-weight: bold;
    }}

    /* === TASK ROW === */
    .task-row {{
        background-color: {Theme.BG_GLASS};
        border: 1px solid {Theme.GLASS_BORDER};
        border-radius: 4px;
        margin: 2px 0;
    }}
    .task-row:hover {{
        background-color: {Theme.BG_GLASS_LIGHT};
        border-color: {Theme.GLASS_BORDER_LIGHT};
    }}

    /* === LABELS === */
    QLabel {{
        background: transparent;
        color: {Theme.TEXT_PRIMARY};
    }}
    QLabel[variant="muted"] {{
        color: {Theme.TEXT_MUTED};
    }}
    QLabel[variant="secondary"] {{
        color: {Theme.TEXT_SECONDARY};
    }}
    QLabel[variant="accent"] {{
        color: {Theme.ACCENT_PRIMARY};
    }}
    QLabel[variant="success"] {{
        color: {Theme.SUCCESS};
    }}

    /* === CHECKBOX/RADIO === */
    QCheckBox, QRadioButton {{
        color: {Theme.TEXT_SECONDARY};
        spacing: 6px;
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 14px;
        height: 14px;
        border: 1px solid {Theme.GLASS_BORDER};
        border-radius: 3px;
        background: {Theme.BG_GLASS_LIGHT};
    }}
    QRadioButton::indicator {{
        border-radius: 7px;
    }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background: {Theme.ACCENT_PRIMARY};
        border-color: {Theme.ACCENT_PRIMARY};
    }}

    /* === TOOLTIP === */
    QToolTip {{
        background-color: {Theme.BG_GLASS};
        border: 1px solid {Theme.GLASS_BORDER};
        color: {Theme.TEXT_PRIMARY};
        padding: 4px 8px;
        border-radius: 4px;
    }}

    /* === SPLITTER === */
    QSplitter::handle {{
        background: {Theme.GLASS_BORDER};
    }}
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    QSplitter::handle:vertical {{
        height: 2px;
    }}

    /* === TAB WIDGET === */
    QTabWidget::pane {{
        border: 1px solid {Theme.GLASS_BORDER};
        border-radius: 4px;
        background: {Theme.BG_GLASS};
    }}
    QTabBar::tab {{
        background: {Theme.BG_GLASS};
        border: 1px solid {Theme.GLASS_BORDER};
        padding: 6px 16px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        background: {Theme.ACCENT_PRIMARY};
        border-color: {Theme.ACCENT_PRIMARY};
    }}
    QTabBar::tab:hover:!selected {{
        background: {Theme.BG_GLASS_LIGHT};
    }}

    /* === SLIDER === */
    QSlider::groove:horizontal {{
        border: 1px solid {Theme.GLASS_BORDER};
        height: 6px;
        background: {Theme.BG_GLASS_LIGHT};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {Theme.ACCENT_PRIMARY};
        border: none;
        width: 16px;
        height: 16px;
        margin: -5px 0;
        border-radius: 8px;
    }}
    QSlider::handle:horizontal:hover {{
        background: {Theme.ACCENT_PRIMARY_HOVER};
    }}
    QSlider::sub-page:horizontal {{
        background: {Theme.ACCENT_PRIMARY};
        border-radius: 3px;
    }}
    """
