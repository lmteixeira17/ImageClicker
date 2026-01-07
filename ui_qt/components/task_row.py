"""
Card de task com informações claras e controles completos.
Inclui animações e status em tempo real.
Suporta tasks simples e com múltiplas opções.
"""

from typing import List, Optional

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy,
    QGraphicsOpacityEffect, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QPropertyAnimation, QEasingCurve

from ..theme import Theme
from .icons import Icons


class TaskRow(QFrame):
    """
    Card de task com informações legíveis.
    Suporta modo simples (template único) e múltiplas opções.

    Layout Simples:
    ┌──────────────────────────────────────────────────────────────────────┐
    │ [▶ Iniciar] #1 ● │ Janela: Chrome*  │ Template: Accept_all │ [✎][✕] │
    │                  │ Ação: Clique     │ Status: Aguardando...         │
    └──────────────────────────────────────────────────────────────────────┘

    Layout Múltiplas:
    ┌──────────────────────────────────────────────────────────────────────┐
    │ [▶ Iniciar] #1 ● │ Janela: Chrome*  │ 3 opções [Sim ▼]    │ [✎][✕] │
    │                  │ Ação: Clique     │ Status: Aguardando...         │
    └──────────────────────────────────────────────────────────────────────┘
    """

    play_clicked = pyqtSignal(int)
    stop_clicked = pyqtSignal(int)
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    simulate_clicked = pyqtSignal(int)  # task_id
    option_changed = pyqtSignal(int, int)  # task_id, option_index

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
        options: Optional[List[dict]] = None,
        selected_option: int = 0,
        parent=None
    ):
        super().__init__(parent)
        self.task_id = task_id
        self.is_running = is_running
        self._click_count = 0
        self._pulse_timer = None
        self._options = options
        self._selected_option = selected_option

        self.setProperty("class", "task-row")
        # Altura maior se tiver múltiplas opções
        self.setFixedHeight(70 if options else 60)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(12)

        # === Play/Stop button ===
        play_text = f"{Icons.STOP}  Parar" if is_running else f"{Icons.PLAY}  Iniciar"
        self.play_btn = QPushButton(play_text)
        self.play_btn.setFixedSize(90, 38)
        self.play_btn.setProperty("variant", "danger" if is_running else "success")
        self._update_play_tooltip(is_running, interval)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setStyleSheet("font-size: 13px; font-weight: bold;")
        self.play_btn.clicked.connect(self._toggle_running)
        self._interval = interval
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
        window_lbl.setToolTip(f"Janela alvo: {window_name}\nA task monitora esta janela buscando o template")
        row1.addWidget(window_lbl)

        # Template ou opções
        if options:
            # Modo múltiplas opções
            opt_names = ", ".join([o["name"] for o in options])
            opts_label = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>{len(options)} opções:</b>")
            opts_label.setToolTip(f"Modo múltiplas opções\nOpções: {opt_names}\nClica quando TODAS estiverem visíveis")
            row1.addWidget(opts_label)

            self.options_combo = QComboBox()
            self.options_combo.setMinimumWidth(100)
            self.options_combo.setMaximumWidth(150)
            for opt in options:
                self.options_combo.addItem(opt["name"])
            self.options_combo.setCurrentIndex(selected_option)
            self.options_combo.currentIndexChanged.connect(self._on_option_changed)
            self.options_combo.setToolTip("Selecione qual opção será clicada automaticamente\nquando o prompt for detectado")
            self.options_combo.setStyleSheet(f"""
                QComboBox {{
                    background: {Theme.BG_GLASS};
                    border: 1px solid {Theme.ACCENT_PRIMARY};
                    border-radius: 4px;
                    padding: 2px 6px;
                    color: {Theme.ACCENT_PRIMARY};
                    font-weight: bold;
                }}
            """)
            row1.addWidget(self.options_combo)
        else:
            # Modo template único
            template_lbl = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Template:</b> <span style='color:{Theme.ACCENT_PRIMARY}'>{image_name}</span>")
            template_lbl.setToolTip(f"Template: {image_name}\nImagem usada para reconhecimento visual")
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
        action_tips = {
            "click": "Clique simples com botão esquerdo",
            "double_click": "Duplo clique rápido com botão esquerdo",
            "right_click": "Clique com botão direito (menu contexto)"
        }
        action_display = action_names.get(action, action)
        action_lbl = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Ação:</b> {action_display}")
        action_lbl.setToolTip(action_tips.get(action, "Tipo de clique a executar"))
        row2.addWidget(action_lbl)

        interval_lbl = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Intervalo:</b> {interval}s")
        interval_lbl.setToolTip(f"Intervalo entre buscas: {interval} segundos\nA cada {interval}s verifica se o template está visível")
        row2.addWidget(interval_lbl)

        threshold_pct = int(threshold * 100)
        threshold_lbl = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Threshold:</b> {threshold_pct}%")
        threshold_lbl.setToolTip(f"Precisão mínima: {threshold_pct}%\nQuanto maior, mais exato deve ser o match\nValores típicos: 80-90%")
        row2.addWidget(threshold_lbl)

        status_text = status if status else "Aguardando..."
        self.status_label = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Status:</b> {status_text}")
        self.status_label.setToolTip("Status atual da task\nMostra a última ação ou estado")
        row2.addWidget(self.status_label)

        # Contador de cliques
        self.click_count_label = QLabel(f"<b style='color:{Theme.TEXT_MUTED}'>Cliques:</b> 0")
        self.click_count_label.setToolTip("Total de cliques executados nesta sessão\nZera ao reiniciar o app")
        row2.addWidget(self.click_count_label)

        row2.addStretch()
        info_layout.addLayout(row2)

        main_layout.addWidget(info_frame, 1)

        # === Action buttons (inline) ===
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)

        # Botão simular
        simulate_btn = QPushButton(Icons.TEST)
        simulate_btn.setFixedSize(36, 36)
        simulate_btn.setProperty("variant", "ghost")
        simulate_btn.setToolTip("Simular busca\nTesta se o template seria encontrado SEM clicar\nÚtil para verificar configuração")
        simulate_btn.setStyleSheet(f"font-size: 18px; color: {Theme.ACCENT_PRIMARY};")
        simulate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        simulate_btn.clicked.connect(lambda: self.simulate_clicked.emit(self.task_id))
        btn_layout.addWidget(simulate_btn)

        edit_btn = QPushButton(Icons.EDIT)
        edit_btn.setFixedSize(36, 36)
        edit_btn.setProperty("variant", "ghost")
        edit_btn.setToolTip("Editar task\nAlterar janela, template, intervalo ou threshold\nDuplo-clique no card também edita")
        edit_btn.setStyleSheet(f"font-size: 18px; color: {Theme.TEXT_SECONDARY};")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.task_id))
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton(Icons.DELETE)
        delete_btn.setFixedSize(36, 36)
        delete_btn.setProperty("variant", "ghost")
        delete_btn.setToolTip("Excluir task permanentemente\nEsta ação não pode ser desfeita")
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

    def _update_play_tooltip(self, is_running: bool, interval: float = None):
        """Atualiza tooltip do botão play/stop."""
        if interval is None:
            interval = getattr(self, '_interval', 5.0)

        if is_running:
            self.play_btn.setToolTip(f"Parar monitoramento\nA task está buscando a cada {interval}s")
        else:
            self.play_btn.setToolTip(f"Iniciar monitoramento\nVai buscar o template a cada {interval}s")

    def _on_option_changed(self, index: int):
        """Emite signal quando opção selecionada muda."""
        self._selected_option = index
        self.option_changed.emit(self.task_id, index)

    def update_status(self, status: str, is_running: bool = None):
        """Atualiza status exibido."""
        status_text = status if status else "Aguardando..."
        self.status_label.setText(f"<b style='color:{Theme.TEXT_SECONDARY}'>Status:</b> {status_text}")

        if is_running is not None and is_running != self.is_running:
            self.is_running = is_running
            play_text = f"{Icons.STOP}  Parar" if is_running else f"{Icons.PLAY}  Iniciar"
            self.play_btn.setText(play_text)
            self.play_btn.setProperty("variant", "danger" if is_running else "success")
            self._update_play_tooltip(is_running)
            self.play_btn.style().unpolish(self.play_btn)
            self.play_btn.style().polish(self.play_btn)

            self.status_dot.setText(Icons.RUNNING if is_running else Icons.STOPPED)
            color = Theme.STATUS_RUNNING if is_running else Theme.STATUS_STOPPED
            self.status_dot.setStyleSheet(f"color: {color}; font-size: 14px;")

    def mouseDoubleClickEvent(self, event):
        """Double-click edita."""
        self.edit_clicked.emit(self.task_id)

    def increment_click_count(self):
        """Incrementa contador de cliques e mostra animação."""
        self._click_count += 1
        self.click_count_label.setText(
            f"<b style='color:{Theme.SUCCESS}'>Cliques:</b> {self._click_count}"
        )

        # Reset cor depois de 500ms
        QTimer.singleShot(500, lambda: self.click_count_label.setText(
            f"<b style='color:{Theme.TEXT_MUTED}'>Cliques:</b> {self._click_count}"
        ))

    def set_click_count(self, count: int):
        """Define contador de cliques."""
        self._click_count = count
        self.click_count_label.setText(
            f"<b style='color:{Theme.TEXT_MUTED}'>Cliques:</b> {count}"
        )

    def start_pulse_animation(self):
        """Inicia animação de pulse no status dot quando rodando."""
        if self._pulse_timer:
            return

        self._pulse_state = True

        def _pulse():
            if not self.is_running:
                self._pulse_timer.stop()
                self._pulse_timer = None
                return

            if self._pulse_state:
                self.status_dot.setStyleSheet(f"color: {Theme.STATUS_RUNNING}; font-size: 16px;")
            else:
                self.status_dot.setStyleSheet(f"color: {Theme.STATUS_RUNNING}; font-size: 14px;")
            self._pulse_state = not self._pulse_state

        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(_pulse)
        self._pulse_timer.start(500)

    def stop_pulse_animation(self):
        """Para animação de pulse."""
        if self._pulse_timer:
            self._pulse_timer.stop()
            self._pulse_timer = None
        self.status_dot.setStyleSheet(f"color: {Theme.STATUS_STOPPED}; font-size: 14px;")
