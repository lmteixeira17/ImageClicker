"""
Página Tasks - Gerenciamento de tasks.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QLineEdit, QRadioButton,
    QButtonGroup, QCheckBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt

from .base_page import BasePage
from ..components.glass_panel import GlassPanel
from ..components.task_row import TaskRow
from ..components.confirm_dialog import ConfirmDialog
from ..components.edit_dialog import EditTaskDialog
from ..components.icons import Icons
from ..theme import Theme


class TasksPage(BasePage):
    """Página de gerenciamento de tasks."""

    def _build_ui(self):
        self.set_title("Tasks")

        # Botões header
        self.start_all_btn = QPushButton(f"{Icons.PLAY}  Todas")
        self.start_all_btn.setProperty("variant", "success")
        self.start_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_all_btn.clicked.connect(self._start_all)
        self.add_header_widget(self.start_all_btn)

        self.stop_all_btn = QPushButton(f"{Icons.STOP}  Parar")
        self.stop_all_btn.setProperty("variant", "danger")
        self.stop_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_all_btn.clicked.connect(self._stop_all)
        self.add_header_widget(self.stop_all_btn)

        layout = self.content_layout()

        # === Formulário Adicionar ===
        form_panel = GlassPanel("Adicionar Task")
        layout.addWidget(form_panel)

        form = form_panel.content_layout()

        # Row 1: Método + Janela
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        label = QLabel("Janela:")
        label.setFixedWidth(50)
        row1.addWidget(label)

        self.method_group = QButtonGroup(self)
        self.rb_process = QRadioButton("Processo")
        self.rb_process.setChecked(True)
        self.rb_title = QRadioButton("Título")
        self.method_group.addButton(self.rb_process)
        self.method_group.addButton(self.rb_title)
        self.rb_process.toggled.connect(self._refresh_windows)

        row1.addWidget(self.rb_process)
        row1.addWidget(self.rb_title)

        self.window_combo = QComboBox()
        self.window_combo.setMinimumWidth(200)
        row1.addWidget(self.window_combo, 1)

        refresh_btn = QPushButton(Icons.REFRESH)
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setProperty("variant", "ghost")
        refresh_btn.setToolTip("Atualizar lista")
        refresh_btn.setStyleSheet("font-size: 16px;")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh_windows)
        row1.addWidget(refresh_btn)

        form.addLayout(row1)

        # Row 2: Template + Ação + Intervalo
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        label2 = QLabel("Template:")
        label2.setFixedWidth(50)
        row2.addWidget(label2)

        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(150)
        row2.addWidget(self.template_combo)

        capture_btn = QPushButton(f"{Icons.CAPTURE} Capturar")
        capture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        capture_btn.clicked.connect(self._capture)
        row2.addWidget(capture_btn)

        row2.addSpacing(16)

        label3 = QLabel("Ação:")
        row2.addWidget(label3)

        self.action_combo = QComboBox()
        self.action_combo.addItems(["click", "double_click", "right_click"])
        self.action_combo.setFixedWidth(100)
        row2.addWidget(self.action_combo)

        label4 = QLabel("Intervalo:")
        row2.addWidget(label4)

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 3600)
        self.interval_spin.setValue(10.0)
        self.interval_spin.setSuffix("s")
        self.interval_spin.setFixedWidth(80)
        row2.addWidget(self.interval_spin)

        self.repeat_check = QCheckBox("Repetir")
        self.repeat_check.setChecked(True)
        row2.addWidget(self.repeat_check)

        row2.addStretch()

        add_btn = QPushButton(f"{Icons.ADD} Adicionar")
        add_btn.setProperty("variant", "primary")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_task)
        row2.addWidget(add_btn)

        form.addLayout(row2)

        # === Lista de Tasks ===
        self.tasks_panel = GlassPanel("Tasks (0)")
        layout.addWidget(self.tasks_panel, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(8)
        self.tasks_layout.addStretch()

        scroll.setWidget(self.tasks_container)
        self.tasks_panel.add_widget(scroll)

        # Placeholder
        self.placeholder = QLabel("Nenhuma task configurada\n\nAdicione tasks usando o formulário acima.")
        self.placeholder.setProperty("variant", "muted")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def on_show(self):
        self._refresh_windows()
        self._refresh_templates()
        self._refresh_tasks()

    def refresh(self):
        self._refresh_tasks()

    def _refresh_windows(self):
        """Atualiza lista de janelas."""
        from core import get_windows, get_available_processes

        self.window_combo.clear()

        if self.rb_process.isChecked():
            processes = get_available_processes()
            self.window_combo.addItems(processes)
        else:
            windows = get_windows()
            titles = [w[1] for w in windows]
            self.window_combo.addItems(titles)

    def _refresh_templates(self):
        """Atualiza lista de templates."""
        self.template_combo.clear()
        if self.images_dir.exists():
            images = sorted(self.images_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            self.template_combo.addItems([img.stem for img in images])

    def _refresh_tasks(self):
        """Atualiza lista de tasks."""
        if not self.task_manager:
            return

        tasks = [t for t in self.task_manager.get_all_tasks() if t.task_type != "prompt_handler"]

        # Update panel title
        self.tasks_panel.set_title(f"Tasks ({len(tasks)})")

        # Limpa
        while self.tasks_layout.count() > 1:
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not tasks:
            self.tasks_layout.insertWidget(0, self.placeholder)
            return

        self.placeholder.setParent(None)

        for task in tasks:
            row = TaskRow(
                task_id=task.id,
                window_name=task.process_name or task.window_title,
                image_name=task.image_name,
                action=task.action,
                interval=task.interval,
                threshold=task.threshold,
                is_running=self.task_manager.is_task_running(task.id),
                status="Rodando" if self.task_manager.is_task_running(task.id) else "Parado"
            )
            row.play_clicked.connect(self._on_play)
            row.stop_clicked.connect(self._on_stop)
            row.edit_clicked.connect(self._on_edit)
            row.delete_clicked.connect(self._on_delete)

            self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, row)

    def _add_task(self):
        """Adiciona nova task."""
        window = self.window_combo.currentText()
        template = self.template_combo.currentText()
        action = self.action_combo.currentText()
        interval = self.interval_spin.value()
        repeat = self.repeat_check.isChecked()

        if not window or not template:
            return

        if self.rb_process.isChecked():
            self.task_manager.add_task(
                window_title="",
                image_name=template,
                action=action,
                interval=interval,
                repeat=repeat,
                window_method="process",
                process_name=window
            )
        else:
            self.task_manager.add_task(
                window_title=window,
                image_name=template,
                action=action,
                interval=interval,
                repeat=repeat,
                window_method="title"
            )

        self.task_manager.save_tasks(self.app.tasks_file)
        self._refresh_tasks()

    def _capture(self):
        """Inicia captura."""
        self.app.start_capture()

    def _start_all(self):
        if self.task_manager:
            self.task_manager.start()
            self._refresh_tasks()

    def _stop_all(self):
        if self.task_manager:
            self.task_manager.stop()
            self._refresh_tasks()

    def _on_play(self, task_id: int):
        if self.task_manager:
            self.task_manager.start_single(task_id)
            self._refresh_tasks()

    def _on_stop(self, task_id: int):
        if self.task_manager:
            self.task_manager.stop_single(task_id)
            self._refresh_tasks()

    def _on_edit(self, task_id: int):
        """Abre dialog de edição da task."""
        if not self.task_manager:
            return

        task = self.task_manager.get_task(task_id)
        if not task:
            return

        result = EditTaskDialog.edit(self, task, self.images_dir)
        if result:
            # Atualiza task
            task.image_name = result["image_name"]
            task.action = result["action"]
            task.interval = result["interval"]
            task.repeat = result["repeat"]
            task.threshold = result.get("threshold", 0.85)

            self.task_manager.save_tasks(self.app.tasks_file)
            self._refresh_tasks()

    def _on_delete(self, task_id: int):
        """Remove task com confirmação."""
        if ConfirmDialog.confirm(
            self,
            title="Excluir Task",
            message=f"Tem certeza que deseja excluir a task #{task_id}?\n\nEsta ação não pode ser desfeita.",
            danger=True
        ):
            if self.task_manager:
                self.task_manager.remove_task(task_id)
                self.task_manager.save_tasks(self.app.tasks_file)
                self._refresh_tasks()
