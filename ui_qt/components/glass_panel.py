"""
Painel com estilo glass.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt


class GlassPanel(QFrame):
    """Painel com estilo glassmorphism."""

    def __init__(self, title: str = None, parent=None):
        super().__init__(parent)
        self.setProperty("class", "glass-panel")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # Title label
        self._title_label = None
        if title:
            self._title_label = QLabel(title)
            self._title_label.setProperty("class", "panel-title")
            self._main_layout.addWidget(self._title_label)

        # Content area
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(12, 8, 12, 8)
        self._content_layout.setSpacing(4)
        self._main_layout.addWidget(self._content)

    def content_layout(self) -> QVBoxLayout:
        """Retorna layout do conteúdo."""
        return self._content_layout

    def add_widget(self, widget: QWidget):
        """Adiciona widget ao conteúdo."""
        self._content_layout.addWidget(widget)

    def add_stretch(self):
        """Adiciona espaço flexível."""
        self._content_layout.addStretch()

    def set_title(self, title: str):
        """Atualiza o título do painel."""
        if self._title_label:
            self._title_label.setText(title)
        else:
            self._title_label = QLabel(title)
            self._title_label.setProperty("class", "panel-title")
            self._main_layout.insertWidget(0, self._title_label)
