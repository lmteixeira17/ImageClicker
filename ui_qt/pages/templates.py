"""
Página Templates - Galeria de imagens.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QSplitter, QFileDialog,
    QInputDialog, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QPixmap, QImage
from pathlib import Path

from .base_page import BasePage
from ..components.glass_panel import GlassPanel
from ..components.confirm_dialog import ConfirmDialog
from ..components.icons import Icons
from ..theme import Theme


class ImageThumbnail(QFrame):
    """Thumbnail de imagem clicável com hover preview."""

    # Tamanho aumentado (era 116x100)
    THUMB_WIDTH = 150
    THUMB_HEIGHT = 130
    IMG_HEIGHT = 95

    def __init__(self, image_path: Path, on_click=None, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.on_click = on_click
        self._selected = False
        self._hover_preview = None

        self.setProperty("class", "glass-panel")
        self.setFixedSize(self.THUMB_WIDTH, self.THUMB_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Imagem
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedHeight(self.IMG_HEIGHT)
        self._load_image()
        layout.addWidget(self.image_label)

        # Nome
        name = image_path.stem
        display_name = name[:18] + "…" if len(name) > 18 else name
        name_label = QLabel(display_name)
        name_label.setProperty("variant", "secondary")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 11px;")
        name_label.setToolTip(f"{name}\nClique para selecionar\nDuplo-clique para abrir no Finder")
        layout.addWidget(name_label)

    def _load_image(self):
        """Carrega e redimensiona imagem."""
        try:
            pixmap = QPixmap(str(self.image_path))
            scaled = pixmap.scaled(
                self.THUMB_WIDTH - 12, self.IMG_HEIGHT - 10,
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
        # macOS: abre Finder com arquivo selecionado
        subprocess.run(['open', '-R', str(self.image_path)])

    def set_selected(self, selected: bool):
        self._selected = selected
        if selected:
            self.setStyleSheet(f"border: 2px solid {Theme.ACCENT_PRIMARY};")
        else:
            self.setStyleSheet("")

    def enterEvent(self, event):
        """Mostra preview ampliado no hover."""
        self._show_hover_preview()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Esconde preview ampliado."""
        self._hide_hover_preview()
        super().leaveEvent(event)

    def _show_hover_preview(self):
        """Mostra popup com imagem ampliada."""
        if self._hover_preview:
            return

        try:
            pixmap = QPixmap(str(self.image_path))

            # Limita tamanho máximo do preview
            max_size = 300
            if pixmap.width() > max_size or pixmap.height() > max_size:
                scaled = pixmap.scaled(
                    max_size, max_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                scaled = pixmap

            self._hover_preview = QLabel()
            self._hover_preview.setPixmap(scaled)
            self._hover_preview.setWindowFlags(
                Qt.WindowType.ToolTip |
                Qt.WindowType.FramelessWindowHint
            )
            self._hover_preview.setStyleSheet(f"""
                background: {Theme.BG_PRIMARY};
                border: 2px solid {Theme.ACCENT_PRIMARY};
                border-radius: 8px;
                padding: 8px;
            """)

            # Posiciona ao lado do thumbnail
            pos = self.mapToGlobal(self.rect().topRight())
            self._hover_preview.move(pos.x() + 10, pos.y())
            self._hover_preview.show()

        except Exception:
            pass

    def _hide_hover_preview(self):
        """Esconde popup de preview."""
        if self._hover_preview:
            self._hover_preview.hide()
            self._hover_preview.deleteLater()
            self._hover_preview = None


class FlowLayout(QVBoxLayout):
    """Layout que organiza widgets em linhas, quebrando automaticamente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._spacing = 8

    def addFlowWidget(self, widget):
        """Adiciona widget ao flow."""
        self._items.append(widget)

    def clearFlow(self):
        """Remove todos os widgets."""
        self._items.clear()
        # Remove layouts filhos
        while self.count() > 0:
            item = self.takeAt(0)
            if item.layout():
                while item.layout().count() > 0:
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().setParent(None)

    def doLayout(self, width):
        """Reorganiza widgets baseado na largura disponível."""
        if not self._items:
            return

        # Remove layouts anteriores
        while self.count() > 0:
            item = self.takeAt(0)
            if item.layout():
                # Não deleta os widgets, só remove do layout
                while item.layout().count() > 0:
                    item.layout().takeAt(0)

        # Calcula quantos cabem por linha
        item_width = ImageThumbnail.THUMB_WIDTH + self._spacing
        cols = max(1, (width - 20) // item_width)

        # Cria linhas
        current_row = QHBoxLayout()
        current_row.setSpacing(self._spacing)
        current_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        col_count = 0

        for widget in self._items:
            if col_count >= cols:
                current_row.addStretch()
                self.addLayout(current_row)
                current_row = QHBoxLayout()
                current_row.setSpacing(self._spacing)
                current_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
                col_count = 0

            current_row.addWidget(widget)
            col_count += 1

        # Adiciona última linha
        if col_count > 0:
            current_row.addStretch()
            self.addLayout(current_row)

        self.addStretch()


class TemplatesPage(BasePage):
    """Página de galeria de templates."""

    def __init__(self, app, parent=None):
        self._selected_path = None
        self._thumbnails = {}
        self._gallery_width = 0
        super().__init__(app, parent)

    def _build_ui(self):
        self.set_title("Templates")

        # Capturar button
        capture_btn = QPushButton(f"{Icons.CAPTURE} Capturar")
        capture_btn.setProperty("variant", "primary")
        capture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        capture_btn.setToolTip("Capturar nova imagem da tela (Ctrl+Shift+C)\nSelecione uma região para criar um novo template")
        capture_btn.clicked.connect(self._capture)
        self.add_header_widget(capture_btn)

        layout = self.content_layout()

        # Splitter: Galeria | Preview
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.splitter, 1)

        # === Galeria ===
        self.gallery_panel = GlassPanel("Galeria")
        self.splitter.addWidget(self.gallery_panel)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.gallery_widget = QWidget()
        self.gallery_layout = FlowLayout(self.gallery_widget)
        self.gallery_layout.setContentsMargins(8, 8, 8, 8)
        self.gallery_layout.setSpacing(8)

        self.scroll.setWidget(self.gallery_widget)
        self.gallery_panel.add_widget(self.scroll)

        # === Preview ===
        preview_panel = GlassPanel("Preview")
        preview_panel.setFixedWidth(280)
        self.splitter.addWidget(preview_panel)

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
        self.test_btn.setToolTip("Testar template em todas as janelas\nBusca o template e mostra onde foi encontrado")
        self.test_btn.clicked.connect(self._test_template)
        self.test_btn.setEnabled(False)
        preview_layout.addWidget(self.test_btn)

        self.rename_btn = QPushButton(f"{Icons.EDIT} Renomear")
        self.rename_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rename_btn.setToolTip("Alterar nome do arquivo de template")
        self.rename_btn.clicked.connect(self._rename_template)
        self.rename_btn.setEnabled(False)
        preview_layout.addWidget(self.rename_btn)

        self.recapture_btn = QPushButton(f"{Icons.CAPTURE} Recapturar")
        self.recapture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.recapture_btn.setToolTip("Capturar nova imagem mantendo o mesmo nome\nÚtil para atualizar template sem quebrar tasks existentes")
        self.recapture_btn.clicked.connect(self._recapture_template)
        self.recapture_btn.setEnabled(False)
        preview_layout.addWidget(self.recapture_btn)

        self.delete_btn = QPushButton(f"{Icons.DELETE} Excluir")
        self.delete_btn.setProperty("variant", "danger")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setToolTip("Excluir template permanentemente\nTasks que usam este template pararão de funcionar")
        self.delete_btn.clicked.connect(self._delete_template)
        self.delete_btn.setEnabled(False)
        preview_layout.addWidget(self.delete_btn)

        open_btn = QPushButton(f"{Icons.FOLDER} Abrir Pasta")
        open_btn.setProperty("variant", "ghost")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.setToolTip("Abrir pasta de templates no Finder\nPasta: images/")
        open_btn.clicked.connect(self._open_folder)
        preview_layout.addWidget(open_btn)

        preview_layout.addStretch()

        self.splitter.setSizes([500, 280])

    def on_show(self):
        self.refresh()
        # Agenda relayout após mostrar
        QTimer.singleShot(100, self._relayout_gallery)

    def resizeEvent(self, event):
        """Reorganiza galeria quando janela redimensiona."""
        super().resizeEvent(event)
        self._relayout_gallery()

    def _relayout_gallery(self):
        """Reorganiza a galeria baseado na largura atual."""
        width = self.scroll.viewport().width()
        if width > 0 and width != self._gallery_width:
            self._gallery_width = width
            self.gallery_layout.doLayout(width)

    def refresh(self):
        """Recarrega galeria."""
        # Limpa
        self.gallery_layout.clearFlow()
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

        for img_path in images:
            thumb = ImageThumbnail(img_path, on_click=self._on_select)
            self.gallery_layout.addFlowWidget(thumb)
            self._thumbnails[img_path] = thumb

        # Faz o layout inicial
        self._gallery_width = 0
        QTimer.singleShot(50, self._relayout_gallery)

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
            self.recapture_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)

        except Exception as e:
            self.log(f"Erro ao carregar preview: {e}", "error")

    def _capture(self):
        """Inicia captura."""
        self.app.start_capture()

    def _test_template(self):
        """Testa template em todas as janelas abertas (replica comportamento real do app)."""
        if not self._selected_path:
            return

        template_name = self._selected_path.stem
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Testando...")
        QApplication.processEvents()

        # Mostra toast de início
        if hasattr(self.app, 'toast'):
            self.app.toast.info(f"Buscando '{template_name}' em todas as janelas...")

        try:
            from core import get_windows
            from core.image_matcher import capture_window, find_template_location, check_template_visible

            # Obtém todas as janelas visíveis
            all_windows = get_windows()

            if not all_windows:
                self.log(f"{Icons.WARNING} Nenhuma janela encontrada", "warning")
                return

            best_match = 0.0
            best_window = None
            found_location = None

            # Threshold padrão do sistema (85%)
            from core.image_matcher import MATCH_THRESHOLD
            test_threshold = MATCH_THRESHOLD

            # Busca em todas as janelas (igual ao app real)
            for window_id, title in all_windows:
                try:
                    # Usa check_template_visible (mesma função do core)
                    visible, match = check_template_visible(window_id, self._selected_path, threshold=test_threshold)

                    if match > best_match:
                        best_match = match
                        best_window = (window_id, title)

                    if visible:
                        # Encontrou! Pega localização exata
                        found_location = find_template_location(window_id, self._selected_path)
                        break

                except Exception:
                    continue

            conf_pct = int(best_match * 100)

            if found_location and best_window:
                x, y, w, h = found_location
                center_x = x + w // 2
                center_y = y + h // 2

                # Determina qualidade do match
                if best_match >= 0.90:
                    quality = "Excelente"
                    level = "success"
                elif best_match >= 0.85:
                    quality = "Bom"
                    level = "success"
                elif best_match >= 0.75:
                    quality = "Aceitável"
                    level = "warning"
                else:
                    quality = "Baixo"
                    level = "warning"

                window_name = best_window[1][:30] + "..." if len(best_window[1]) > 30 else best_window[1]
                msg = f"Encontrado em '{window_name}' | Pos: ({center_x}, {center_y}) | {conf_pct}% ({quality})"
                self.log(f"{Icons.SUCCESS} {msg}", level)

                if hasattr(self.app, 'toast'):
                    if best_match >= 0.75:
                        self.app.toast.success(f"Encontrado com {conf_pct}% em '{window_name}'")
                    else:
                        self.app.toast.warning(f"Encontrado com {conf_pct}% (baixa precisão)")

                # NÃO move cursor - apenas log (Ghost Click não rouba foco)

            elif best_match > 0:
                # Não encontrou mas teve algum match
                window_name = best_window[1][:30] if best_window else "?"
                threshold_pct = int(test_threshold * 100)
                msg = f"Não encontrado. Melhor match: {conf_pct}% em '{window_name}' (mínimo: {threshold_pct}%)"
                self.log(f"{Icons.WARNING} {msg}", "warning")

                if hasattr(self.app, 'toast'):
                    self.app.toast.warning(f"Não encontrado (melhor: {conf_pct}%)")
            else:
                self.log(f"{Icons.WARNING} Template não encontrado em nenhuma janela", "warning")
                if hasattr(self.app, 'toast'):
                    self.app.toast.warning("Não encontrado em nenhuma janela")

        except Exception as e:
            self.log(f"Erro ao testar: {e}", "error")
            if hasattr(self.app, 'toast'):
                self.app.toast.error(f"Erro: {str(e)[:50]}")

        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText(f"{Icons.SUCCESS} Testar")

    def _rename_template(self):
        """Renomeia template e atualiza tasks que o usam."""
        if not self._selected_path:
            return

        old_name = self._selected_path.stem
        new_name, ok = QInputDialog.getText(
            self, "Renomear Template",
            "Novo nome:",
            text=old_name
        )

        if ok and new_name and new_name != old_name:
            new_path = self._selected_path.parent / f"{new_name}.png"

            if new_path.exists():
                QMessageBox.warning(self, "Erro", "Já existe um template com esse nome.")
                return

            try:
                self._selected_path.rename(new_path)
                self.log(f"Renomeado: {old_name} → {new_name}")
                self._selected_path = new_path
                
                # Atualiza tasks que usam este template
                if hasattr(self.app, 'task_manager') and self.app.task_manager:
                    updated = self.app.task_manager.update_image_name(old_name, new_name)
                    if updated > 0:
                        # Salva tasks atualizadas
                        self.app.task_manager.save_tasks(self.app.tasks_file)
                        self.log(f"Atualizado {updated} referência(s) em tasks")
                        if hasattr(self.app, 'toast'):
                            self.app.toast.info(f"{updated} task(s) atualizada(s)")
                
                self.refresh()
            except Exception as e:
                self.log(f"Erro ao renomear: {e}", "error")

    def _recapture_template(self):
        """Recaptura template mantendo o mesmo nome."""
        if not self._selected_path:
            return

        template_name = self._selected_path.stem

        # Confirma com o usuário
        if not ConfirmDialog.confirm(
            self,
            title="Recapturar Template",
            message=f"Substituir '{template_name}' por uma nova captura?\n\nO template atual será sobrescrito.",
            danger=False
        ):
            return

        # Salva o caminho para usar no callback
        self._recapture_path = self._selected_path

        # Minimiza janela principal
        self.app.showMinimized()

        # Aguarda minimização e inicia captura
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(200, self._show_recapture_overlay)

    def _show_recapture_overlay(self):
        """Mostra overlay para recaptura."""
        from ..components.capture_overlay import CaptureOverlay

        self._capture_overlay = CaptureOverlay(
            save_dir=self.images_dir,
            on_complete=self._on_recapture_complete,
            fixed_output_path=self._recapture_path
        )
        self._capture_overlay.start()

    def _on_recapture_complete(self, path: Path):
        """Callback quando recaptura termina."""
        self.app.showNormal()
        self.log(f"{Icons.SUCCESS} Template atualizado: {path.stem}")

        if hasattr(self.app, 'toast'):
            self.app.toast.success(f"Template '{path.stem}' atualizado!")

        # Atualiza galeria e re-seleciona o template
        self.refresh()
        self._on_select(path)

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
        self.recapture_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def _open_folder(self):
        """Abre pasta de imagens no Finder."""
        import subprocess
        # macOS: abre Finder na pasta
        subprocess.run(['open', str(self.images_dir)])
