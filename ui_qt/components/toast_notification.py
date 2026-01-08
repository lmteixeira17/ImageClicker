"""
Sistema de notificações toast para feedback visual.
Toasts aparecem no canto inferior direito e desaparecem automaticamente.
Design moderno com fundo sólido e boa visibilidade.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QFrame, QLabel, QHBoxLayout, QPushButton,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect,
    QApplication
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtSignal
)
from PyQt6.QtGui import QColor


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

    # Ícones por tipo
    ICONS = {
        "success": "✓",
        "error": "✕",
        "warning": "⚠",
        "info": "ℹ",
    }

    # Cores por tipo (fundo, borda, ícone)
    COLORS = {
        "success": {
            "bg": "#065f46",       # Verde escuro
            "border": "#10b981",   # Verde
            "icon_bg": "#10b981",  # Verde
            "text": "#ecfdf5",     # Branco esverdeado
        },
        "error": {
            "bg": "#7f1d1d",       # Vermelho escuro
            "border": "#ef4444",   # Vermelho
            "icon_bg": "#ef4444",  # Vermelho
            "text": "#fef2f2",     # Branco avermelhado
        },
        "warning": {
            "bg": "#78350f",       # Laranja escuro
            "border": "#f59e0b",   # Laranja
            "icon_bg": "#f59e0b",  # Laranja
            "text": "#fffbeb",     # Branco amarelado
        },
        "info": {
            "bg": "#1e3a5f",       # Azul escuro
            "border": "#3b82f6",   # Azul
            "icon_bg": "#3b82f6",  # Azul
            "text": "#eff6ff",     # Branco azulado
        },
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

        # Cores do tipo
        colors = self.COLORS.get(self.toast_type, self.COLORS["info"])
        icon = self.ICONS.get(self.toast_type, "ℹ")

        # Container com fundo sólido e sombra
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg']};
                border: 2px solid {colors['border']};
                border-radius: 8px;
            }}
        """)

        # Sombra para destacar do fundo
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 8, 12, 8)
        layout.setSpacing(10)

        # Ícone em círculo colorido
        icon_container = QFrame()
        icon_container.setFixedSize(28, 28)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['icon_bg']};
                border: none;
                border-radius: 14px;
            }}
        """)
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: white;
                background: transparent;
                border: none;
            }}
        """)
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_container)

        # Mensagem
        msg_label = QLabel(self.message)
        msg_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 500;
                color: {colors['text']};
                background: transparent;
                border: none;
            }}
        """)
        msg_label.setWordWrap(True)
        msg_label.setMaximumWidth(280)
        layout.addWidget(msg_label, 1)

        # Botão fechar
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 12px;
                color: {colors['text']};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
        """)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close_toast)
        layout.addWidget(close_btn)

        # Ajusta tamanho
        self.adjustSize()
        self.setFixedHeight(max(self.sizeHint().height(), 48))
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)

    def _setup_animations(self):
        """Configura animações de entrada/saída."""
        # Efeito de opacidade (precisa ser separado do shadow)
        self._opacity_effect = QGraphicsOpacityEffect(self)
        # Nota: não podemos ter dois efeitos, então usamos apenas o shadow
        # e controlamos visibilidade de outra forma

        # Timer para auto-close
        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self.close_toast)

        # Timer para fade out
        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(16)  # ~60fps
        self._fade_timer.timeout.connect(self._fade_step)
        self._fade_value = 1.0
        self._fading_out = False

    def _fade_step(self):
        """Passo da animação de fade."""
        if self._fading_out:
            self._fade_value -= 0.1
            if self._fade_value <= 0:
                self._fade_timer.stop()
                self._on_fade_out_finished()
            else:
                self.setWindowOpacity(self._fade_value)

    def show_toast(self):
        """Mostra o toast com animação."""
        self._fade_value = 1.0
        self.setWindowOpacity(1.0)
        self.show()
        self._close_timer.start(self._duration)

    def close_toast(self):
        """Fecha o toast com animação."""
        self._close_timer.stop()
        self._fading_out = True
        self._fade_timer.start()

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
    SPACING = 8
    MARGIN_RIGHT = 24
    MARGIN_BOTTOM = 24

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
        screen = QApplication.primaryScreen()
        if not screen:
            return

        screen_rect = screen.availableGeometry()

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
