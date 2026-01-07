"""
Sistema de notificações toast para feedback visual.
Toasts aparecem no canto inferior direito e desaparecem automaticamente.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QFrame, QLabel, QHBoxLayout, QPushButton,
    QGraphicsOpacityEffect, QApplication
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtSignal, QPoint
)
from PyQt6.QtGui import QFont

from ..theme import Theme


class Toast(QFrame):
    """
    Uma notificação toast individual.

    Types:
    - success: Verde, para ações completadas
    - error: Vermelho, para erros
    - warning: Laranja, para avisos
    - info: Azul, para informações
    """

    closed = pyqtSignal()

    # Configuração de duração por tipo (ms)
    DURATION = {
        "success": 3000,
        "error": 5000,
        "warning": 4000,
        "info": 3000,
    }

    # Ícones por tipo (emoji)
    ICONS = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
    }

    # Cores por tipo
    COLORS = {
        "success": Theme.SUCCESS,
        "error": Theme.DANGER,
        "warning": Theme.WARNING,
        "info": Theme.ACCENT_SECONDARY,
    }

    def __init__(
        self,
        message: str,
        toast_type: str = "info",
        duration: Optional[int] = None,
        parent=None
    ):
        super().__init__(parent)
        self.toast_type = toast_type
        self.message = message
        self._duration = duration or self.DURATION.get(toast_type, 3000)

        self._build_ui()
        self._setup_animations()

    def _build_ui(self):
        """Constrói a interface do toast."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Container principal
        color = self.COLORS.get(self.toast_type, Theme.ACCENT_SECONDARY)
        icon = self.ICONS.get(self.toast_type, "ℹ️")

        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BG_PRIMARY};
                border: 1px solid {color};
                border-left: 4px solid {color};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Ícone
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            font-size: 16px;
            background: transparent;
        """)
        layout.addWidget(icon_label)

        # Mensagem
        msg_label = QLabel(self.message)
        msg_label.setStyleSheet(f"""
            font-size: 13px;
            color: {Theme.TEXT_PRIMARY};
            background: transparent;
        """)
        msg_label.setWordWrap(True)
        msg_label.setMaximumWidth(280)
        layout.addWidget(msg_label, 1)

        # Botão fechar
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Theme.TEXT_MUTED};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close_toast)
        layout.addWidget(close_btn)

        # Ajusta tamanho
        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)

    def _setup_animations(self):
        """Configura animações de entrada/saída."""
        # Efeito de opacidade
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0)

        # Animação de fade in
        self._fade_in = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_in.setDuration(200)
        self._fade_in.setStartValue(0)
        self._fade_in.setEndValue(1)
        self._fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Animação de fade out
        self._fade_out = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_out.setDuration(200)
        self._fade_out.setStartValue(1)
        self._fade_out.setEndValue(0)
        self._fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_out.finished.connect(self._on_fade_out_finished)

        # Timer para auto-close
        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self.close_toast)

    def show_toast(self):
        """Mostra o toast com animação."""
        self.show()
        self._fade_in.start()
        self._close_timer.start(self._duration)

    def close_toast(self):
        """Fecha o toast com animação."""
        self._close_timer.stop()
        self._fade_out.start()

    def _on_fade_out_finished(self):
        """Callback quando fade out termina."""
        self.hide()
        self.closed.emit()
        self.deleteLater()


class ToastManager:
    """
    Gerenciador de toasts.
    Controla posicionamento e empilhamento de múltiplos toasts.
    """

    MAX_VISIBLE = 3
    SPACING = 10
    MARGIN_RIGHT = 20
    MARGIN_BOTTOM = 20

    def __init__(self, parent=None):
        self.parent = parent
        self._toasts: List[Toast] = []

    def show(
        self,
        message: str,
        toast_type: str = "info",
        duration: Optional[int] = None
    ):
        """
        Mostra um novo toast.

        Args:
            message: Texto da notificação
            toast_type: "success", "error", "warning", "info"
            duration: Duração em ms (opcional, usa padrão do tipo)
        """
        # Remove toasts excedentes
        while len(self._toasts) >= self.MAX_VISIBLE:
            oldest = self._toasts[0]
            oldest.close_toast()
            self._toasts.pop(0)

        # Cria novo toast
        toast = Toast(message, toast_type, duration, self.parent)
        toast.closed.connect(lambda: self._on_toast_closed(toast))

        self._toasts.append(toast)
        self._reposition_toasts()
        toast.show_toast()

    def _on_toast_closed(self, toast: Toast):
        """Callback quando um toast fecha."""
        if toast in self._toasts:
            self._toasts.remove(toast)
        self._reposition_toasts()

    def _reposition_toasts(self):
        """Reposiciona todos os toasts visíveis."""
        if not self.parent:
            return

        # Obtém geometria da janela pai
        parent_rect = self.parent.geometry()
        screen = QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()
        else:
            screen_rect = parent_rect

        # Posição inicial (canto inferior direito)
        x = screen_rect.right() - self.MARGIN_RIGHT
        y = screen_rect.bottom() - self.MARGIN_BOTTOM

        # Posiciona cada toast de baixo para cima
        for toast in reversed(self._toasts):
            toast_width = toast.width()
            toast_height = toast.height()

            toast_x = x - toast_width
            toast_y = y - toast_height

            toast.move(toast_x, toast_y)

            # Próximo toast acima
            y = toast_y - self.SPACING

    def success(self, message: str, duration: Optional[int] = None):
        """Atalho para toast de sucesso."""
        self.show(message, "success", duration)

    def error(self, message: str, duration: Optional[int] = None):
        """Atalho para toast de erro."""
        self.show(message, "error", duration)

    def warning(self, message: str, duration: Optional[int] = None):
        """Atalho para toast de aviso."""
        self.show(message, "warning", duration)

    def info(self, message: str, duration: Optional[int] = None):
        """Atalho para toast de informação."""
        self.show(message, "info", duration)

    def clear_all(self):
        """Fecha todos os toasts imediatamente."""
        for toast in self._toasts[:]:
            toast.close_toast()
        self._toasts.clear()
