"""
Card de task com informações claras e controles completos.
"""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt

from ..theme import Theme
from .icons import Icons


class TaskRow(QFrame):
    """
    Card de task com informações legíveis.

    Layout:
    ┌──────────────────────────────────────────────────────────────────────┐
    │ [▶ Iniciar] #1 ● │ Janela: Chrome*  │ Template: Accept_all │ [✎][✕] │
    │                  │ Ação: Clique     │ Status: Aguardando...         │
    └──────────────────────────────────────────────────────────────────────┘
    """

    play_clicked = pyqtSignal(int)
    stop_clicked = pyqtSignal(int)
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)

    def __init__(
        self,
        task_id: int,
        window_name: str,
        image_name: str,
        action: str,
        interval: float,
        threshold: float = 0.85,
        is_running: bool = False,
        status: str = "",
        parent=None
    ):
        super().__init__(parent)
        self.task_id = task_id
        self.is_running = is_running

        self.setProperty("class", "task-row")
        self.setFixedHeight(60)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(12)

        # === Play/Stop button ===
        play_text = f"{Icons.STOP}  Parar" if is_running else f"{Icons.PLAY}  Iniciar"
        self.play_btn = QPushButton(play_text)
        self.play_btn.setFixedSize(90, 38)
        self.play_btn.setProperty("variant", "danger" if is_running else "success")
        self.play_btn.setToolTip("Parar task" if is_running else "Iniciar task")
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setStyleSheet("font-size: 13px; font-weight: bold;")
        self.play_btn.clicked.connect(self._toggle_running)
        main_layout.addWidget(self.play_btn)

        # === ID + Status indicator ===
        id_frame = QFrame()
        id_frame.setFixedWidth(45)
        id_layout = QVBoxLayout(id_frame)
        id_layout.setContentsMargins(0, 0, 0, 0)
        id_layout.setSpacing(2)
        id_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        id_label = QLabel(f"#{task_id}")
        id_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        id_layout.addWidget(id_label)

        self.status_dot = QLabel(Icons.RUNNING if is_running else Icons.STOPPED)
        self.status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = Theme.STATUS_RUNNING if is_running else Theme.STATUS_STOPPED
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 14px;")
        id_layout.addWidget(self.status_dot)

        main_layout.addWidget(id_frame)

        # === Separator ===
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"background: {Theme.GLASS_BORDER}; max-width: 1px;")
        main_layout.addWidget(sep)

        # === Info section (2 rows) ===
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        # Row 1: Window + Template
        row1 = QHBoxLayout()
        row1.setSpacing(24)

        window_display = window_name if len(window_name) <= 30 else window_name[:27] + "..."
        window_lbl = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Janela:</b> {window_display}")
        window_lbl.setToolTip(window_name)
        row1.addWidget(window_lbl)

        template_lbl = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Template:</b> <span style='color:{Theme.ACCENT_PRIMARY}'>{image_name}</span>")
        template_lbl.setToolTip(image_name)
        row1.addWidget(template_lbl)

        row1.addStretch()
        info_layout.addLayout(row1)

        # Row 2: Action + Interval + Status
        row2 = QHBoxLayout()
        row2.setSpacing(24)

        action_names = {
            "click": "Clique",
            "double_click": "Duplo Clique",
            "right_click": "Clique Direito"
        }
        action_display = action_names.get(action, action)
        action_lbl = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Ação:</b> {action_display}")
        row2.addWidget(action_lbl)

        interval_lbl = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Intervalo:</b> {interval}s")
        row2.addWidget(interval_lbl)

        threshold_pct = int(threshold * 100)
        threshold_lbl = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Threshold:</b> {threshold_pct}%")
        row2.addWidget(threshold_lbl)

        status_text = status if status else "Aguardando..."
        self.status_label = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Status:</b> {status_text}")
        row2.addWidget(self.status_label)

        row2.addStretch()
        info_layout.addLayout(row2)

        main_layout.addWidget(info_frame, 1)

        # === Action buttons (inline) ===
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        edit_btn = QPushButton(Icons.EDIT)
        edit_btn.setFixedSize(36, 36)
        edit_btn.setProperty("variant", "ghost")
        edit_btn.setToolTip("Editar task")
        edit_btn.setStyleSheet(f"font-size: 18px; color: {Theme.TEXT_SECONDARY};")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.task_id))
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton(Icons.DELETE)
        delete_btn.setFixedSize(36, 36)
        delete_btn.setProperty("variant", "ghost")
        delete_btn.setToolTip("Excluir task")
        delete_btn.setStyleSheet(f"font-size: 18px; color: {Theme.DANGER};")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.task_id))
        btn_layout.addWidget(delete_btn)

        main_layout.addWidget(btn_frame)

    def _toggle_running(self):
        """Alterna estado de execução."""
        if self.is_running:
            self.stop_clicked.emit(self.task_id)
        else:
            self.play_clicked.emit(self.task_id)

    def update_status(self, status: str, is_running: bool = None):
        """Atualiza status exibido."""
        status_text = status if status else "Aguardando..."
        self.status_label.setText(f"<b style='color:{Theme.TEXT_SECONDARY}'>Status:</b> {status_text}")

        if is_running is not None and is_running != self.is_running:
            self.is_running = is_running
            play_text = f"{Icons.STOP}  Parar" if is_running else f"{Icons.PLAY}  Iniciar"
            self.play_btn.setText(play_text)
            self.play_btn.setProperty("variant", "danger" if is_running else "success")
            self.play_btn.setToolTip("Parar task" if is_running else "Iniciar task")
            self.play_btn.style().unpolish(self.play_btn)
            self.play_btn.style().polish(self.play_btn)

            self.status_dot.setText(Icons.RUNNING if is_running else Icons.STOPPED)
            color = Theme.STATUS_RUNNING if is_running else Theme.STATUS_STOPPED
            self.status_dot.setStyleSheet(f"color: {color}; font-size: 14px;")

    def mouseDoubleClickEvent(self, event):
        """Double-click edita."""
        self.edit_clicked.emit(self.task_id)
