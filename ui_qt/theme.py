"""
Tema Glassmorphism para PyQt6.
Suporta Dark Mode e Light Mode.
"""

from typing import Callable, List


class ThemeColors:
    """Classe base para cores do tema."""
    pass


class DarkTheme(ThemeColors):
    """Tema escuro - Glassmorphism dark."""

    # Cores base
    BG_DARK = "#0d0d14"
    BG_DARKER = "#08080c"
    BG_PRIMARY = "#0d0d14"
    BG_GLASS = "#181828"
    BG_GLASS_LIGHT = "#222238"
    BG_GLASS_LIGHTER = "#2a2a42"

    # Bordas
    GLASS_BORDER = "#4a4a70"
    GLASS_BORDER_LIGHT = "#5a5a88"

    # Accent
    ACCENT_PRIMARY = "#6366f1"
    ACCENT_PRIMARY_HOVER = "#818cf8"
    ACCENT_SECONDARY = "#8b5cf6"

    # Semânticas
    SUCCESS = "#22c55e"
    SUCCESS_LIGHT = "#4ade80"
    WARNING = "#f59e0b"
    DANGER = "#ef4444"
    DANGER_LIGHT = "#f87171"

    # Texto
    TEXT_PRIMARY = "#f1f5f9"
    TEXT_SECONDARY = "#cbd5e1"
    TEXT_MUTED = "#94a3b8"

    # Status
    STATUS_RUNNING = "#22c55e"
    STATUS_STOPPED = "#94a3b8"


class LightTheme(ThemeColors):
    """Tema claro - Clean light."""

    # Cores base
    BG_DARK = "#f8fafc"
    BG_DARKER = "#f1f5f9"
    BG_PRIMARY = "#ffffff"
    BG_GLASS = "#ffffff"
    BG_GLASS_LIGHT = "#f1f5f9"
    BG_GLASS_LIGHTER = "#e2e8f0"

    # Bordas
    GLASS_BORDER = "#cbd5e1"
    GLASS_BORDER_LIGHT = "#94a3b8"

    # Accent
    ACCENT_PRIMARY = "#4f46e5"
    ACCENT_PRIMARY_HOVER = "#6366f1"
    ACCENT_SECONDARY = "#7c3aed"

    # Semânticas
    SUCCESS = "#16a34a"
    SUCCESS_LIGHT = "#22c55e"
    WARNING = "#d97706"
    DANGER = "#dc2626"
    DANGER_LIGHT = "#ef4444"

    # Texto
    TEXT_PRIMARY = "#0f172a"
    TEXT_SECONDARY = "#475569"
    TEXT_MUTED = "#64748b"

    # Status
    STATUS_RUNNING = "#16a34a"
    STATUS_STOPPED = "#64748b"


