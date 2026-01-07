"""
Página Settings - Configurações.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QDoubleSpinBox, QFileDialog
)
from PyQt6.QtCore import Qt

from .base_page import BasePage
from ..components.glass_panel import GlassPanel


class SettingsPage(BasePage):
    """Página de configurações."""

    def _build_ui(self):
        self.set_title("Configurações")

        layout = self.content_layout()

        # === Diretórios ===
        dirs_panel = GlassPanel("Diretórios")
        layout.addWidget(dirs_panel)

        dirs_layout = dirs_panel.content_layout()

        # Images dir
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        label1 = QLabel("Pasta de Imagens:")
        label1.setFixedWidth(120)
        row1.addWidget(label1)

        self.images_entry = QLineEdit()
        self.images_entry.setReadOnly(True)
        row1.addWidget(self.images_entry, 1)

        browse_btn = QPushButton("📂 Alterar")
        browse_btn.clicked.connect(self._browse_images)
        row1.addWidget(browse_btn)

        dirs_layout.addLayout(row1)

        # Tasks file
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        label2 = QLabel("Arquivo Tasks:")
        label2.setFixedWidth(120)
        row2.addWidget(label2)

        self.tasks_entry = QLineEdit()
        self.tasks_entry.setReadOnly(True)
        row2.addWidget(self.tasks_entry, 1)

        dirs_layout.addLayout(row2)

        # === Template Matching ===
        match_panel = GlassPanel("Template Matching")
        layout.addWidget(match_panel)

        match_layout = match_panel.content_layout()

        row3 = QHBoxLayout()
        row3.setSpacing(8)

        label3 = QLabel("Confidence:")
        label3.setFixedWidth(120)
        row3.addWidget(label3)

        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.5, 1.0)
        self.confidence_spin.setSingleStep(0.05)
        self.confidence_spin.setValue(0.85)
        self.confidence_spin.setFixedWidth(80)
        row3.addWidget(self.confidence_spin)

        info_label = QLabel("(0.80 - 0.95 recomendado)")
        info_label.setProperty("variant", "muted")
        row3.addWidget(info_label)

        row3.addStretch()

        match_layout.addLayout(row3)

        # === Ações ===
        actions_panel = GlassPanel("Ações")
        layout.addWidget(actions_panel)

        actions_layout = actions_panel.content_layout()

        row4 = QHBoxLayout()
        row4.setSpacing(8)

        reset_btn = QPushButton("🔄 Resetar Configurações")
        reset_btn.clicked.connect(self._reset_settings)
        row4.addWidget(reset_btn)

        export_btn = QPushButton("📤 Exportar Tasks")
        export_btn.clicked.connect(self._export_tasks)
        row4.addWidget(export_btn)

        import_btn = QPushButton("📥 Importar Tasks")
        import_btn.clicked.connect(self._import_tasks)
        row4.addWidget(import_btn)

        row4.addStretch()

        actions_layout.addLayout(row4)

        # Spacer
        layout.addStretch()

        # === Info ===
        info_panel = GlassPanel("Sobre")
        layout.addWidget(info_panel)

        info_layout = info_panel.content_layout()

        version_label = QLabel("ImageClicker v2.0 - PyQt6 Edition")
        version_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(version_label)

        desc_label = QLabel("Ferramenta de automação de cliques baseada em reconhecimento de imagem.")
        desc_label.setProperty("variant", "secondary")
        info_layout.addWidget(desc_label)

    def on_show(self):
        self._load_settings()

    def _load_settings(self):
        """Carrega configurações atuais."""
        self.images_entry.setText(str(self.images_dir))
        self.tasks_entry.setText(str(self.app.tasks_file))

    def _browse_images(self):
        """Seleciona pasta de imagens."""
        folder = QFileDialog.getExistingDirectory(
            self, "Selecionar Pasta de Imagens",
            str(self.images_dir)
        )
        if folder:
            self.images_entry.setText(folder)
            # TODO: Salvar configuração

    def _reset_settings(self):
        """Reseta configurações."""
        self.confidence_spin.setValue(0.85)

    def _export_tasks(self):
        """Exporta tasks para arquivo."""
        file, _ = QFileDialog.getSaveFileName(
            self, "Exportar Tasks",
            "tasks_export.json",
            "JSON Files (*.json)"
        )
        if file:
            import shutil
            shutil.copy(self.app.tasks_file, file)
            self.log(f"Tasks exportadas para: {file}")

    def _import_tasks(self):
        """Importa tasks de arquivo."""
        file, _ = QFileDialog.getOpenFileName(
            self, "Importar Tasks",
            "",
            "JSON Files (*.json)"
        )
        if file:
            import shutil
            shutil.copy(file, self.app.tasks_file)
            self.task_manager.load_tasks(self.app.tasks_file)
            self.log(f"Tasks importadas de: {file}")
