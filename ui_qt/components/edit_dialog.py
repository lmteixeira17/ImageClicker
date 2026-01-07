"""
Dialogs de edição para Tasks e Prompts.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QDoubleSpinBox, QCheckBox, QFrame, QLineEdit,
    QRadioButton, QButtonGroup, QWidget, QSlider
)
from PyQt6.QtCore import Qt
from pathlib import Path

from ..theme import Theme
from .icons import Icons


class EditTaskDialog(QDialog):
    """Dialog para editar uma task existente."""

    def __init__(self, task, images_dir: Path, parent=None):
        super().__init__(parent)
        self.task = task
        self.images_dir = images_dir
        self.result_data = None

        self.setWindowTitle(f"Editar Task #{task.id}")
        self.setFixedSize(400, 340)
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
        layout.setSpacing(16)

        # Title
        title = QLabel(f"{Icons.EDIT}  Editar Task #{self.task.id}")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {Theme.GLASS_BORDER};")
        layout.addWidget(sep)

        # Window info (read-only)
        window_name = self.task.process_name or self.task.window_title
        window_lbl = QLabel(f"<b>Janela:</b> {window_name}")
        window_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        layout.addWidget(window_lbl)

        # Template
        template_row = QHBoxLayout()
        template_row.setSpacing(8)

        template_lbl = QLabel("Template:")
        template_lbl.setFixedWidth(70)
        template_row.addWidget(template_lbl)

        self.template_combo = QComboBox()
        self._load_templates()
        if self.task.image_name:
            idx = self.template_combo.findText(self.task.image_name)
            if idx >= 0:
                self.template_combo.setCurrentIndex(idx)
        template_row.addWidget(self.template_combo, 1)

        layout.addLayout(template_row)

        # Action
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        action_lbl = QLabel("Ação:")
        action_lbl.setFixedWidth(70)
        action_row.addWidget(action_lbl)

        self.action_combo = QComboBox()
        self.action_combo.addItems(["click", "double_click", "right_click"])
        if self.task.action:
            idx = self.action_combo.findText(self.task.action)
            if idx >= 0:
                self.action_combo.setCurrentIndex(idx)
        action_row.addWidget(self.action_combo, 1)

        layout.addLayout(action_row)

        # Interval
        interval_row = QHBoxLayout()
        interval_row.setSpacing(8)

        interval_lbl = QLabel("Intervalo:")
        interval_lbl.setFixedWidth(70)
        interval_row.addWidget(interval_lbl)

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 3600)
        self.interval_spin.setValue(self.task.interval or 10.0)
        self.interval_spin.setSuffix("s")
        interval_row.addWidget(self.interval_spin, 1)

        layout.addLayout(interval_row)

        # Threshold
        threshold_row = QHBoxLayout()
        threshold_row.setSpacing(8)

        threshold_lbl = QLabel("Threshold:")
        threshold_lbl.setFixedWidth(70)
        threshold_row.addWidget(threshold_lbl)

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(50, 99)  # 50% a 99%
        current_threshold = int(getattr(self.task, 'threshold', 0.85) * 100)
        self.threshold_slider.setValue(current_threshold)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.threshold_slider.setTickInterval(10)
        threshold_row.addWidget(self.threshold_slider, 1)

        self.threshold_value_lbl = QLabel(f"{current_threshold}%")
        self.threshold_value_lbl.setFixedWidth(40)
        self.threshold_value_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        threshold_row.addWidget(self.threshold_value_lbl)

        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_value_lbl.setText(f"{v}%")
        )

        layout.addLayout(threshold_row)

        # Repeat
        self.repeat_check = QCheckBox("Repetir continuamente")
        self.repeat_check.setChecked(getattr(self.task, 'repeat', True))
        layout.addWidget(self.repeat_check)

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

    def _load_templates(self):
        if self.images_dir.exists():
            images = sorted(self.images_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            self.template_combo.addItems([img.stem for img in images])

    def _save(self):
        self.result_data = {
            "image_name": self.template_combo.currentText(),
            "action": self.action_combo.currentText(),
            "interval": self.interval_spin.value(),
            "repeat": self.repeat_check.isChecked(),
            "threshold": self.threshold_slider.value() / 100.0
        }
        self.accept()

    @staticmethod
    def edit(parent, task, images_dir: Path):
        """Abre dialog e retorna dados editados ou None."""
        dialog = EditTaskDialog(task, images_dir, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.result_data
        return None


class EditPromptDialog(QDialog):
    """Dialog para editar um prompt handler existente."""

    def __init__(self, handler, images_dir: Path, parent=None):
        super().__init__(parent)
        self.handler = handler
        self.images_dir = images_dir
        self.result_data = None
        self._option_rows = []

        self.setWindowTitle(f"Editar Prompt #{handler.id}")
        self.setFixedSize(500, 460)
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
        title = QLabel(f"{Icons.EDIT}  Editar Prompt Handler #{self.handler.id}")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {Theme.GLASS_BORDER};")
        layout.addWidget(sep)

        # Window info (read-only)
        window_name = self.handler.process_name or self.handler.window_title
        window_lbl = QLabel(f"<b>Janela:</b> {window_name}")
        window_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        layout.addWidget(window_lbl)

        # Interval
        interval_row = QHBoxLayout()
        interval_row.setSpacing(8)

        interval_lbl = QLabel("Intervalo:")
        interval_lbl.setFixedWidth(70)
        interval_row.addWidget(interval_lbl)

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 60)
        self.interval_spin.setValue(self.handler.interval or 1.0)
        self.interval_spin.setSuffix("s")
        interval_row.addWidget(self.interval_spin)
        interval_row.addStretch()

        layout.addLayout(interval_row)

        # Threshold
        threshold_row = QHBoxLayout()
        threshold_row.setSpacing(8)

        threshold_lbl = QLabel("Threshold:")
        threshold_lbl.setFixedWidth(70)
        threshold_row.addWidget(threshold_lbl)

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(50, 99)  # 50% a 99%
        current_threshold = int(getattr(self.handler, 'threshold', 0.85) * 100)
        self.threshold_slider.setValue(current_threshold)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.threshold_slider.setTickInterval(10)
        threshold_row.addWidget(self.threshold_slider, 1)

        self.threshold_value_lbl = QLabel(f"{current_threshold}%")
        self.threshold_value_lbl.setFixedWidth(40)
        self.threshold_value_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        threshold_row.addWidget(self.threshold_value_lbl)

        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_value_lbl.setText(f"{v}%")
        )

        layout.addLayout(threshold_row)

        # Options label
        options_lbl = QLabel("Opções de resposta:")
        options_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-weight: bold;")
        layout.addWidget(options_lbl)

        # Options container
        self.options_container = QVBoxLayout()
        self.options_container.setSpacing(6)
        layout.addLayout(self.options_container)

        # Load existing options
        self._template_names = self._get_templates()
        if self.handler.options:
            for opt in self.handler.options:
                self._add_option_row(opt.get("name", ""), opt.get("image", ""))
        else:
            self._add_option_row()
            self._add_option_row()

        # Add option button
        add_btn = QPushButton(f"{Icons.ADD} Adicionar Opção")
        add_btn.setProperty("variant", "ghost")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda: self._add_option_row())
        layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignLeft)

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

    def _get_templates(self):
        if self.images_dir.exists():
            images = sorted(self.images_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            return [img.stem for img in images]
        return []

    def _add_option_row(self, name: str = "", image: str = ""):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        name_entry = QLineEdit()
        name_entry.setPlaceholderText("Nome")
        name_entry.setText(name)
        name_entry.setFixedWidth(120)
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

    def _remove_option_row(self, row_data):
        if len(self._option_rows) <= 2:
            return
        row_data["widget"].deleteLater()
        self._option_rows.remove(row_data)

    def _save(self):
        options = []
        for row in self._option_rows:
            name = row["name_entry"].text().strip()
            template = row["template_combo"].currentText()
            if name and template:
                options.append({"name": name, "image": template})

        if len(options) < 2:
            return

        self.result_data = {
            "interval": self.interval_spin.value(),
            "threshold": self.threshold_slider.value() / 100.0,
            "options": options
        }
        self.accept()

    @staticmethod
    def edit(parent, handler, images_dir: Path):
        """Abre dialog e retorna dados editados ou None."""
        dialog = EditPromptDialog(handler, images_dir, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.result_data
        return None