class Theme:
    """
    Gerenciador de tema com suporte a Dark/Light mode.
    Uso: Theme.TEXT_PRIMARY, Theme.BG_DARK, etc.
    """

    _current_mode = "dark"  # "dark" ou "light"
    _listeners: List[Callable] = []

    # Cores base (inicializadas com dark)
    BG_DARK = DarkTheme.BG_DARK
    BG_DARKER = DarkTheme.BG_DARKER
    BG_PRIMARY = DarkTheme.BG_PRIMARY
    BG_GLASS = DarkTheme.BG_GLASS
    BG_GLASS_LIGHT = DarkTheme.BG_GLASS_LIGHT
    BG_GLASS_LIGHTER = DarkTheme.BG_GLASS_LIGHTER

    # Bordas
    GLASS_BORDER = DarkTheme.GLASS_BORDER
    GLASS_BORDER_LIGHT = DarkTheme.GLASS_BORDER_LIGHT

    # Accent
    ACCENT_PRIMARY = DarkTheme.ACCENT_PRIMARY
    ACCENT_PRIMARY_HOVER = DarkTheme.ACCENT_PRIMARY_HOVER
    ACCENT_SECONDARY = DarkTheme.ACCENT_SECONDARY

    # Semânticas
    SUCCESS = DarkTheme.SUCCESS
    SUCCESS_LIGHT = DarkTheme.SUCCESS_LIGHT
    WARNING = DarkTheme.WARNING
    DANGER = DarkTheme.DANGER
    DANGER_LIGHT = DarkTheme.DANGER_LIGHT

    # Texto
    TEXT_PRIMARY = DarkTheme.TEXT_PRIMARY
    TEXT_SECONDARY = DarkTheme.TEXT_SECONDARY
    TEXT_MUTED = DarkTheme.TEXT_MUTED

    # Status
    STATUS_RUNNING = DarkTheme.STATUS_RUNNING
    STATUS_STOPPED = DarkTheme.STATUS_STOPPED

    # Dimensões (não mudam com tema)
    SIDEBAR_WIDTH = 200
    ROW_HEIGHT = 32

    @classmethod
    def get_mode(cls) -> str:
        """Retorna o modo atual ('dark' ou 'light')."""
        return cls._current_mode

    @classmethod
    def is_dark(cls) -> bool:
        """Retorna True se estiver no modo escuro."""
        return cls._current_mode == "dark"

    @classmethod
    def set_mode(cls, mode: str):
        """
        Define o modo do tema.

        Args:
            mode: 'dark' ou 'light'
        """
        if mode not in ("dark", "light"):
            raise ValueError("Mode must be 'dark' or 'light'")

        if mode == cls._current_mode:
            return

        cls._current_mode = mode
        theme_class = DarkTheme if mode == "dark" else LightTheme

        # Atualiza todas as cores
        cls.BG_DARK = theme_class.BG_DARK
        cls.BG_DARKER = theme_class.BG_DARKER
        cls.BG_PRIMARY = theme_class.BG_PRIMARY
        cls.BG_GLASS = theme_class.BG_GLASS
        cls.BG_GLASS_LIGHT = theme_class.BG_GLASS_LIGHT
        cls.BG_GLASS_LIGHTER = theme_class.BG_GLASS_LIGHTER
        cls.GLASS_BORDER = theme_class.GLASS_BORDER
        cls.GLASS_BORDER_LIGHT = theme_class.GLASS_BORDER_LIGHT
        cls.ACCENT_PRIMARY = theme_class.ACCENT_PRIMARY
        cls.ACCENT_PRIMARY_HOVER = theme_class.ACCENT_PRIMARY_HOVER
        cls.ACCENT_SECONDARY = theme_class.ACCENT_SECONDARY
        cls.SUCCESS = theme_class.SUCCESS
        cls.SUCCESS_LIGHT = theme_class.SUCCESS_LIGHT
        cls.WARNING = theme_class.WARNING
        cls.DANGER = theme_class.DANGER
        cls.DANGER_LIGHT = theme_class.DANGER_LIGHT
        cls.TEXT_PRIMARY = theme_class.TEXT_PRIMARY
        cls.TEXT_SECONDARY = theme_class.TEXT_SECONDARY
        cls.TEXT_MUTED = theme_class.TEXT_MUTED
        cls.STATUS_RUNNING = theme_class.STATUS_RUNNING
        cls.STATUS_STOPPED = theme_class.STATUS_STOPPED

        # Notifica listeners
        for listener in cls._listeners:
            try:
                listener(mode)
            except Exception:
                pass

    @classmethod
    def toggle(cls):
        """Alterna entre dark e light mode."""
        new_mode = "light" if cls._current_mode == "dark" else "dark"
        cls.set_mode(new_mode)

    @classmethod
    def add_listener(cls, callback: Callable):
        """Adiciona listener para mudanças de tema."""
        if callback not in cls._listeners:
            cls._listeners.append(callback)

    @classmethod
    def remove_listener(cls, callback: Callable):
        """Remove listener."""
        if callback in cls._listeners:
            cls._listeners.remove(callback)


def get_stylesheet() -> str:
    """Retorna stylesheet QSS completo baseado no tema atual."""
    return f"""
    /* === GLOBAL === */
    QWidget {{
        background-color: {Theme.BG_DARK};
        color: {Theme.TEXT_PRIMARY};
        font-family: "Segoe UI", sans-serif;
        font-size: 13px;
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
        color: #ffffff;
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
        color: #ffffff;
    }}
    QPushButton[variant="primary"]:hover {{
        background-color: {Theme.ACCENT_PRIMARY_HOVER};
    }}

    QPushButton[variant="success"] {{
        background-color: {Theme.SUCCESS};
        border: none;
        color: #ffffff;
    }}
    QPushButton[variant="success"]:hover {{
        background-color: {Theme.SUCCESS_LIGHT};
    }}

    QPushButton[variant="danger"] {{
        background-color: {Theme.DANGER};
        border: none;
        color: #ffffff;
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
        color: #ffffff;
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
