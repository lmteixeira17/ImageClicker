"""
Página Prompts - Gerenciamento de prompt handlers.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QLineEdit, QRadioButton,
    QButtonGroup, QDoubleSpinBox
)
from PyQt6.QtCore import Qt

from .base_page import BasePage
from ..components.glass_panel import GlassPanel
from ..components.confirm_dialog import ConfirmDialog
from ..components.edit_dialog import EditPromptDialog
from ..components.icons import Icons
from ..theme import Theme


class PromptHandlerRow(QFrame):
    """Card de prompt handler com informações claras."""

    def __init__(self, handler, is_running: bool, on_play, on_stop, on_option_change, on_edit, on_delete, parent=None):
        super().__init__(parent)
        self.handler = handler
        self.is_running = is_running
        self.on_play = on_play
        self.on_stop = on_stop
        self.on_option_change = on_option_change
        self.on_edit = on_edit
        self.on_delete = on_delete

        self.setProperty("class", "task-row")

        # Altura dinâmica baseada no número de opções
        num_options = len(handler.options) if handler.options else 0
        height = 80 + (num_options * 28)
        self.setMinimumHeight(height)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(12)

        # === Play/Stop button ===
        play_text = f"{Icons.STOP}  Parar" if is_running else f"{Icons.PLAY}  Iniciar"
        self.play_btn = QPushButton(play_text)
        self.play_btn.setFixedSize(90, 38)
        self.play_btn.setProperty("variant", "danger" if is_running else "success")
        self.play_btn.setToolTip("Parar" if is_running else "Iniciar")
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setStyleSheet("font-size: 13px; font-weight: bold;")
        self.play_btn.clicked.connect(self._toggle)
        main_layout.addWidget(self.play_btn, alignment=Qt.AlignmentFlag.AlignTop)

        # === ID + Status ===
        id_frame = QFrame()
        id_frame.setFixedWidth(45)
        id_layout = QVBoxLayout(id_frame)
        id_layout.setContentsMargins(0, 0, 0, 0)
        id_layout.setSpacing(2)

        id_label = QLabel(f"#{handler.id}")
        id_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        id_layout.addWidget(id_label)

        self.status_dot = QLabel(Icons.RUNNING if is_running else Icons.STOPPED)
        self.status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = Theme.STATUS_RUNNING if is_running else Theme.STATUS_STOPPED
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 14px;")
        id_layout.addWidget(self.status_dot)

        id_layout.addStretch()
        main_layout.addWidget(id_frame, alignment=Qt.AlignmentFlag.AlignTop)

        # === Separator ===
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"background: {Theme.GLASS_BORDER}; max-width: 1px;")
        main_layout.addWidget(sep)

        # === Info section ===
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(6)

        # Window name
        window_name = handler.process_name or handler.window_title
        window_lbl = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Janela:</b> {window_name}")
        window_lbl.setToolTip(window_name)
        info_layout.addWidget(window_lbl)

        # Interval + Threshold
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(24)

        interval_lbl = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Intervalo:</b> {handler.interval}s")
        settings_layout.addWidget(interval_lbl)

        threshold_pct = int(getattr(handler, 'threshold', 0.85) * 100)
        threshold_lbl = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Threshold:</b> {threshold_pct}%")
        settings_layout.addWidget(threshold_lbl)

        settings_layout.addStretch()
        info_layout.addLayout(settings_layout)

        # Options section
        if handler.options:
            options_label = QLabel(f"<b style='color:{Theme.TEXT_SECONDARY}'>Opções de resposta:</b>")
            info_layout.addWidget(options_label)

            self.option_group = QButtonGroup(self)
            for idx, opt in enumerate(handler.options):
                opt_frame = QFrame()
                opt_layout = QHBoxLayout(opt_frame)
                opt_layout.setContentsMargins(16, 2, 0, 2)
                opt_layout.setSpacing(10)

                rb = QRadioButton()
                rb.setFixedSize(18, 18)
                if idx == handler.selected_option:
                    rb.setChecked(True)
                rb.toggled.connect(lambda checked, i=idx: self._on_option(i) if checked else None)
                self.option_group.addButton(rb, idx)
                opt_layout.addWidget(rb)

                # Option info
                opt_name = QLabel(f"<b>{opt['name']}</b>")
                opt_layout.addWidget(opt_name)

                opt_template = QLabel(f"→ Template: <span style='color:{Theme.ACCENT_PRIMARY}'>{opt['image']}</span>")
                opt_layout.addWidget(opt_template)

                opt_layout.addStretch()
                info_layout.addWidget(opt_frame)

        main_layout.addWidget(info_frame, 1)

        # === Action buttons ===
        actions_frame = QFrame()
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(4)

        edit_btn = QPushButton(Icons.EDIT)
        edit_btn.setFixedSize(36, 36)
        edit_btn.setProperty("variant", "ghost")
        edit_btn.setStyleSheet(f"font-size: 16px; color: {Theme.ACCENT_PRIMARY};")
        edit_btn.setToolTip("Editar handler")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda: on_edit(handler.id))
        actions_layout.addWidget(edit_btn)

        delete_btn = QPushButton(Icons.DELETE)
        delete_btn.setFixedSize(36, 36)
        delete_btn.setProperty("variant", "ghost")
        delete_btn.setStyleSheet(f"font-size: 18px; color: {Theme.DANGER};")
        delete_btn.setToolTip("Excluir handler")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(lambda: on_delete(handler.id))
        actions_layout.addWidget(delete_btn)

        actions_layout.addStretch()
        main_layout.addWidget(actions_frame, alignment=Qt.AlignmentFlag.AlignTop)

    def _toggle(self):
        if self.is_running:
            self.on_stop(self.handler.id)
            self.is_running = False
            self.play_btn.setText(f"{Icons.PLAY}  Iniciar")
            self.play_btn.setProperty("variant", "success")
            self.play_btn.setToolTip("Iniciar")
        else:
            self.on_play(self.handler.id)
            self.is_running = True
            self.play_btn.setText(f"{Icons.STOP}  Parar")
            self.play_btn.setProperty("variant", "danger")
            self.play_btn.setToolTip("Parar")

        self.play_btn.style().unpolish(self.play_btn)
        self.play_btn.style().polish(self.play_btn)

        self.status_dot.setText(Icons.RUNNING if self.is_running else Icons.STOPPED)
        color = Theme.STATUS_RUNNING if self.is_running else Theme.STATUS_STOPPED
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 14px;")

    def _on_option(self, idx: int):
        self.on_option_change(self.handler.id, idx)


class PromptsPage(BasePage):
    """Página de prompt handlers."""

    def __init__(self, app, parent=None):
        self._option_rows = []
        super().__init__(app, parent)

    def _build_ui(self):
        self.set_title("Prompt Handlers")

        layout = self.content_layout()

        # === Formulário ===
        form_panel = GlassPanel("Novo Prompt Handler")
        layout.addWidget(form_panel)

        form = form_panel.content_layout()

        # Row 1: Janela
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

        # Options label
        opt_label = QLabel("Opções de Resposta:")
        opt_label.setProperty("variant", "secondary")
        form.addWidget(opt_label)

        # Options container
        self.options_container = QVBoxLayout()
        self.options_container.setSpacing(4)
        form.addLayout(self.options_container)

        # Add option button
        add_opt_btn = QPushButton(f"{Icons.ADD} Adicionar Opção")
        add_opt_btn.setProperty("variant", "ghost")
        add_opt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_opt_btn.clicked.connect(self._add_option_row)
        form.addWidget(add_opt_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # Row bottom: Interval + Create
        row_bottom = QHBoxLayout()
        row_bottom.setSpacing(8)

        label2 = QLabel("Intervalo:")
        row_bottom.addWidget(label2)

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 60)
        self.interval_spin.setValue(1.0)
        self.interval_spin.setSuffix("s")
        self.interval_spin.setFixedWidth(80)
        row_bottom.addWidget(self.interval_spin)

        row_bottom.addStretch()

        create_btn = QPushButton(f"{Icons.ADD} Criar Handler")
        create_btn.setProperty("variant", "primary")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self._create_handler)
        row_bottom.addWidget(create_btn)

        form.addLayout(row_bottom)

        # Initial options
        self._add_option_row()
        self._add_option_row()

        # === Lista de Handlers ===
        self.handlers_panel = GlassPanel("Prompt Handlers (0)")
        layout.addWidget(self.handlers_panel, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.handlers_container = QWidget()
        self.handlers_layout = QVBoxLayout(self.handlers_container)
        self.handlers_layout.setContentsMargins(0, 0, 0, 0)
        self.handlers_layout.setSpacing(8)
        self.handlers_layout.addStretch()

        scroll.setWidget(self.handlers_container)
        self.handlers_panel.add_widget(scroll)

        self.placeholder = QLabel("Nenhum prompt handler configurado")
        self.placeholder.setProperty("variant", "muted")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def on_show(self):
        self._refresh_windows()
        self._refresh_templates()
        self._refresh_handlers()

    def refresh(self):
        self._refresh_handlers()

    def _refresh_windows(self):
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
        self._template_names = []
        if self.images_dir.exists():
            images = sorted(self.images_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            self._template_names = [img.stem for img in images]

        # Update combos in option rows
        for row in self._option_rows:
            combo = row.get("template_combo")
            if combo:
                current = combo.currentText()
                combo.clear()
                combo.addItems(self._template_names)
                if current in self._template_names:
                    combo.setCurrentText(current)

    def _add_option_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        name_entry = QLineEdit()
        name_entry.setPlaceholderText("Nome")
        name_entry.setFixedWidth(100)
        row_layout.addWidget(name_entry)

        template_combo = QComboBox()
        template_combo.setMinimumWidth(150)
        template_combo.addItems(getattr(self, "_template_names", []))
        row_layout.addWidget(template_combo)

        remove_btn = QPushButton(Icons.DELETE)
        remove_btn.setFixedSize(28, 28)
        remove_btn.setProperty("variant", "ghost")
        remove_btn.setStyleSheet(f"font-size: 14px; color: {Theme.TEXT_MUTED};")
        remove_btn.setToolTip("Remover opção")
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        row_layout.addWidget(remove_btn)

        row_layout.addStretch()

        row_data = {
            "widget": row_widget,
            "name_entry": name_entry,
            "template_combo": template_combo
        }

        remove_btn.clicked.connect(lambda: self._remove_option_row(row_data))

        self._option_rows.append(row_data)
        self.options_container.addWidget(row_widget)

    def _remove_option_row(self, row_data):
        if len(self._option_rows) <= 2:
            return

        row_data["widget"].deleteLater()
        self._option_rows.remove(row_data)

    def _create_handler(self):
        window = self.window_combo.currentText()
        interval = self.interval_spin.value()

        options = []
        for row in self._option_rows:
            name = row["name_entry"].text().strip()
            template = row["template_combo"].currentText()
            if name and template:
                options.append({"name": name, "image": template})

        if not window:
            return

        if len(options) < 2:
            return

        if self.rb_process.isChecked():
            self.task_manager.add_prompt_handler(
                window_title="",
                options=options,
                interval=interval,
                window_method="process",
                process_name=window
            )
        else:
            self.task_manager.add_prompt_handler(
                window_title=window,
                options=options,
                interval=interval,
                window_method="title"
            )

        self.task_manager.save_tasks(self.app.tasks_file)
        self._refresh_handlers()

        # Clear form
        for row in self._option_rows:
            row["name_entry"].clear()

    def _refresh_handlers(self):
        if not self.task_manager:
            return

        handlers = [t for t in self.task_manager.get_all_tasks() if t.task_type == "prompt_handler"]

        # Update panel title
        self.handlers_panel.set_title(f"Prompt Handlers ({len(handlers)})")

        # Clear
        while self.handlers_layout.count() > 1:
            item = self.handlers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not handlers:
            self.handlers_layout.insertWidget(0, self.placeholder)
            return

        self.placeholder.setParent(None)

        for handler in handlers:
            row = PromptHandlerRow(
                handler=handler,
                is_running=self.task_manager.is_task_running(handler.id),
                on_play=lambda tid: self.task_manager.start_single(tid),
                on_stop=lambda tid: self.task_manager.stop_single(tid),
                on_option_change=lambda tid, idx: self.task_manager.set_selected_option(tid, idx),
                on_edit=self._edit_handler,
                on_delete=self._delete_handler
            )
            self.handlers_layout.insertWidget(self.handlers_layout.count() - 1, row)

    def _edit_handler(self, handler_id: int):
        """Abre dialog de edição do handler."""
        if not self.task_manager:
            return

        handler = self.task_manager.get_task(handler_id)
        if not handler:
            return

        result = EditPromptDialog.edit(self, handler, self.images_dir)
        if result:
            # Atualiza handler
            handler.interval = result["interval"]
            handler.threshold = result.get("threshold", 0.85)
            handler.options = result["options"]

            self.task_manager.save_tasks(self.app.tasks_file)
            self._refresh_handlers()

    def _delete_handler(self, task_id: int):
        """Remove handler com confirmação."""
        if ConfirmDialog.confirm(
            self,
            title="Excluir Handler",
            message=f"Tem certeza que deseja excluir o prompt handler #{task_id}?\n\nEsta ação não pode ser desfeita.",
            danger=True
        ):
            self.task_manager.remove_task(task_id)
            self.task_manager.save_tasks(self.app.tasks_file)
            self._refresh_handlers()
