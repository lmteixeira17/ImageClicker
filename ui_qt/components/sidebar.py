"""
Sidebar de navegação.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QButtonGroup, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt

from .icons import Icons
from ..theme import Theme


class Sidebar(QFrame):
    """Barra lateral de navegação."""

    page_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo/Título
        title = QLabel(f"  {Icons.APP_ICON}  ImageClicker")
        title.setObjectName("sidebar_title")
        layout.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {Theme.GLASS_BORDER}; max-height: 1px;")
        layout.addWidget(sep)

        # Menu items
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._buttons = {}

        menu_items = [
            ("dashboard", Icons.DASHBOARD, "Dashboard"),
            ("tasks", Icons.TASKS, "Tasks"),
            ("prompts", Icons.PROMPTS, "Prompts"),
            ("templates", Icons.IMAGE, "Templates"),
        ]

        for page_id, icon, label in menu_items:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("font-size: 13px; text-align: left;")
            btn.clicked.connect(lambda checked, p=page_id: self._on_click(p))
            self._button_group.addButton(btn)
            self._buttons[page_id] = btn
            layout.addWidget(btn)

        # Spacer
        layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background: {Theme.GLASS_BORDER}; max-height: 1px;")
        layout.addWidget(sep2)

        # Settings
        settings_btn = QPushButton(f"  {Icons.SETTINGS}   Settings")
        settings_btn.setCheckable(True)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setStyleSheet("font-size: 13px; text-align: left;")
        settings_btn.clicked.connect(lambda: self._on_click("settings"))
        self._button_group.addButton(settings_btn)
        self._buttons["settings"] = settings_btn
        layout.addWidget(settings_btn)

        # Padding bottom
        layout.addSpacing(8)

        # Select first by default
        self._buttons["dashboard"].setChecked(True)

    def _on_click(self, page_id: str):
        """Emite sinal de mudança de página."""
        self.page_changed.emit(page_id)

    def set_current(self, page_id: str):
        """Define página atual."""
        if page_id in self._buttons:
            self._buttons[page_id].setChecked(True)
