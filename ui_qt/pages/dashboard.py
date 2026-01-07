"""
Página Dashboard - Visão geral e estatísticas.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt

from .base_page import BasePage
from ..components.glass_panel import GlassPanel
from ..components.log_panel import LogPanel
from ..components.icons import Icons
from ..theme import Theme


class StatCard(QFrame):
    """Card de estatística."""

    def __init__(self, icon: str, value: str, label: str, color: str = None, parent=None):
        super().__init__(parent)
        self.setProperty("class", "glass-panel")
        self.setFixedHeight(80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        # Valor grande
        self.value_label = QLabel(f"{icon} {value}")
        self.value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color or Theme.TEXT_PRIMARY};")
        layout.addWidget(self.value_label)

        # Label
        desc_label = QLabel(label)
        desc_label.setProperty("variant", "secondary")
        layout.addWidget(desc_label)

        self._icon = icon
        self._color = color

    def set_value(self, value: str):
        """Atualiza o valor do card."""
        self.value_label.setText(f"{self._icon} {value}")


class MiniTaskRow(QFrame):
    """Versão compacta do TaskRow para o Dashboard (sem CRUD)."""

    def __init__(self, task, is_running: bool, on_play, on_stop, parent=None):
        super().__init__(parent)
        self.task = task
        self.is_running = is_running
        self.on_play = on_play
        self.on_stop = on_stop

        self.setProperty("class", "task-row")
        self.setFixedHeight(50)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 6, 10, 6)
        main_layout.setSpacing(10)

        # Play/Stop button
        play_text = f"{Icons.STOP}" if is_running else f"{Icons.PLAY}"
        self.play_btn = QPushButton(play_text)
        self.play_btn.setFixedSize(36, 36)
        self.play_btn.setProperty("variant", "danger" if is_running else "success")
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.clicked.connect(self._toggle)
        main_layout.addWidget(self.play_btn)

        # ID + Status
        id_frame = QFrame()
        id_frame.setFixedWidth(35)
        id_layout = QVBoxLayout(id_frame)
        id_layout.setContentsMargins(0, 0, 0, 0)
        id_layout.setSpacing(0)

        id_label = QLabel(f"#{task.id}")
        id_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        id_layout.addWidget(id_label)

        self.status_dot = QLabel(Icons.RUNNING if is_running else Icons.STOPPED)
        self.status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = Theme.STATUS_RUNNING if is_running else Theme.STATUS_STOPPED
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 12px;")
        id_layout.addWidget(self.status_dot)

        main_layout.addWidget(id_frame)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        window_name = task.process_name or task.window_title
        window_display = window_name[:20] + "..." if len(window_name) > 20 else window_name
        window_lbl = QLabel(f"<b>{window_display}</b>")
        window_lbl.setToolTip(window_name)
        info_layout.addWidget(window_lbl)

        threshold_pct = int(getattr(task, 'threshold', 0.85) * 100)
        template_lbl = QLabel(f"<span style='color:{Theme.TEXT_SECONDARY}'>{task.image_name}</span> · <span style='color:{Theme.ACCENT_PRIMARY}'>{task.interval}s</span> · <span style='color:{Theme.TEXT_MUTED}'>{threshold_pct}%</span>")
        template_lbl.setStyleSheet("font-size: 11px;")
        info_layout.addWidget(template_lbl)

        main_layout.addLayout(info_layout, 1)

    def _toggle(self):
        if self.is_running:
            self.on_stop(self.task.id)
            self.is_running = False
            self.play_btn.setText(Icons.PLAY)
            self.play_btn.setProperty("variant", "success")
        else:
            self.on_play(self.task.id)
            self.is_running = True
            self.play_btn.setText(Icons.STOP)
            self.play_btn.setProperty("variant", "danger")

        self.play_btn.style().unpolish(self.play_btn)
        self.play_btn.style().polish(self.play_btn)

        self.status_dot.setText(Icons.RUNNING if self.is_running else Icons.STOPPED)
        color = Theme.STATUS_RUNNING if self.is_running else Theme.STATUS_STOPPED
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 12px;")


class MiniPromptRow(QFrame):
    """Versão compacta do PromptHandlerRow para o Dashboard."""

    def __init__(self, handler, is_running: bool, on_play, on_stop, parent=None):
        super().__init__(parent)
        self.handler = handler
        self.is_running = is_running
        self.on_play = on_play
        self.on_stop = on_stop

        self.setProperty("class", "task-row")
        self.setFixedHeight(50)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 6, 10, 6)
        main_layout.setSpacing(10)

        # Play/Stop button
        play_text = f"{Icons.STOP}" if is_running else f"{Icons.PLAY}"
        self.play_btn = QPushButton(play_text)
        self.play_btn.setFixedSize(36, 36)
        self.play_btn.setProperty("variant", "danger" if is_running else "success")
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.clicked.connect(self._toggle)
        main_layout.addWidget(self.play_btn)

        # ID + Status
        id_frame = QFrame()
        id_frame.setFixedWidth(35)
        id_layout = QVBoxLayout(id_frame)
        id_layout.setContentsMargins(0, 0, 0, 0)
        id_layout.setSpacing(0)

        id_label = QLabel(f"#{handler.id}")
        id_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        id_layout.addWidget(id_label)

        self.status_dot = QLabel(Icons.RUNNING if is_running else Icons.STOPPED)
        self.status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = Theme.STATUS_RUNNING if is_running else Theme.STATUS_STOPPED
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 12px;")
        id_layout.addWidget(self.status_dot)

        main_layout.addWidget(id_frame)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        window_name = handler.process_name or handler.window_title
        window_display = window_name[:20] + "..." if len(window_name) > 20 else window_name
        window_lbl = QLabel(f"<b>{window_display}</b>")
        window_lbl.setToolTip(window_name)
        info_layout.addWidget(window_lbl)

        opts_count = len(handler.options) if handler.options else 0
        selected = handler.options[handler.selected_option]["name"] if handler.options else "N/A"
        threshold_pct = int(getattr(handler, 'threshold', 0.85) * 100)
        opts_lbl = QLabel(f"<span style='color:{Theme.TEXT_SECONDARY}'>{opts_count} opções</span> · <span style='color:{Theme.ACCENT_PRIMARY}'>{selected}</span> · <span style='color:{Theme.TEXT_MUTED}'>{threshold_pct}%</span>")
        opts_lbl.setStyleSheet("font-size: 11px;")
        info_layout.addWidget(opts_lbl)

        main_layout.addLayout(info_layout, 1)

    def _toggle(self):
        if self.is_running:
            self.on_stop(self.handler.id)
            self.is_running = False
            self.play_btn.setText(Icons.PLAY)
            self.play_btn.setProperty("variant", "success")
        else:
            self.on_play(self.handler.id)
            self.is_running = True
            self.play_btn.setText(Icons.STOP)
            self.play_btn.setProperty("variant", "danger")

        self.play_btn.style().unpolish(self.play_btn)
        self.play_btn.style().polish(self.play_btn)

        self.status_dot.setText(Icons.RUNNING if self.is_running else Icons.STOPPED)
        color = Theme.STATUS_RUNNING if self.is_running else Theme.STATUS_STOPPED
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 12px;")


class DashboardPage(BasePage):
    """Página de dashboard."""

    def _build_ui(self):
        self.set_title("Dashboard")

        # Botões de controle no header
        self.start_all_btn = QPushButton(f"{Icons.PLAY}  Iniciar Tudo")
        self.start_all_btn.setProperty("variant", "success")
        self.start_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_all_btn.clicked.connect(self._start_all)
        self.add_header_widget(self.start_all_btn)

        self.stop_all_btn = QPushButton(f"{Icons.STOP}  Parar Tudo")
        self.stop_all_btn.setProperty("variant", "danger")
        self.stop_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_all_btn.clicked.connect(self._stop_all)
        self.add_header_widget(self.stop_all_btn)

        layout = self.content_layout()

        # Stats cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.stat_tasks = StatCard("☰", "0", "Tasks", Theme.ACCENT_PRIMARY)
        self.stat_prompts = StatCard("◎", "0", "Prompts", Theme.ACCENT_SECONDARY)
        self.stat_running = StatCard("●", "0", "Rodando", Theme.SUCCESS)
        self.stat_stopped = StatCard("○", "0", "Parados", Theme.TEXT_MUTED)

        stats_layout.addWidget(self.stat_tasks)
        stats_layout.addWidget(self.stat_prompts)
        stats_layout.addWidget(self.stat_running)
        stats_layout.addWidget(self.stat_stopped)

        layout.addLayout(stats_layout)

        # Splitter: Tasks | Prompts
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)

        # === Tasks Panel ===
        self.tasks_panel = GlassPanel("Tasks (0)")
        splitter.addWidget(self.tasks_panel)

        tasks_scroll = QScrollArea()
        tasks_scroll.setWidgetResizable(True)
        tasks_scroll.setFrameShape(QFrame.Shape.NoFrame)
        tasks_scroll.setStyleSheet("background: transparent;")

        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(4)
        self.tasks_layout.addStretch()

        tasks_scroll.setWidget(self.tasks_container)
        self.tasks_panel.add_widget(tasks_scroll)

        # === Prompts Panel ===
        self.prompts_panel = GlassPanel("Prompts (0)")
        splitter.addWidget(self.prompts_panel)

        prompts_scroll = QScrollArea()
        prompts_scroll.setWidgetResizable(True)
        prompts_scroll.setFrameShape(QFrame.Shape.NoFrame)
        prompts_scroll.setStyleSheet("background: transparent;")

        self.prompts_container = QWidget()
        self.prompts_layout = QVBoxLayout(self.prompts_container)
        self.prompts_layout.setContentsMargins(0, 0, 0, 0)
        self.prompts_layout.setSpacing(4)
        self.prompts_layout.addStretch()

        prompts_scroll.setWidget(self.prompts_container)
        self.prompts_panel.add_widget(prompts_scroll)

        splitter.setSizes([500, 500])

        # Log panel
        self.log_panel = LogPanel(
            title="Log",
            height=100,
            collapsible=True,
            auto_scroll=True
        )
        layout.addWidget(self.log_panel)

        # Log inicial
        self.log_panel.log("Dashboard carregado", "info")

    def on_show(self):
        """Atualiza ao exibir."""
        self.refresh()

    def refresh(self):
        """Atualiza dados."""
        if not self.task_manager:
            return

        all_items = self.task_manager.get_all_tasks()
        tasks = [t for t in all_items if t.task_type != "prompt_handler"]
        prompts = [t for t in all_items if t.task_type == "prompt_handler"]

        running_count = sum(1 for t in all_items if self.task_manager.is_task_running(t.id))
        stopped_count = len(all_items) - running_count

        # Atualiza stats
        self.stat_tasks.set_value(str(len(tasks)))
        self.stat_prompts.set_value(str(len(prompts)))
        self.stat_running.set_value(str(running_count))
        self.stat_stopped.set_value(str(stopped_count))

        # Atualiza títulos dos painéis
        self.tasks_panel.set_title(f"Tasks ({len(tasks)})")
        self.prompts_panel.set_title(f"Prompts ({len(prompts)})")

        # === Atualiza lista de tasks ===
        while self.tasks_layout.count() > 1:
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not tasks:
            placeholder = QLabel("Nenhuma task")
            placeholder.setProperty("variant", "muted")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tasks_layout.insertWidget(0, placeholder)
        else:
            for task in tasks:
                row = MiniTaskRow(
                    task=task,
                    is_running=self.task_manager.is_task_running(task.id),
                    on_play=self._on_task_play,
                    on_stop=self._on_task_stop
                )
                self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, row)

        # === Atualiza lista de prompts ===
        while self.prompts_layout.count() > 1:
            item = self.prompts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not prompts:
            placeholder = QLabel("Nenhum prompt handler")
            placeholder.setProperty("variant", "muted")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.prompts_layout.insertWidget(0, placeholder)
        else:
            for handler in prompts:
                row = MiniPromptRow(
                    handler=handler,
                    is_running=self.task_manager.is_task_running(handler.id),
                    on_play=self._on_prompt_play,
                    on_stop=self._on_prompt_stop
                )
                self.prompts_layout.insertWidget(self.prompts_layout.count() - 1, row)

    def add_log(self, message: str, level: str = "info"):
        """Adiciona mensagem ao log."""
        self.log_panel.log(message, level)

    def _start_all(self):
        """Inicia todas as tasks e prompts."""
        if self.task_manager:
            self.task_manager.start()
            self.log_panel.log("Tudo iniciado", "success")
            self.refresh()

    def _stop_all(self):
        """Para todas as tasks e prompts."""
        if self.task_manager:
            self.task_manager.stop()
            self.log_panel.log("Tudo parado", "warning")
            self.refresh()

    def _on_task_play(self, task_id: int):
        """Inicia task específica."""
        if self.task_manager:
            self.task_manager.start_single(task_id)
            self.refresh()

    def _on_task_stop(self, task_id: int):
        """Para task específica."""
        if self.task_manager:
            self.task_manager.stop_single(task_id)
            self.refresh()

    def _on_prompt_play(self, handler_id: int):
        """Inicia prompt handler."""
        if self.task_manager:
            self.task_manager.start_single(handler_id)
            self.refresh()

    def _on_prompt_stop(self, handler_id: int):
        """Para prompt handler."""
        if self.task_manager:
            self.task_manager.stop_single(handler_id)
            self.refresh()
