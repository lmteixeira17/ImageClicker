"""
Dialogs de edição para Tasks (unificado - simples e múltiplas opções).
"""

from typing import List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QDoubleSpinBox, QCheckBox, QFrame, QLineEdit,
    QRadioButton, QButtonGroup, QWidget, QSlider, QSpinBox,
    QScrollArea
)
from PyQt6.QtCore import Qt
from pathlib import Path

from ..theme import Theme
from .icons import Icons


def _get_windows_and_processes():
    """Obtém lista de janelas e processos disponíveis."""
    try:
        from core import get_windows, get_available_processes
        windows = [w[1] for w in get_windows()]
        processes = get_available_processes()
        return windows, processes
    except Exception:
        return [], []


class EditTaskDialog(QDialog):
    """Dialog unificado para editar tasks (simples ou múltiplas opções)."""

    def __init__(self, task, images_dir: Path, parent=None):
        super().__init__(parent)
        self.task = task
        self.images_dir = images_dir
        self.result_data = None
        self._option_rows = []
        self._is_multi_mode = task.task_type == "prompt_handler" and task.options

        self.setWindowTitle(f"Editar Task #{task.id}")
        self.setFixedSize(500, 550)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_PRIMARY};
                border: 1px solid {Theme.GLASS_BORDER};
                border-radius: 8px;
            }}
        """)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title
        mode_text = "Múltiplas Opções" if self._is_multi_mode else "Template Único"
        title = QLabel(f"{Icons.EDIT}  Editar Task #{self.task.id} ({mode_text})")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {Theme.GLASS_BORDER};")
        layout.addWidget(sep)

        # Window selection
        window_row = QHBoxLayout()
        window_row.setSpacing(8)

        window_lbl = QLabel("Janela:")
        window_lbl.setFixedWidth(60)
        window_row.addWidget(window_lbl)

        # Radio buttons para método
        self.method_group = QButtonGroup(self)
        self.rb_process = QRadioButton("Processo")
        self.rb_title = QRadioButton("Título")
        self.method_group.addButton(self.rb_process)
        self.method_group.addButton(self.rb_title)

        window_row.addWidget(self.rb_process)
        window_row.addWidget(self.rb_title)

        self.window_combo = QComboBox()
        self.window_combo.setEditable(True)
        self.window_combo.setToolTip("Selecione ou digite o nome\nO campo é editável")
        window_row.addWidget(self.window_combo, 1)

        # Botão refresh
        refresh_btn = QPushButton(Icons.REFRESH)
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setProperty("variant", "ghost")
        refresh_btn.setToolTip("Atualizar lista de janelas/processos")
        refresh_btn.setStyleSheet("font-size: 14px;")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh_windows)
        window_row.addWidget(refresh_btn)

        # Carrega templates
        self._template_names = self._get_templates()

        # Define método atual e popula combo
        if self.task.window_method == "process" or self.task.process_name:
            self.rb_process.setChecked(True)
            self._current_value = self.task.process_name or ""
        else:
            self.rb_title.setChecked(True)
            self._current_value = self.task.window_title or ""

        # Carrega janelas/processos e popula combo
        self._refresh_windows()

        self.rb_process.toggled.connect(self._on_method_changed)

        layout.addLayout(window_row)

        # === Seção específica do modo ===
        if self._is_multi_mode:
            self._build_multi_mode_section(layout)
        else:
            self._build_single_mode_section(layout)

        # === Configurações comuns ===
        config_frame = QFrame()
        config_frame.setStyleSheet(f"background: {Theme.BG_GLASS}; border-radius: 6px;")
        config_layout = QVBoxLayout(config_frame)
        config_layout.setContentsMargins(12, 12, 12, 12)
        config_layout.setSpacing(8)

        # Action
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        action_lbl = QLabel("Ação:")
        action_lbl.setFixedWidth(60)
        action_row.addWidget(action_lbl)
        self.action_combo = QComboBox()
        self.action_combo.addItems(["click", "double_click", "right_click"])
        if self.task.action:
            idx = self.action_combo.findText(self.task.action)
            if idx >= 0:
                self.action_combo.setCurrentIndex(idx)
        action_row.addWidget(self.action_combo)
        action_row.addStretch()
        config_layout.addLayout(action_row)

        # Interval
        interval_row = QHBoxLayout()
        interval_row.setSpacing(8)
        interval_lbl = QLabel("Intervalo:")
        interval_lbl.setFixedWidth(60)
        interval_row.addWidget(interval_lbl)
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 3600)
        self.interval_spin.setValue(self.task.interval or 10.0)
        self.interval_spin.setSuffix("s")
        self.interval_spin.setFixedWidth(100)
        interval_row.addWidget(self.interval_spin)
        interval_row.addStretch()
        config_layout.addLayout(interval_row)

        # Threshold
        threshold_row = QHBoxLayout()
        threshold_row.setSpacing(8)
        threshold_lbl = QLabel("Threshold:")
        threshold_lbl.setFixedWidth(60)
        threshold_row.addWidget(threshold_lbl)
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(50, 99)
        current_threshold = int(getattr(self.task, 'threshold', 0.85) * 100)
        self.threshold_slider.setValue(current_threshold)
        threshold_row.addWidget(self.threshold_slider, 1)
        self.threshold_value_lbl = QLabel(f"{current_threshold}%")
        self.threshold_value_lbl.setFixedWidth(40)
        self.threshold_value_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        threshold_row.addWidget(self.threshold_value_lbl)
        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_value_lbl.setText(f"{v}%")
        )
        config_layout.addLayout(threshold_row)

        # Repeat (só para modo simples)
        if not self._is_multi_mode:
            self.repeat_check = QCheckBox("Repetir continuamente")
            self.repeat_check.setChecked(getattr(self.task, 'repeat', True))
            config_layout.addWidget(self.repeat_check)

        layout.addWidget(config_frame)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton(f"{Icons.SUCCESS}  Salvar")
        save_btn.setProperty("variant", "primary")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _build_single_mode_section(self, layout):
        """Constrói seção para modo template único."""
        template_row = QHBoxLayout()
        template_row.setSpacing(8)

        template_lbl = QLabel("Template:")
        template_lbl.setFixedWidth(60)
        template_row.addWidget(template_lbl)

        self.template_combo = QComboBox()
        self.template_combo.addItems(self._template_names)
        if self.task.image_name:
            idx = self.template_combo.findText(self.task.image_name)
            if idx >= 0:
                self.template_combo.setCurrentIndex(idx)
        template_row.addWidget(self.template_combo, 1)

        layout.addLayout(template_row)

    def _build_multi_mode_section(self, layout):
        """Constrói seção para modo múltiplas opções."""
        # Label
        options_lbl = QLabel("Opções de resposta:")
        options_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-weight: bold;")
        layout.addWidget(options_lbl)

        # Container com scroll para opções
        options_frame = QFrame()
        options_frame.setStyleSheet(f"background: {Theme.BG_GLASS}; border-radius: 6px;")
        options_frame.setMaximumHeight(150)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        self.options_container = QVBoxLayout(scroll_content)
        self.options_container.setContentsMargins(8, 8, 8, 8)
        self.options_container.setSpacing(6)

        scroll.setWidget(scroll_content)

        frame_layout = QVBoxLayout(options_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(scroll)

        # Carrega opções existentes
        if self.task.options:
            for opt in self.task.options:
                self._add_option_row(opt.get("name", ""), opt.get("image", ""))

        layout.addWidget(options_frame)

        # Botão adicionar opção
        add_btn = QPushButton(f"{Icons.ADD} Adicionar Opção")
        add_btn.setProperty("variant", "ghost")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda: self._add_option_row())
        layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # Resposta padrão
        resp_row = QHBoxLayout()
        resp_row.setSpacing(8)
        resp_lbl = QLabel("Resposta padrão:")
        resp_lbl.setFixedWidth(100)
        resp_row.addWidget(resp_lbl)
        self.response_combo = QComboBox()
        self.response_combo.setMinimumWidth(120)
        self._update_response_combo()
        if self.task.selected_option < self.response_combo.count():
            self.response_combo.setCurrentIndex(self.task.selected_option)
        resp_row.addWidget(self.response_combo)
        resp_row.addStretch()
        layout.addLayout(resp_row)

    def _add_option_row(self, name: str = "", image: str = ""):
        """Adiciona uma linha de opção."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        name_entry = QLineEdit()
        name_entry.setPlaceholderText("Nome")
        name_entry.setText(name)
        name_entry.setFixedWidth(100)
        name_entry.textChanged.connect(self._update_response_combo)
        row_layout.addWidget(name_entry)

        template_combo = QComboBox()
        template_combo.addItems(self._template_names)
        if image and image in self._template_names:
            template_combo.setCurrentText(image)
        row_layout.addWidget(template_combo, 1)

        remove_btn = QPushButton(Icons.DELETE)
        remove_btn.setFixedSize(28, 28)
        remove_btn.setProperty("variant", "ghost")
        remove_btn.setStyleSheet(f"font-size: 14px; color: {Theme.TEXT_MUTED};")
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        row_layout.addWidget(remove_btn)

        row_data = {
            "widget": row_widget,
            "name_entry": name_entry,
            "template_combo": template_combo
        }

        remove_btn.clicked.connect(lambda: self._remove_option_row(row_data))

        self._option_rows.append(row_data)
        self.options_container.addWidget(row_widget)
        self._update_response_combo()

    def _remove_option_row(self, row_data):
        """Remove uma linha de opção."""
        if len(self._option_rows) <= 2:
            return
        row_data["widget"].deleteLater()
        self._option_rows.remove(row_data)
        self._update_response_combo()

    def _update_response_combo(self):
        """Atualiza combo de resposta padrão."""
        if not hasattr(self, 'response_combo'):
            return
        current = self.response_combo.currentText()
        self.response_combo.clear()

        for i, row in enumerate(self._option_rows):
            name = row["name_entry"].text() or f"Opção {i + 1}"
            self.response_combo.addItem(name)

        idx = self.response_combo.findText(current)
        if idx >= 0:
            self.response_combo.setCurrentIndex(idx)

    def _get_templates(self):
        """Carrega lista de templates."""
        if self.images_dir.exists():
            images = sorted(self.images_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            return [img.stem for img in images]
        return []

    def _refresh_windows(self):
        """Atualiza lista de janelas/processos."""
        current_text = self.window_combo.currentText() or getattr(self, '_current_value', '')
        self.window_combo.clear()

        # Carrega janelas e processos atuais
        windows, processes = _get_windows_and_processes()

        if self.rb_process.isChecked():
            self.window_combo.addItems(processes)
        else:
            self.window_combo.addItems(windows)

        # Seleciona o valor atual
        idx = self.window_combo.findText(current_text)
        if idx >= 0:
            self.window_combo.setCurrentIndex(idx)
        elif current_text:
            self.window_combo.setCurrentText(current_text)

    def _on_method_changed(self):
        """Atualiza combo quando método de janela muda."""
        self._refresh_windows()

    def _save(self):
        window_value = self.window_combo.currentText().strip()

        self.result_data = {
            "action": self.action_combo.currentText(),
            "interval": self.interval_spin.value(),
            "threshold": self.threshold_slider.value() / 100.0,
            "window_method": "process" if self.rb_process.isChecked() else "title",
            "window_title": window_value if self.rb_title.isChecked() else "",
            "process_name": window_value if self.rb_process.isChecked() else ""
        }

        if self._is_multi_mode:
            # Modo múltiplas opções
            options = []
            for row in self._option_rows:
                name = row["name_entry"].text().strip()
                template = row["template_combo"].currentText()
                if name and template:
                    options.append({"name": name, "image": template})

            if len(options) < 2:
                return  # Precisa de pelo menos 2 opções

            self.result_data["options"] = options
            self.result_data["selected_option"] = self.response_combo.currentIndex()
            self.result_data["repeat"] = True  # Múltiplas sempre repetem
            self.result_data["image_name"] = ""
        else:
            # Modo template único
            self.result_data["image_name"] = self.template_combo.currentText()
            self.result_data["repeat"] = self.repeat_check.isChecked()
            self.result_data["options"] = None
            self.result_data["selected_option"] = 0

        self.accept()

    @staticmethod
    def edit(parent, task, images_dir: Path):
        """Abre dialog e retorna dados editados ou None."""
        dialog = EditTaskDialog(task, images_dir, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.result_data
        return None


# Alias para compatibilidade - EditPromptDialog agora usa EditTaskDialog
EditPromptDialog = EditTaskDialog
