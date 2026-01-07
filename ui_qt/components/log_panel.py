"""
Painel de log com estilo Glassmorphism para PyQt6.
Exibe mensagens com timestamp e suporta auto-scroll.
"""

from datetime import datetime
from typing import List
from pathlib import Path

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QCheckBox, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor

from ..theme import Theme


class LogPanel(QFrame):
    """
    Painel de log colapsável.
    """

    MAX_LINES = 500

    def __init__(
        self,
        parent=None,
        title: str = "Log",
        height: int = 120,
        collapsible: bool = True,
        auto_scroll: bool = True
    ):
        super().__init__(parent)
        self.setProperty("class", "glass-panel")
        self.setMaximumHeight(height + 50)

        self._expanded_height = height
        self._collapsible = collapsible
        self._auto_scroll = auto_scroll
        self._is_expanded = True
        self._lines: List[str] = []

        self._build_ui(title)

    def _build_ui(self, title: str):
        """Constrói a interface do log."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(36)
        header.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border-bottom: 1px solid {Theme.GLASS_BORDER};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        header_layout.setSpacing(8)

        # Collapse button + título
        if self._collapsible:
            self.collapse_btn = QPushButton("▼" if self._is_expanded else "▶")
            self.collapse_btn.setFixedSize(20, 20)
            self.collapse_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    color: {Theme.TEXT_SECONDARY};
                    font-size: 10px;
                }}
                QPushButton:hover {{
                    color: {Theme.TEXT_PRIMARY};
                }}
            """)
            self.collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.collapse_btn.clicked.connect(self._toggle_collapse)
            header_layout.addWidget(self.collapse_btn)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: bold;
            color: {Theme.TEXT_PRIMARY};
            background: transparent;
        """)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Auto-scroll checkbox
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(self._auto_scroll)
        self.auto_scroll_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 11px;
                background: transparent;
                spacing: 4px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
            }}
        """)
        self.auto_scroll_cb.toggled.connect(self._on_auto_scroll_change)
        header_layout.addWidget(self.auto_scroll_cb)

        # Botões de ação - usando texto simples
        btn_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Theme.TEXT_SECONDARY};
                font-size: 12px;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                background: {Theme.BG_GLASS_LIGHT};
                color: {Theme.TEXT_PRIMARY};
                border-radius: 3px;
            }}
        """

        copy_btn = QPushButton("Copiar")
        copy_btn.setToolTip("Copiar log")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet(btn_style)
        copy_btn.clicked.connect(self._copy_log)
        header_layout.addWidget(copy_btn)

        clear_btn = QPushButton("Limpar")
        clear_btn.setToolTip("Limpar log")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(btn_style)
        clear_btn.clicked.connect(self.clear)
        header_layout.addWidget(clear_btn)

        layout.addWidget(header)

        # Content frame (para collapse)
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(0)

        # TextEdit para log
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFixedHeight(self._expanded_height)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.BG_DARKER};
                color: {Theme.TEXT_SECONDARY};
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 11px;
            }}
        """)
        content_layout.addWidget(self.text_edit)

        layout.addWidget(self.content_frame)

    def log(self, message: str, level: str = "info"):
        """
        Adiciona mensagem ao log.

        Args:
            message: Mensagem a adicionar
            level: "info", "success", "warning", "error", "click", "search", "task"
        """
        timestamp = datetime.now().strftime("[%H:%M:%S]")

        # Prefixo (emoji) e cor por nível
        level_config = {
            "info": ("ℹ️", Theme.ACCENT_SECONDARY),      # Azul claro - informação geral
            "success": ("✅", Theme.SUCCESS),            # Verde - sucesso/clique realizado
            "warning": ("⚠️", Theme.WARNING),            # Amarelo - aviso
            "error": ("❌", Theme.DANGER),               # Vermelho - erro
            "click": ("🖱️", "#00E676"),                  # Verde brilhante - clique executado
            "search": ("🔍", Theme.ACCENT_PRIMARY),      # Roxo - buscando template
            "task": ("📋", "#64B5F6"),                   # Azul - ação de task
            "window": ("🪟", "#81D4FA"),                 # Azul claro - janela encontrada
            "start": ("▶️", Theme.SUCCESS),              # Verde - iniciando
            "stop": ("⏹️", Theme.TEXT_MUTED),            # Cinza - parando
            "found": ("🎯", "#FFAB40"),                  # Laranja - encontrou template
            "notfound": ("👻", Theme.TEXT_MUTED),        # Cinza - não encontrou
        }
        emoji, color = level_config.get(level, ("ℹ️", Theme.TEXT_SECONDARY))

        line = f"{timestamp} {emoji} {message}"

        # Adiciona à lista
        self._lines.append((line, color))

        # Remove linhas antigas se exceder limite
        while len(self._lines) > self.MAX_LINES:
            self._lines.pop(0)

        # Atualiza textbox
        if len(self._lines) == self.MAX_LINES:
            self._rebuild_text()
        else:
            # Append
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)

            html_line = f'<span style="color: {color}">{line}</span>'
            if self.text_edit.toPlainText():
                cursor.insertHtml("<br>" + html_line)
            else:
                cursor.insertHtml(html_line)

        # Auto-scroll
        if self._auto_scroll:
            self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
            self.text_edit.ensureCursorVisible()

    def _rebuild_text(self):
        """Reconstrói o texto do log."""
        self.text_edit.clear()
        html_parts = []
        for line, color in self._lines:
            html_parts.append(f'<span style="color: {color}">{line}</span>')
        self.text_edit.setHtml("<br>".join(html_parts))

    def clear(self):
        """Limpa o log."""
        self._lines.clear()
        self.text_edit.clear()

    def get_text(self) -> str:
        """Retorna todo o texto do log."""
        return "\n".join([line for line, _ in self._lines])

    def _toggle_collapse(self):
        """Expande ou colapsa o painel."""
        self._is_expanded = not self._is_expanded

        if self._is_expanded:
            self.content_frame.show()
            self.collapse_btn.setText("▼")
            self.setMaximumHeight(self._expanded_height + 50)
        else:
            self.content_frame.hide()
            self.collapse_btn.setText("▶")
            self.setMaximumHeight(36)

    def _on_auto_scroll_change(self, checked: bool):
        """Callback quando auto-scroll muda."""
        self._auto_scroll = checked

    def _copy_log(self):
        """Copia log para clipboard."""
        text = self.get_text()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.log("Log copiado!", "success")

    @property
    def auto_scroll(self) -> bool:
        """Retorna estado do auto-scroll."""
        return self._auto_scroll

    @auto_scroll.setter
    def auto_scroll(self, value: bool):
        """Define auto-scroll."""
        self._auto_scroll = value
        self.auto_scroll_cb.setChecked(value)
