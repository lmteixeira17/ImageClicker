"""
Página Tasks - Gerenciamento unificado de tasks.
Suporta tasks simples (template único) e múltiplas opções (antigo prompt_handler).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QLineEdit, QRadioButton,
    QButtonGroup, QCheckBox, QDoubleSpinBox, QSpinBox, QGridLayout
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

    def __init__(self, app, parent=None):
        self._task_rows = {}  # Inicializa antes do _build_ui
        super().__init__(app, parent)

    def _build_ui(self):
        self.set_title("Tasks")

        # Inicializa lista de opções para modo múltiplas
        self._option_rows = []

        # Botões header
        self.start_all_btn = QPushButton(f"{Icons.PLAY}  Todas")
        self.start_all_btn.setProperty("variant", "success")
        self.start_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_all_btn.setToolTip("Iniciar todas as tasks (Ctrl+E)\nInicia o monitoramento de todas as tasks configuradas")
        self.start_all_btn.clicked.connect(self._start_all)
        self.add_header_widget(self.start_all_btn)

        self.stop_all_btn = QPushButton(f"{Icons.STOP}  Parar")
        self.stop_all_btn.setProperty("variant", "danger")
        self.stop_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_all_btn.setToolTip("Parar todas as tasks (Shift+S)\nInterrompe o monitoramento de todas as tasks")
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
        self.rb_process.setToolTip("Buscar por nome do processo (ex: Code, Safari)\nRecomendado: funciona mesmo se o título da janela mudar")
        self.rb_title = QRadioButton("Título")
        self.rb_title.setToolTip("Buscar por título da janela\nÚtil quando múltiplos processos têm o mesmo nome")
        self.method_group.addButton(self.rb_process)
        self.method_group.addButton(self.rb_title)
        self.rb_process.toggled.connect(self._refresh_windows)

        row1.addWidget(self.rb_process)
        row1.addWidget(self.rb_title)

        self.window_combo = QComboBox()
        self.window_combo.setMinimumWidth(200)
        self.window_combo.setToolTip("Selecione a janela/processo alvo\nA task vai monitorar esta janela buscando o template")
        row1.addWidget(self.window_combo, 1)

        refresh_btn = QPushButton(Icons.REFRESH)
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setProperty("variant", "ghost")
        refresh_btn.setToolTip("Atualizar lista de janelas/processos\nClique se abriu uma nova janela após carregar a página")
        refresh_btn.setStyleSheet("font-size: 16px;")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh_windows)
        row1.addWidget(refresh_btn)

        form.addLayout(row1)

        # Row 2: Modo de operação
        row_mode = QHBoxLayout()
        row_mode.setSpacing(8)

        label_mode = QLabel("Modo:")
        label_mode.setFixedWidth(50)
        row_mode.addWidget(label_mode)

        self.mode_group = QButtonGroup(self)
        self.rb_single = QRadioButton("Template Único")
        self.rb_single.setChecked(True)
        self.rb_single.setToolTip("Monitora uma única imagem\nClica sempre que encontrar o template na janela")
        self.rb_multiple = QRadioButton("Múltiplas Opções")
        self.rb_multiple.setToolTip("Monitora múltiplas imagens simultaneamente\nClica na opção selecionada quando TODAS estiverem visíveis\nIdeal para responder prompts/diálogos automaticamente")
        self.mode_group.addButton(self.rb_single)
        self.mode_group.addButton(self.rb_multiple)
        self.rb_single.toggled.connect(self._toggle_mode)

        row_mode.addWidget(self.rb_single)
        row_mode.addWidget(self.rb_multiple)
        row_mode.addStretch()

        form.addLayout(row_mode)

        # === Seção Template Único ===
        self.single_section = QFrame()
        self.single_section.setStyleSheet(f"background: {Theme.BG_GLASS}; border-radius: 6px; padding: 8px;")
        single_layout = QVBoxLayout(self.single_section)
        single_layout.setContentsMargins(8, 8, 8, 8)
        single_layout.setSpacing(8)

        row2 = QHBoxLayout()
        row2.setSpacing(8)

        label2 = QLabel("Template:")
        label2.setFixedWidth(50)
        row2.addWidget(label2)

        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(150)
        self.template_combo.setToolTip("Imagem a ser encontrada na janela\nCapture novos templates com o botão ao lado")
        row2.addWidget(self.template_combo)

        capture_btn = QPushButton(f"{Icons.CAPTURE} Capturar")
        capture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        capture_btn.setToolTip("Capturar novo template (Ctrl+Shift+C)\nSelecione uma região da tela para criar um novo template")
        capture_btn.clicked.connect(self._capture)
        row2.addWidget(capture_btn)

        row2.addSpacing(16)

        label3 = QLabel("Ação:")
        row2.addWidget(label3)

        self.action_combo = QComboBox()
        self.action_combo.addItems(["click", "double_click", "right_click"])
        self.action_combo.setFixedWidth(100)
        self.action_combo.setToolTip("Tipo de clique a executar:\n• click: Clique simples (mais comum)\n• double_click: Duplo clique\n• right_click: Clique direito (menu contexto)")
        row2.addWidget(self.action_combo)

        label4 = QLabel("Intervalo:")
        row2.addWidget(label4)

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 3600)
        self.interval_spin.setValue(10.0)
        self.interval_spin.setSuffix("s")
        self.interval_spin.setFixedWidth(80)
        self.interval_spin.setToolTip("Tempo entre cada verificação (em segundos)\nValores menores = mais responsivo, mas usa mais CPU\nRecomendado: 1-10s para a maioria dos casos")
        row2.addWidget(self.interval_spin)

        self.repeat_check = QCheckBox("Repetir")
        self.repeat_check.setChecked(True)
        self.repeat_check.setToolTip("Continua monitorando após o primeiro clique\nDesmarque para clicar apenas uma vez")
        row2.addWidget(self.repeat_check)

        row2.addStretch()
        single_layout.addLayout(row2)

        # Threshold para modo único
        row_threshold = QHBoxLayout()
        row_threshold.setSpacing(8)
        threshold_label = QLabel("Threshold:")
        threshold_label.setFixedWidth(50)
        row_threshold.addWidget(threshold_label)
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(50, 99)
        self.threshold_spin.setValue(85)
        self.threshold_spin.setSuffix("%")
        self.threshold_spin.setFixedWidth(70)
        self.threshold_spin.setToolTip("Precisão mínima para considerar um match\n• 85%: Padrão, bom equilíbrio\n• 90%+: Mais preciso, menos falsos positivos\n• 70-80%: Mais tolerante, para imagens que variam")
        row_threshold.addWidget(self.threshold_spin)
        row_threshold.addStretch()
        single_layout.addLayout(row_threshold)

        form.addWidget(self.single_section)

        # === Seção Múltiplas Opções ===
        self.multi_section = QFrame()
        self.multi_section.setStyleSheet(f"background: {Theme.BG_GLASS}; border-radius: 6px; padding: 8px;")
        self.multi_section.setVisible(False)
        multi_layout = QVBoxLayout(self.multi_section)
        multi_layout.setContentsMargins(8, 8, 8, 8)
        multi_layout.setSpacing(8)

        # Header com labels
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        name_header = QLabel("Nome")
        name_header.setFixedWidth(120)
        name_header.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-weight: bold;")
        header_row.addWidget(name_header)
        template_header = QLabel("Template")
        template_header.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-weight: bold;")
        header_row.addWidget(template_header)
        header_row.addStretch()
        multi_layout.addLayout(header_row)

        # Container para opções
        self.options_container = QVBoxLayout()
        self.options_container.setSpacing(4)
        multi_layout.addLayout(self.options_container)

        # Botão adicionar opção
        add_option_btn = QPushButton(f"{Icons.ADD} Adicionar Opção")
        add_option_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_option_btn.setToolTip("Adicionar mais uma opção ao prompt\nCada opção representa um botão/resposta possível")
        add_option_btn.clicked.connect(self._add_option_row)
        multi_layout.addWidget(add_option_btn)

        # Resposta padrão + configurações
        config_row = QHBoxLayout()
        config_row.setSpacing(8)

        resp_label = QLabel("Resposta padrão:")
        config_row.addWidget(resp_label)
        self.response_combo = QComboBox()
        self.response_combo.setMinimumWidth(120)
        self.response_combo.setToolTip("Qual opção clicar automaticamente\nQuando TODAS as opções estiverem visíveis, clica nesta")
        config_row.addWidget(self.response_combo)

        config_row.addSpacing(16)

        label_action2 = QLabel("Ação:")
        config_row.addWidget(label_action2)
        self.multi_action_combo = QComboBox()
        self.multi_action_combo.addItems(["click", "double_click", "right_click"])
        self.multi_action_combo.setFixedWidth(100)
        self.multi_action_combo.setToolTip("Tipo de clique a executar:\n• click: Clique simples (mais comum)\n• double_click: Duplo clique\n• right_click: Clique direito")
        config_row.addWidget(self.multi_action_combo)

        label_interval2 = QLabel("Intervalo:")
        config_row.addWidget(label_interval2)
        self.multi_interval_spin = QDoubleSpinBox()
        self.multi_interval_spin.setRange(0.1, 3600)
        self.multi_interval_spin.setValue(1.0)
        self.multi_interval_spin.setSuffix("s")
        self.multi_interval_spin.setFixedWidth(80)
        self.multi_interval_spin.setToolTip("Tempo entre cada verificação\nPara prompts, 1-2s é recomendado")
        config_row.addWidget(self.multi_interval_spin)

        label_threshold2 = QLabel("Threshold:")
        config_row.addWidget(label_threshold2)
        self.multi_threshold_spin = QSpinBox()
        self.multi_threshold_spin.setRange(50, 99)
        self.multi_threshold_spin.setValue(85)
        self.multi_threshold_spin.setSuffix("%")
        self.multi_threshold_spin.setFixedWidth(70)
        self.multi_threshold_spin.setToolTip("Precisão mínima para detectar cada opção\nTodas as opções precisam atingir este threshold")
        config_row.addWidget(self.multi_threshold_spin)

        config_row.addStretch()
        multi_layout.addLayout(config_row)

        form.addWidget(self.multi_section)

        # Botão Adicionar (comum)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        add_btn = QPushButton(f"{Icons.ADD} Adicionar Task")
        add_btn.setProperty("variant", "primary")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setToolTip("Criar nova task com as configurações acima\nA task será adicionada à lista e pode ser iniciada")
        add_btn.clicked.connect(self._add_task)
        btn_row.addWidget(add_btn)
        form.addLayout(btn_row)

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

        # Carrega tasks inicial
        self._refresh_tasks()

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
        self._template_names = []
        if self.images_dir.exists():
            images = sorted(self.images_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            self._template_names = [img.stem for img in images]
            self.template_combo.addItems(self._template_names)

            # Atualiza combos nas linhas de opção existentes
            for row in self._option_rows:
                current = row["template"].currentText()
                row["template"].clear()
                row["template"].addItems(self._template_names)
                idx = row["template"].findText(current)
                if idx >= 0:
                    row["template"].setCurrentIndex(idx)

    def _toggle_mode(self, checked: bool):
        """Alterna entre modo único e múltiplas opções."""
        if checked:  # Template único selecionado
            self.single_section.setVisible(True)
            self.multi_section.setVisible(False)
        else:  # Múltiplas opções selecionado
            self.single_section.setVisible(False)
            self.multi_section.setVisible(True)
            # Adiciona 2 opções iniciais se não houver nenhuma
            if len(self._option_rows) == 0:
                self._add_option_row()
                self._add_option_row()

    def _add_option_row(self):
        """Adiciona uma nova linha de opção."""
        row_frame = QFrame()
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        # Nome da opção
        name_edit = QLineEdit()
        name_edit.setFixedWidth(120)
        name_edit.setPlaceholderText(f"Opção {len(self._option_rows) + 1}")
        name_edit.setToolTip("Nome descritivo para esta opção\nExemplo: 'Sim', 'Não', 'Cancelar'")
        name_edit.textChanged.connect(self._update_response_combo)
        row_layout.addWidget(name_edit)

        # Template combo
        template_combo = QComboBox()
        template_combo.setMinimumWidth(150)
        template_combo.setToolTip("Template que representa esta opção\nCapture a imagem do botão correspondente")
        if hasattr(self, '_template_names'):
            template_combo.addItems(self._template_names)
        row_layout.addWidget(template_combo, 1)

        # Botão remover
        remove_btn = QPushButton(Icons.DELETE)
        remove_btn.setFixedSize(28, 28)
        remove_btn.setProperty("variant", "ghost")
        remove_btn.setToolTip("Remover esta opção")
        remove_btn.setStyleSheet(f"color: {Theme.DANGER}; font-size: 14px;")
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.clicked.connect(lambda: self._remove_option_row(row_frame))
        row_layout.addWidget(remove_btn)

        self._option_rows.append({
            "frame": row_frame,
            "name": name_edit,
            "template": template_combo
        })

        self.options_container.addWidget(row_frame)
        self._update_response_combo()

    def _remove_option_row(self, row_frame: QFrame):
        """Remove uma linha de opção."""
        for i, row in enumerate(self._option_rows):
            if row["frame"] == row_frame:
                row_frame.deleteLater()
                self._option_rows.pop(i)
                self._update_response_combo()
                break

    def _update_response_combo(self):
        """Atualiza combo de resposta padrão com nomes das opções."""
        current = self.response_combo.currentText()
        self.response_combo.clear()

        for i, row in enumerate(self._option_rows):
            name = row["name"].text() or f"Opção {i + 1}"
            self.response_combo.addItem(name)

        # Restaura seleção se possível
        idx = self.response_combo.findText(current)
        if idx >= 0:
            self.response_combo.setCurrentIndex(idx)

    def _get_options_from_form(self):
        """Extrai opções do formulário."""
        options = []
        for i, row in enumerate(self._option_rows):
            name = row["name"].text() or f"Opção {i + 1}"
            template = row["template"].currentText()
            if template:  # Só adiciona se tem template selecionado
                options.append({"name": name, "image": template})
        return options

    def _clear_option_rows(self):
        """Limpa todas as linhas de opção."""
        for row in self._option_rows:
            row["frame"].deleteLater()
        self._option_rows.clear()
        self._update_response_combo()

    def _refresh_tasks(self):
        """Atualiza lista de tasks."""
        if not self.task_manager:
            return

        # Mostra TODAS as tasks (unificado)
        tasks = self.task_manager.get_all_tasks()

        # Update panel title
        self.tasks_panel.set_title(f"Tasks ({len(tasks)})")

        # Preserva contadores de cliques existentes
        old_clicks = {tid: row._click_count for tid, row in self._task_rows.items()}

        # Limpa widgets antigos
        while self.tasks_layout.count() > 1:
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._task_rows.clear()

        if not tasks:
            self.tasks_layout.insertWidget(0, self.placeholder)
            return

        self.placeholder.setParent(None)

        for task in tasks:
            # Determina nome da imagem/opções para exibição
            if task.task_type == "prompt_handler" and task.options:
                selected_name = task.options[task.selected_option]["name"] if task.selected_option < len(task.options) else "?"
                image_display = f"{len(task.options)} opções: {selected_name}"
                options = task.options
                selected_option = task.selected_option
            else:
                image_display = task.image_name
                options = None
                selected_option = 0

            row = TaskRow(
                task_id=task.id,
                window_name=task.process_name or task.window_title,
                image_name=image_display,
                action=task.action,
                interval=task.interval,
                threshold=task.threshold,
                is_running=self.task_manager.is_task_running(task.id),
                status="Rodando" if self.task_manager.is_task_running(task.id) else "Parado",
                options=options,
                selected_option=selected_option
            )
            row.play_clicked.connect(self._on_play)
            row.stop_clicked.connect(self._on_stop)
            row.edit_clicked.connect(self._on_edit)
            row.delete_clicked.connect(self._on_delete)
            row.simulate_clicked.connect(self._on_simulate)
            row.option_changed.connect(self._on_option_changed)

            # Restaura contador de cliques
            if task.id in old_clicks:
                row.set_click_count(old_clicks[task.id])

            self._task_rows[task.id] = row
            self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, row)

    def increment_click_count(self, task_id: int):
        """Incrementa contador de cliques de uma task."""
        if hasattr(self, '_task_rows') and task_id in self._task_rows:
            self._task_rows[task_id].increment_click_count()

    def _add_task(self):
        """Adiciona nova task (modo único ou múltiplas opções)."""
        window = self.window_combo.currentText()

        if not window:
            if hasattr(self.app, 'toast'):
                self.app.toast.warning("Selecione uma janela")
            return

        # Determina método de seleção de janela
        window_method = "process" if self.rb_process.isChecked() else "title"

        if self.rb_single.isChecked():
            # === Modo Template Único ===
            template = self.template_combo.currentText()
            action = self.action_combo.currentText()
            interval = self.interval_spin.value()
            repeat = self.repeat_check.isChecked()
            threshold = self.threshold_spin.value() / 100.0

            if not template:
                if hasattr(self.app, 'toast'):
                    self.app.toast.warning("Selecione um template")
                return

            self.task_manager.add_task(
                window_title="" if window_method == "process" else window,
                image_name=template,
                action=action,
                interval=interval,
                repeat=repeat,
                threshold=threshold,
                window_method=window_method,
                process_name=window if window_method == "process" else ""
            )
        else:
            # === Modo Múltiplas Opções ===
            options = self._get_options_from_form()

            if len(options) < 2:
                if hasattr(self.app, 'toast'):
                    self.app.toast.warning("Adicione pelo menos 2 opções com templates")
                return

            action = self.multi_action_combo.currentText()
            interval = self.multi_interval_spin.value()
            threshold = self.multi_threshold_spin.value() / 100.0
            selected_option = self.response_combo.currentIndex()

            self.task_manager.add_task(
                window_title="" if window_method == "process" else window,
                image_name="",
                action=action,
                interval=interval,
                repeat=True,  # Múltiplas opções sempre repetem
                threshold=threshold,
                window_method=window_method,
                process_name=window if window_method == "process" else "",
                options=options,
                selected_option=selected_option
            )

            # Limpa opções após criar
            self._clear_option_rows()

        self.task_manager.save_tasks(self.app.tasks_file)
        self._refresh_tasks()

        if hasattr(self.app, 'toast'):
            self.app.toast.success("Task criada com sucesso")

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

    def _on_option_changed(self, task_id: int, option_index: int):
        """Callback quando opção selecionada muda em task com múltiplas opções."""
        if self.task_manager:
            self.task_manager.set_selected_option(task_id, option_index)
            self.task_manager.save_tasks(self.app.tasks_file)

    def _on_edit(self, task_id: int):
        """Abre dialog de edição da task."""
        if not self.task_manager:
            return

        task = self.task_manager.get_task(task_id)
        if not task:
            return

        result = EditTaskDialog.edit(self, task, self.images_dir)
        if result:
            # Atualiza campos comuns
            task.action = result["action"]
            task.interval = result["interval"]
            task.repeat = result["repeat"]
            task.threshold = result.get("threshold", 0.85)

            # Atualiza campos específicos do modo
            task.image_name = result.get("image_name", "")
            task.options = result.get("options")
            task.selected_option = result.get("selected_option", 0)

            # Atualiza janela se fornecido
            if "window_method" in result:
                task.window_method = result["window_method"]
                task.window_title = result.get("window_title", "")
                task.process_name = result.get("process_name", "")

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

    def _on_simulate(self, task_id: int):
        """Simula execução da task sem clicar."""
        if not self.task_manager:
            return

        task = self.task_manager.get_task(task_id)
        if not task:
            return

        # Mostra toast de início
        if hasattr(self.app, 'toast'):
            self.app.toast.info(f"Simulando Task #{task_id}...")

        try:
            from core.image_matcher import check_template_visible, find_template_location
            from core.window_utils import find_window_by_process, find_window_by_title, find_all_windows_by_process, find_all_windows_by_title, get_window_title

            # Encontra janela(s)
            if task.window_method == "process":
                all_windows = find_all_windows_by_process(task.process_name, task.title_filter if task.title_filter else None)
                window_display = task.process_name
            else:
                all_windows = find_all_windows_by_title(task.window_title)
                window_display = task.window_title[:30]

            if not all_windows:
                self.log(f"{Icons.WARNING} Task #{task_id}: Janela '{window_display}' não encontrada", "warning")
                if hasattr(self.app, 'toast'):
                    self.app.toast.warning(f"Janela não encontrada: {window_display}")
                return

            # === Simulação baseada no tipo de task ===
            if task.task_type == "prompt_handler" and task.options:
                # Modo múltiplas opções - verifica todas
                self._simulate_multi_options(task, all_windows)
            else:
                # Modo template único
                self._simulate_single_template(task, all_windows)

        except Exception as e:
            self.log(f"{Icons.ERROR} Erro ao simular: {e}", "error")
            if hasattr(self.app, 'toast'):
                self.app.toast.error(f"Erro: {str(e)[:50]}")

    def _simulate_single_template(self, task, all_windows):
        """Simula busca de template único."""
        from core.image_matcher import check_template_visible, find_template_location
        from core.window_utils import get_window_title

        template_path = self.images_dir / f"{task.image_name}.png"
        if not template_path.exists():
            self.log(f"{Icons.ERROR} Task #{task.id}: Template '{task.image_name}' não existe", "error")
            if hasattr(self.app, 'toast'):
                self.app.toast.error(f"Template não existe: {task.image_name}")
            return

        best_match = 0.0
        best_window = None
        found_location = None

        for window_id in all_windows:
            try:
                window_title = get_window_title(window_id)
                visible, match = check_template_visible(window_id, template_path, threshold=task.threshold)

                if match > best_match:
                    best_match = match
                    best_window = (window_id, window_title)

                if visible:
                    found_location = find_template_location(window_id, template_path)
                    break
            except Exception:
                continue

        conf_pct = int(best_match * 100)
        threshold_pct = int(task.threshold * 100)

        if found_location and best_window:
            x, y, w, h = found_location
            center_x = x + w // 2
            center_y = y + h // 2

            quality = self._get_quality_label(best_match)
            window_name = best_window[1][:25] + "..." if len(best_window[1]) > 25 else best_window[1]

            self.log(f"{Icons.SUCCESS} Task #{task.id}: ENCONTRADO em '{window_name}'", "success")
            self.log(f"   Posição: ({center_x}, {center_y}) | Precisão: {conf_pct}% ({quality}) | Threshold: {threshold_pct}%", "success")

            if hasattr(self.app, 'toast'):
                self.app.toast.success(f"Encontrado! {conf_pct}% em '{window_name}'")

            # NÃO move cursor - apenas log (Ghost Click não rouba foco)
        else:
            window_name = best_window[1][:25] if best_window else "?"
            self.log(f"{Icons.WARNING} Task #{task.id}: NÃO ENCONTRADO", "warning")
            self.log(f"   Melhor match: {conf_pct}% em '{window_name}' (threshold: {threshold_pct}%)", "warning")

            if hasattr(self.app, 'toast'):
                self.app.toast.warning(f"Não encontrado (melhor: {conf_pct}%)")

    def _simulate_multi_options(self, task, all_windows):
        """Simula busca de múltiplas opções."""
        from core.image_matcher import check_template_visible, find_template_location
        from core.window_utils import get_window_title

        if not task.options:
            return

        total_options = len(task.options)
        threshold_pct = int(task.threshold * 100)

        for window_id in all_windows:
            try:
                window_title = get_window_title(window_id)
                window_name = window_title[:25] + "..." if len(window_title) > 25 else window_title

                visible_count = 0
                results = []

                for opt in task.options:
                    template_path = self.images_dir / f"{opt['image']}.png"
                    if not template_path.exists():
                        results.append((opt['name'], 0, False, "Template não existe"))
                        continue

                    visible, match = check_template_visible(window_id, template_path, threshold=task.threshold)
                    conf_pct = int(match * 100)

                    if visible:
                        visible_count += 1
                        location = find_template_location(window_id, template_path)
                        if location:
                            x, y, w, h = location
                            results.append((opt['name'], conf_pct, True, f"({x + w//2}, {y + h//2})"))
                        else:
                            results.append((opt['name'], conf_pct, True, ""))
                    else:
                        results.append((opt['name'], conf_pct, False, ""))

                # Mostra resultados
                if visible_count == total_options:
                    self.log(f"{Icons.SUCCESS} Task #{task.id}: PROMPT CONFIRMADO em '{window_name}'", "success")
                    self.log(f"   Todas as {total_options} opções visíveis (threshold: {threshold_pct}%)", "success")

                    # Mostra cada opção
                    for name, conf, vis, pos in results:
                        status = f"{Icons.SUCCESS} {conf}%" + (f" {pos}" if pos else "")
                        self.log(f"   - {name}: {status}", "success")

                    # Mostra qual seria clicada
                    selected = task.options[task.selected_option]['name']
                    self.log(f"   → Resposta selecionada: {selected}", "success")

                    if hasattr(self.app, 'toast'):
                        self.app.toast.success(f"Prompt confirmado! Clicaria em '{selected}'")

                    # NÃO move cursor - apenas log (Ghost Click não rouba foco)
                    return

                elif visible_count > 0:
                    self.log(f"{Icons.WARNING} Task #{task.id}: PARCIAL em '{window_name}'", "warning")
                    self.log(f"   {visible_count}/{total_options} opções visíveis (threshold: {threshold_pct}%)", "warning")

                    for name, conf, vis, pos in results:
                        icon = Icons.SUCCESS if vis else Icons.ERROR
                        status = f"{conf}%" + (f" {pos}" if pos else "")
                        self.log(f"   - {name}: {icon} {status}", "warning" if not vis else "info")

            except Exception:
                continue

        # Nenhuma janela teve match
        self.log(f"{Icons.WARNING} Task #{task.id}: Nenhuma opção encontrada em nenhuma janela", "warning")
        if hasattr(self.app, 'toast'):
            self.app.toast.warning("Nenhuma opção encontrada")

    def _get_quality_label(self, match_value: float) -> str:
        """Retorna label de qualidade baseado no valor de match."""
        if match_value >= 0.90:
            return "Excelente"
        elif match_value >= 0.85:
            return "Bom"
        elif match_value >= 0.75:
            return "Aceitável"
        else:
            return "Baixo"

    def open_new_task_dialog(self):
        """Abre formulário para nova task (chamado por atalho)."""
        # Atualiza combos
        self._refresh_windows()
        self._refresh_templates()

        # Foca no primeiro combo para facilitar preenchimento
        self.window_combo.setFocus()

        # Mostra toast de ajuda
        if hasattr(self.app, 'toast'):
            self.app.toast.info("Preencha o formulário para criar uma nova task")
