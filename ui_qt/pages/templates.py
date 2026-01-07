"""
Página Templates - Galeria de imagens.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QSplitter, QFileDialog,
    QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QImage
from pathlib import Path

from .base_page import BasePage
from ..components.glass_panel import GlassPanel
from ..components.confirm_dialog import ConfirmDialog
from ..components.icons import Icons
from ..theme import Theme


class ImageThumbnail(QFrame):
    """Thumbnail de imagem clicável."""

    def __init__(self, image_path: Path, on_click=None, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.on_click = on_click
        self._selected = False

        self.setProperty("class", "glass-panel")
        self.setFixedSize(116, 100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Imagem
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedHeight(70)
        self._load_image()
        layout.addWidget(self.image_label)

        # Nome
        name = image_path.stem
        display_name = name[:14] + "…" if len(name) > 14 else name
        name_label = QLabel(display_name)
        name_label.setProperty("variant", "secondary")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 10px;")
        name_label.setToolTip(name)
        layout.addWidget(name_label)

    def _load_image(self):
        """Carrega e redimensiona imagem."""
        try:
            pixmap = QPixmap(str(self.image_path))
            scaled = pixmap.scaled(
                100, 60,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
        except Exception as e:
            self.image_label.setText(Icons.ERROR)

    def mousePressEvent(self, event):
        if self.on_click:
            self.on_click(self.image_path)

    def mouseDoubleClickEvent(self, event):
        import subprocess
        subprocess.Popen(f'explorer /select,"{self.image_path}"')

    def set_selected(self, selected: bool):
        self._selected = selected
        if selected:
            self.setStyleSheet(f"border: 2px solid {Theme.ACCENT_PRIMARY};")
        else:
            self.setStyleSheet("")


class TemplatesPage(BasePage):
    """Página de galeria de templates."""

    def __init__(self, app, parent=None):
        self._selected_path = None
        self._thumbnails = {}
        super().__init__(app, parent)

    def _build_ui(self):
        self.set_title("Templates")

        # Capturar button
        capture_btn = QPushButton(f"{Icons.CAPTURE} Capturar")
        capture_btn.setProperty("variant", "primary")
        capture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        capture_btn.clicked.connect(self._capture)
        self.add_header_widget(capture_btn)

        layout = self.content_layout()

        # Splitter: Galeria | Preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)

        # === Galeria ===
        gallery_panel = GlassPanel("Galeria")
        splitter.addWidget(gallery_panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.gallery_widget = QWidget()
        self.gallery_layout = QGridLayout(self.gallery_widget)
        self.gallery_layout.setSpacing(8)
        self.gallery_layout.setContentsMargins(4, 4, 4, 4)
        self.gallery_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self.gallery_widget)
        gallery_panel.add_widget(scroll)

        # === Preview ===
        preview_panel = GlassPanel("Preview")
        preview_panel.setFixedWidth(280)
        splitter.addWidget(preview_panel)

        preview_layout = preview_panel.content_layout()

        # Preview image
        preview_frame = QFrame()
        preview_frame.setStyleSheet(f"background: {Theme.BG_DARKER}; border-radius: 4px;")
        preview_frame.setFixedHeight(180)
        preview_frame_layout = QVBoxLayout(preview_frame)

        self.preview_label = QLabel("Selecione uma imagem")
        self.preview_label.setProperty("variant", "muted")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_frame_layout.addWidget(self.preview_label)

        preview_layout.addWidget(preview_frame)

        # Info
        self.name_label = QLabel("")
        self.name_label.setStyleSheet("font-weight: bold;")
        preview_layout.addWidget(self.name_label)

        self.size_label = QLabel("")
        self.size_label.setProperty("variant", "secondary")
        preview_layout.addWidget(self.size_label)

        preview_layout.addSpacing(8)

        # Ações
        self.test_btn = QPushButton(f"{Icons.SUCCESS} Testar")
        self.test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.test_btn.clicked.connect(self._test_template)
        self.test_btn.setEnabled(False)
        preview_layout.addWidget(self.test_btn)

        self.rename_btn = QPushButton(f"{Icons.EDIT} Renomear")
        self.rename_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rename_btn.clicked.connect(self._rename_template)
        self.rename_btn.setEnabled(False)
        preview_layout.addWidget(self.rename_btn)

        self.delete_btn = QPushButton(f"{Icons.DELETE} Excluir")
        self.delete_btn.setProperty("variant", "danger")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.clicked.connect(self._delete_template)
        self.delete_btn.setEnabled(False)
        preview_layout.addWidget(self.delete_btn)

        open_btn = QPushButton(f"{Icons.FOLDER} Abrir Pasta")
        open_btn.setProperty("variant", "ghost")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(self._open_folder)
        preview_layout.addWidget(open_btn)

        preview_layout.addStretch()

        splitter.setSizes([500, 280])

    def on_show(self):
        self.refresh()

    def refresh(self):
        """Recarrega galeria."""
        # Limpa
        for thumb in self._thumbnails.values():
            thumb.deleteLater()
        self._thumbnails.clear()

        if not self.images_dir.exists():
            return

        images = sorted(
            self.images_dir.glob("*.png"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        cols = 3
        for idx, img_path in enumerate(images):
            row = idx // cols
            col = idx % cols

            thumb = ImageThumbnail(img_path, on_click=self._on_select)
            self.gallery_layout.addWidget(thumb, row, col)
            self._thumbnails[img_path] = thumb

    def _on_select(self, path: Path):
        """Seleciona imagem."""
        # Deseleciona anterior
        if self._selected_path and self._selected_path in self._thumbnails:
            self._thumbnails[self._selected_path].set_selected(False)

        self._selected_path = path

        if path in self._thumbnails:
            self._thumbnails[path].set_selected(True)

        # Atualiza preview
        try:
            pixmap = QPixmap(str(path))
            scaled = pixmap.scaled(
                240, 160,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)

            self.name_label.setText(path.name)
            self.size_label.setText(f"{pixmap.width()} x {pixmap.height()} px")

            self.test_btn.setEnabled(True)
            self.rename_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)

        except Exception as e:
            self.log(f"Erro ao carregar preview: {e}", "error")

    def _capture(self):
        """Inicia captura."""
        self.app.start_capture()

    def _test_template(self):
        """Testa template na tela."""
        if not self._selected_path:
            return

        self.log(f"Testando template: {self._selected_path.stem}...")

        try:
            import pyautogui
            location = pyautogui.locateOnScreen(str(self._selected_path), confidence=0.85)

            if location:
                self.log(f"{Icons.SUCCESS} Encontrado em: {location}", "success")
            else:
                self.log(f"{Icons.ERROR} Não encontrado na tela", "warning")
        except Exception as e:
            self.log(f"Erro: {e}", "error")

    def _rename_template(self):
        """Renomeia template."""
        if not self._selected_path:
            return

        new_name, ok = QInputDialog.getText(
            self, "Renomear Template",
            "Novo nome:",
            text=self._selected_path.stem
        )

        if ok and new_name and new_name != self._selected_path.stem:
            new_path = self._selected_path.parent / f"{new_name}.png"

            if new_path.exists():
                QMessageBox.warning(self, "Erro", "Já existe um template com esse nome.")
                return

            try:
                self._selected_path.rename(new_path)
                self.log(f"Renomeado: {self._selected_path.stem} → {new_name}")
                self._selected_path = new_path
                self.refresh()
            except Exception as e:
                self.log(f"Erro ao renomear: {e}", "error")

    def _delete_template(self):
        """Exclui template com confirmação."""
        if not self._selected_path:
            return

        if ConfirmDialog.confirm(
            self,
            title="Excluir Template",
            message=f"Tem certeza que deseja excluir '{self._selected_path.stem}'?\n\nEsta ação não pode ser desfeita.",
            danger=True
        ):
            try:
                self._selected_path.unlink()
                self.log(f"Template excluído: {self._selected_path.stem}")
                self._selected_path = None
                self._clear_preview()
                self.refresh()
            except Exception as e:
                self.log(f"Erro ao excluir: {e}", "error")

    def _clear_preview(self):
        """Limpa preview."""
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("Selecione uma imagem")
        self.name_label.setText("")
        self.size_label.setText("")
        self.test_btn.setEnabled(False)
        self.rename_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def _open_folder(self):
        """Abre pasta de imagens."""
        import subprocess
        subprocess.Popen(f'explorer "{self.images_dir}"')
