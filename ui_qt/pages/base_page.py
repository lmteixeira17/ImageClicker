"""
Página base abstrata.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from pathlib import Path

from ..theme import Theme


class BasePage(QWidget):
    """Página base com header."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app

        # Layout principal
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(16, 16, 16, 16)
        self._main_layout.setSpacing(12)

        # Header
        self._header = QHBoxLayout()
        self._header.setSpacing(12)

        self._title_label = QLabel()
        self._title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self._header.addWidget(self._title_label)
        self._header.addStretch()

        # Actions area (para botões no header)
        self._header_actions = QHBoxLayout()
        self._header_actions.setSpacing(8)
        self._header.addLayout(self._header_actions)

        self._main_layout.addLayout(self._header)

        # Content area
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)
        self._main_layout.addWidget(self._content, 1)

        self._build_ui()

    def set_title(self, title: str):
        """Define título da página."""
        self._title_label.setText(title)

    def add_header_widget(self, widget):
        """Adiciona widget ao header."""
        self._header_actions.addWidget(widget)

    def content_layout(self) -> QVBoxLayout:
        """Retorna layout do conteúdo."""
        return self._content_layout

    def _build_ui(self):
        """Override nas subclasses para construir UI."""
        pass

    def on_show(self):
        """Chamado quando página é exibida."""
        pass

    def refresh(self):
        """Atualiza dados da página."""
        pass

    @property
    def task_manager(self):
        """Acesso ao TaskManager."""
        return self.app.task_manager

    @property
    def images_dir(self) -> Path:
        """Diretório de imagens."""
        return self.app.images_dir

    def log(self, message: str, level: str = "info"):
        """Log na UI."""
        if hasattr(self.app, 'log'):
            self.app.log(message, level)
