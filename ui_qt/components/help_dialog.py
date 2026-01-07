"""
Dialog de ajuda com lista de atalhos de teclado.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..theme import Theme


class HelpDialog(QDialog):
    """Dialog que mostra atalhos de teclado e ajuda."""

    def __init__(self, keyboard_manager, parent=None):
        super().__init__(parent)
        self.keyboard_manager = keyboard_manager
        self._build_ui()

    def _build_ui(self):
        """Constrói a interface do dialog."""
        self.setWindowTitle("Atalhos de Teclado")
        self.setFixedSize(500, 600)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_PRIMARY};
                border: 1px solid {Theme.GLASS_BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel("Atalhos de Teclado")
        header.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {Theme.TEXT_PRIMARY};
        """)
        layout.addWidget(header)

        # Subtítulo
        subtitle = QLabel("Use esses atalhos para navegar e executar ações rapidamente")
        subtitle.setStyleSheet(f"""
            font-size: 12px;
            color: {Theme.TEXT_SECONDARY};
            margin-bottom: 8px;
        """)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Scroll area para shortcuts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {Theme.BG_DARKER};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.TEXT_MUTED};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Theme.TEXT_SECONDARY};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(16)

        # Agrupa por categoria
        shortcuts_by_category = self.keyboard_manager.get_shortcuts_by_category()

        # Ordem das categorias
        category_order = [
            self.keyboard_manager.CATEGORY_NAVIGATION,
            self.keyboard_manager.CATEGORY_ACTIONS,
            self.keyboard_manager.CATEGORY_TASKS,
            self.keyboard_manager.CATEGORY_HELP,
        ]

        for category in category_order:
            if category not in shortcuts_by_category:
                continue

            shortcuts = shortcuts_by_category[category]

            # Categoria header
            cat_label = QLabel(category)
            cat_label.setStyleSheet(f"""
                font-size: 13px;
                font-weight: bold;
                color: {Theme.ACCENT_PRIMARY};
                padding-top: 8px;
            """)
            content_layout.addWidget(cat_label)

            # Shortcuts da categoria
            for shortcut in shortcuts:
                row = self._create_shortcut_row(shortcut)
                content_layout.addWidget(row)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # Linha separadora
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background: {Theme.GLASS_BORDER};")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # Footer com versão
        footer_layout = QHBoxLayout()

        version_label = QLabel("ImageClicker v3.0")
        version_label.setStyleSheet(f"""
            font-size: 11px;
            color: {Theme.TEXT_MUTED};
        """)
        footer_layout.addWidget(version_label)

        footer_layout.addStretch()

        # Botão fechar
        close_btn = QPushButton("Fechar")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT_PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {Theme.ACCENT_PRIMARY_HOVER};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        footer_layout.addWidget(close_btn)

        layout.addLayout(footer_layout)

    def _create_shortcut_row(self, shortcut) -> QFrame:
        """Cria uma linha para um atalho."""
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BG_GLASS_LIGHT};
                border-radius: 8px;
                padding: 4px;
            }}
        """)

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(12, 8, 12, 8)
        row_layout.setSpacing(12)

        # Descrição
        desc_label = QLabel(shortcut.description)
        desc_label.setStyleSheet(f"""
            font-size: 13px;
            color: {Theme.TEXT_PRIMARY};
        """)
        row_layout.addWidget(desc_label, 1)

        # Tecla (badge)
        key_badge = self._create_key_badge(shortcut.key)
        row_layout.addWidget(key_badge)

        return row

    def _create_key_badge(self, key: str) -> QLabel:
        """Cria badge visual para uma tecla."""
        # Divide teclas compostas
        parts = key.split("+")

        badge = QLabel(" + ".join(parts))
        badge.setStyleSheet(f"""
            QLabel {{
                background: {Theme.BG_DARKER};
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.GLASS_BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 11px;
            }}
        """)
        return badge


class QuickHelpTooltip(QFrame):
    """
    Tooltip pequeno que mostra um atalho específico.
    Usado para mostrar atalhos inline em botões.
    """

    def __init__(self, shortcut_key: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BG_DARKER};
                border: 1px solid {Theme.GLASS_BORDER};
                border-radius: 4px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)

        label = QLabel(shortcut_key)
        label.setStyleSheet(f"""
            font-family: "Consolas", monospace;
            font-size: 10px;
            color: {Theme.TEXT_MUTED};
        """)
        layout.addWidget(label)
