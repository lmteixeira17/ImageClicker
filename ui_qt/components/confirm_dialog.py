"""
Dialog de confirmação com estilo Glassmorphism.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt

from ..theme import Theme


class ConfirmDialog(QDialog):
    """Dialog de confirmação estilizado."""

    def __init__(
        self,
        parent=None,
        title: str = "Confirmar",
        message: str = "Tem certeza?",
        confirm_text: str = "Confirmar",
        cancel_text: str = "Cancelar",
        danger: bool = False
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 180)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Container principal com estilo glass
        container = QFrame(self)
        container.setGeometry(0, 0, 400, 180)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_GLASS};
                border: 1px solid {Theme.GLASS_BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {Theme.TEXT_PRIMARY};
            background: transparent;
        """)
        layout.addWidget(title_label)

        # Mensagem
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            font-size: 13px;
            color: {Theme.TEXT_SECONDARY};
            background: transparent;
        """)
        layout.addWidget(message_label)

        layout.addStretch()

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        # Cancelar
        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_GLASS_LIGHT};
                border: 1px solid {Theme.GLASS_BORDER};
                border-radius: 6px;
                color: {Theme.TEXT_PRIMARY};
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_GLASS_LIGHTER};
                border-color: {Theme.GLASS_BORDER_LIGHT};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        # Confirmar
        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setFixedSize(100, 36)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        if danger:
            confirm_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.DANGER};
                    border: none;
                    border-radius: 6px;
                    color: {Theme.TEXT_PRIMARY};
                    font-size: 13px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {Theme.DANGER_LIGHT};
                }}
            """)
        else:
            confirm_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.ACCENT_PRIMARY};
                    border: none;
                    border-radius: 6px;
                    color: {Theme.TEXT_PRIMARY};
                    font-size: 13px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {Theme.ACCENT_PRIMARY_HOVER};
                }}
            """)

        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)

    @staticmethod
    def confirm(parent, title: str, message: str, danger: bool = False) -> bool:
        """Mostra dialog e retorna True se confirmado."""
        dialog = ConfirmDialog(
            parent=parent,
            title=title,
            message=message,
            confirm_text="Excluir" if danger else "Confirmar",
            cancel_text="Cancelar",
            danger=danger
        )
        return dialog.exec() == QDialog.DialogCode.Accepted
