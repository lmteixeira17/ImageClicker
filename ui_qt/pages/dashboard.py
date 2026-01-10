"""
Página Dashboard - Visão geral e estatísticas.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt

from .base_page import BasePage
from ..components.glass_panel import GlassPanel
from ..components.log_panel import LogPanel
from ..components.icons import Icons
from ..theme import Theme


class StatCard(QFrame):
    """Card de estatística - Design flat e colorido."""

    def __init__(self, icon: str, value: str, label: str, color: str = None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)  # Maior

        # Cor de fundo baseada no tipo
        bg_color = color or Theme.ACCENT_PRIMARY
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {bg_color}20;
                border: 2px solid {bg_color};
                border-radius: 12px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Ícone grande à esquerda
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 32px; color: {bg_color};")
        icon_label.setFixedWidth(45)
        layout.addWidget(icon_label)

        # Info à direita
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # Valor GRANDE
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"font-size: 36px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        info_layout.addWidget(self.value_label)

        # Label menor
        desc_label = QLabel(label)
        desc_label.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_SECONDARY};")
        info_layout.addWidget(desc_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        self._icon = icon
        self._color = bg_color

    def set_value(self, value: str):
        """Atualiza o valor do card."""
        self.value_label.setText(value)


class MiniTaskRow(QFrame):
    """Versão compacta do TaskRow para o Dashboard - Design flat e colorido."""

    def __init__(self, task, is_running: bool, on_play, on_stop, parent=None):
        super().__init__(parent)
        self.task = task
        self.is_running = is_running
        self.on_play = on_play
        self.on_stop = on_stop

        self.setFixedHeight(70)  # Maior para mais visibilidade

        # Style flat com cor baseada no status
        status_color = Theme.SUCCESS if is_running else Theme.GLASS_BORDER
        self.setStyleSheet(f"""
            MiniTaskRow {{
                background-color: {Theme.BG_GLASS};
                border: 2px solid {status_color};
                border-radius: 10px;
                border-left: 5px solid {status_color};
            }}
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 16, 10)
        main_layout.setSpacing(14)

        # Play/Stop button - MAIOR
        play_text = f"{Icons.STOP}" if is_running else f"{Icons.PLAY}"
        self.play_btn = QPushButton(play_text)
        self.play_btn.setFixedSize(44, 44)
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 18px;
                border-radius: 22px;
                background-color: {Theme.DANGER if is_running else Theme.SUCCESS};
                border: none;
            }}
            QPushButton:hover {{
                background-color: {Theme.DANGER_LIGHT if is_running else Theme.SUCCESS_LIGHT};
            }}
        """)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.clicked.connect(self._toggle)
        main_layout.addWidget(self.play_btn)

        # Status indicator - GRANDE e colorido
        self.status_dot = QLabel("●" if is_running else "○")
        color = Theme.SUCCESS if is_running else Theme.TEXT_MUTED
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 24px;")
        self.status_dot.setFixedWidth(30)
        self.status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_dot)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        # ID + Nome do processo
        window_name = task.process_name or task.window_title
        window_display = window_name[:25] + "..." if len(window_name) > 25 else window_name
        header_text = f"<span style='color:{Theme.TEXT_MUTED}'>#{task.id}</span>  <b style='font-size:15px'>{window_display}</b>"
        window_lbl = QLabel(header_text)
        window_lbl.setToolTip(window_name)
        info_layout.addWidget(window_lbl)

        threshold_pct = int(getattr(task, 'threshold', 0.85) * 100)

        # Info da task com cores vibrantes
        if task.task_type == "prompt_handler" and task.options:
            opt_names = [o["name"] for o in task.options]
            selected_name = opt_names[task.selected_option] if task.selected_option < len(opt_names) else "?"
            all_opts = ", ".join(opt_names)
            if len(all_opts) > 30:
                all_opts = all_opts[:27] + "..."
            info_text = f"<span style='color:{Theme.TEXT_SECONDARY}'>{all_opts}</span> → <b style='color:{Theme.ACCENT_PRIMARY}'>{selected_name}</b> · <span style='color:{Theme.WARNING}'>{task.interval}s</span> · <span style='color:{Theme.ACCENT_SECONDARY}'>{threshold_pct}%</span>"
        else:
            info_text = f"<b style='color:{Theme.ACCENT_PRIMARY}'>{task.image_name}</b> · <span style='color:{Theme.WARNING}'>{task.interval}s</span> · <span style='color:{Theme.ACCENT_SECONDARY}'>{threshold_pct}%</span>"

        template_lbl = QLabel(info_text)
        template_lbl.setToolTip(self._build_task_tooltip(task))
        info_layout.addWidget(template_lbl)

        main_layout.addLayout(info_layout, 1)

        # Click counter - GRANDE e destacado
        self._click_count = 0
        click_frame = QFrame()
        click_frame.setFixedWidth(50)
        click_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_GLASS_LIGHT};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        click_layout = QVBoxLayout(click_frame)
        click_layout.setContentsMargins(4, 4, 4, 4)
        click_layout.setSpacing(0)

        self.click_label = QLabel("0")
        self.click_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-weight: bold; font-size: 20px;")
        self.click_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.click_label.setToolTip("Cliques realizados")
        click_layout.addWidget(self.click_label)

        click_hint = QLabel("clicks")
        click_hint.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 9px;")
        click_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        click_layout.addWidget(click_hint)

        main_layout.addWidget(click_frame)

    def increment_click_count(self):
        """Incrementa contador de cliques com animação."""
        self._click_count += 1
        self.click_label.setText(str(self._click_count))
        self.click_label.setStyleSheet(f"color: {Theme.SUCCESS}; font-weight: bold; font-size: 22px;")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(400, lambda: self.click_label.setStyleSheet(
            f"color: {Theme.TEXT_PRIMARY}; font-weight: bold; font-size: 20px;"
        ))

    def _toggle(self):
        if self.is_running:
            self.on_stop(self.task.id)
            self.is_running = False
            self.play_btn.setText(Icons.PLAY)
            self.play_btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 18px;
                    border-radius: 22px;
                    background-color: {Theme.SUCCESS};
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {Theme.SUCCESS_LIGHT};
                }}
            """)
        else:
            self.on_play(self.task.id)
            self.is_running = True
            self.play_btn.setText(Icons.STOP)
            self.play_btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 18px;
                    border-radius: 22px;
                    background-color: {Theme.DANGER};
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {Theme.DANGER_LIGHT};
                }}
            """)

        # Atualiza status dot e borda
        self.status_dot.setText("●" if self.is_running else "○")
        color = Theme.SUCCESS if self.is_running else Theme.TEXT_MUTED
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 24px;")

        # Atualiza borda da row
        status_color = Theme.SUCCESS if self.is_running else Theme.GLASS_BORDER
        self.setStyleSheet(f"""
            MiniTaskRow {{
                background-color: {Theme.BG_GLASS};
                border: 2px solid {status_color};
                border-radius: 10px;
                border-left: 5px solid {status_color};
            }}
        """)

    def _build_task_tooltip(self, task) -> str:
        """Constrói tooltip detalhado para a task."""
        lines = [f"Task #{task.id}"]
        lines.append(f"Janela: {task.process_name or task.window_title}")

        if task.task_type == "prompt_handler" and task.options:
            lines.append(f"\nOpções ({len(task.options)}):")
            for i, opt in enumerate(task.options):
                marker = "→ " if i == task.selected_option else "   "
                lines.append(f"{marker}{opt['name']} ({opt['image']})")
        else:
            lines.append(f"Template: {task.image_name}")

        lines.append(f"\nIntervalo: {task.interval}s")
        lines.append(f"Threshold: {int(task.threshold * 100)}%")

        return "\n".join(lines)


class DashboardPage(BasePage):
    """Página de dashboard com lista unificada de tasks."""

    def __init__(self, app, parent=None):
        # Inicializa dicionários ANTES do _build_ui
        self._task_rows = {}
        self._total_clicks = 0
        super().__init__(app, parent)

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
        self.stat_running = StatCard("●", "0", "Rodando", Theme.SUCCESS)
        self.stat_stopped = StatCard("○", "0", "Parados", Theme.TEXT_MUTED)
        self.stat_clicks = StatCard("🖱", "0", "Clicks", Theme.WARNING)

        stats_layout.addWidget(self.stat_tasks)
        stats_layout.addWidget(self.stat_running)
        stats_layout.addWidget(self.stat_stopped)
        stats_layout.addWidget(self.stat_clicks)

        layout.addLayout(stats_layout)

        # Quick Actions Bar
        quick_actions = QFrame()
        quick_actions.setProperty("class", "glass-panel")
        quick_actions.setFixedHeight(50)

        qa_layout = QHBoxLayout(quick_actions)
        qa_layout.setContentsMargins(12, 8, 12, 8)
        qa_layout.setSpacing(8)

        qa_label = QLabel("Ações Rápidas")
        qa_label.setStyleSheet(f"color: {Theme.TEXT_MUTED};")  # Removido font-size hardcoded
        qa_layout.addWidget(qa_label)

        qa_layout.addSpacing(12)

        # Botão Nova Task
        new_task_btn = QPushButton(f"{Icons.ADD}  Nova Task")
        new_task_btn.setProperty("variant", "primary")
        new_task_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_task_btn.setToolTip("Ctrl+N")
        new_task_btn.clicked.connect(self._new_task)
        qa_layout.addWidget(new_task_btn)

        # Botão Capturar
        capture_btn = QPushButton(f"{Icons.CAPTURE}  Capturar")
        capture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        capture_btn.setToolTip("Ctrl+Shift+C")
        capture_btn.clicked.connect(self._capture)
        qa_layout.addWidget(capture_btn)

        qa_layout.addStretch()

        # Atalhos dica
        shortcuts_hint = QLabel("F1 ou Ctrl+H para ver atalhos")
        shortcuts_hint.setStyleSheet(f"color: {Theme.TEXT_MUTED};")  # Removido font-size hardcoded
        qa_layout.addWidget(shortcuts_hint)

        layout.addWidget(quick_actions)

        # === Tasks Panel (unified) ===
        self.tasks_panel = GlassPanel("Tasks (0)")
        layout.addWidget(self.tasks_panel, 1)

        tasks_scroll = QScrollArea()
        tasks_scroll.setWidgetResizable(True)
        tasks_scroll.setFrameShape(QFrame.Shape.NoFrame)
        tasks_scroll.setStyleSheet("background: transparent;")

        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(8)  # Aumentado de 4 para 8 (mais espaço entre tasks)
        self.tasks_layout.addStretch()

        tasks_scroll.setWidget(self.tasks_container)
        self.tasks_panel.add_widget(tasks_scroll)

        # Log panel
        self.log_panel = LogPanel(
            title="Log",
            height=100,
            collapsible=True,
            auto_scroll=True
        )
        layout.addWidget(self.log_panel)

        # Log inicial
        self.log_panel.log("Dashboard pronto", "success")

    def on_show(self):
        """Atualiza ao exibir."""
        self.refresh()

    def refresh(self):
        """Atualiza dados."""
        if not self.task_manager:
            return

        # Lista unificada de todas as tasks
        all_tasks = self.task_manager.get_all_tasks()

        running_count = sum(1 for t in all_tasks if self.task_manager.is_task_running(t.id))
        stopped_count = len(all_tasks) - running_count

        # Atualiza stats
        self.stat_tasks.set_value(str(len(all_tasks)))
        self.stat_running.set_value(str(running_count))
        self.stat_stopped.set_value(str(stopped_count))

        # Atualiza título do painel
        self.tasks_panel.set_title(f"Tasks ({len(all_tasks)})")

        # Preserva contadores de cliques existentes
        old_clicks = {tid: row._click_count for tid, row in self._task_rows.items()}

        # === Atualiza lista unificada de tasks ===
        # Limpa widgets antigos
        while self.tasks_layout.count() > 1:
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Limpa dicionário (widgets foram deletados)
        self._task_rows.clear()

        if not all_tasks:
            placeholder = QLabel("Nenhuma task")
            placeholder.setProperty("variant", "muted")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tasks_layout.insertWidget(0, placeholder)
        else:
            for task in all_tasks:
                row = MiniTaskRow(
                    task=task,
                    is_running=self.task_manager.is_task_running(task.id),
                    on_play=self._on_task_play,
                    on_stop=self._on_task_stop
                )
                # Restaura contador de cliques
                if task.id in old_clicks:
                    row._click_count = old_clicks[task.id]
                    row.click_label.setText(str(row._click_count))
                self._task_rows[task.id] = row
                self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, row)

    def add_log(self, message: str, level: str = "info"):
        """Adiciona mensagem ao log."""
        self.log_panel.log(message, level)

    def increment_click_count(self, task_id: int):
        """Incrementa contador de cliques de uma task."""
        if hasattr(self, '_task_rows') and task_id in self._task_rows:
            self._task_rows[task_id].increment_click_count()

        # Atualiza total de clicks na sessão
        self._total_clicks += 1
        self.stat_clicks.set_value(str(self._total_clicks))

    def _start_all(self):
        """Inicia todas as tasks."""
        if self.task_manager:
            self.task_manager.start()
            self.log_panel.log("Todas as tasks iniciadas", "success")
            self.refresh()

    def _stop_all(self):
        """Para todas as tasks."""
        if self.task_manager:
            self.task_manager.stop()
            self.log_panel.log("Todas as tasks paradas", "warning")
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

    def _new_task(self):
        """Navega para Tasks e abre formulário."""
        self.app.navigate("tasks")
        if hasattr(self.app._pages.get("tasks"), 'open_new_task_dialog'):
            self.app._pages["tasks"].open_new_task_dialog()

    def _capture(self):
        """Inicia captura de template."""
        self.app.start_capture()
