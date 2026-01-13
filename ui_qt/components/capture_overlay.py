"""
Overlay de captura de tela com selecao de area.
Usa CGWindowListCreateImage para captura consistente com o sistema de matching no macOS.
"""

import re
import threading
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, QRect, QPoint, QBuffer, QIODevice
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QGuiApplication, QImage
from pathlib import Path
import numpy as np

from Quartz import (
    CGWindowListCreateImage,
    CGRectNull,
    CGRectMake,
    kCGWindowListOptionIncludingWindow,
    kCGWindowImageBoundsIgnoreFraming,
    kCGWindowImageDefault,
    CGImageGetWidth,
    CGImageGetHeight,
    CGImageGetBytesPerRow,
    CGImageGetDataProvider,
    CGDataProviderCopyData,
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGWindowListExcludeDesktopElements,
    kCGNullWindowID,
)
from AppKit import NSScreen

# Cache global do EasyOCR reader (carrega apenas uma vez)
_ocr_reader = None
_ocr_lock = threading.Lock()


def _get_ocr_reader():
    """Retorna o reader OCR em cache (singleton thread-safe)."""
    global _ocr_reader
    if _ocr_reader is None:
        with _ocr_lock:
            if _ocr_reader is None:
                try:
                    import easyocr
                    _ocr_reader = easyocr.Reader(['en', 'pt'], gpu=False, verbose=False)
                except Exception:
                    pass
    return _ocr_reader


def get_process_at_point(x: int, y: int, exclude_window_id: int = 0) -> str:
    """Retorna o nome do processo da janela em uma coordenada especifica.

    Args:
        x: Coordenada X (pixels)
        y: Coordenada Y (pixels)
        exclude_window_id: Window ID a excluir da busca (ex: overlay)

    Returns:
        Nome do app (ex: "Safari") ou string vazia
    """
    try:
        windows = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
            kCGNullWindowID
        )

        if not windows:
            return ""

        # Ordena por layer (janelas mais na frente primeiro)
        windows_sorted = sorted(windows, key=lambda w: w.get('kCGWindowLayer', 0))

        for window in windows_sorted:
            window_id = window.get('kCGWindowNumber', 0)
            if window_id == exclude_window_id:
                continue

            bounds = window.get('kCGWindowBounds', {})
            wx = int(bounds.get('X', 0))
            wy = int(bounds.get('Y', 0))
            ww = int(bounds.get('Width', 0))
            wh = int(bounds.get('Height', 0))

            if wx <= x < wx + ww and wy <= y < wy + wh:
                owner = window.get('kCGWindowOwnerName', '')
                # Ignora janelas do sistema
                if owner not in ['Window Server', 'Dock', 'SystemUIServer']:
                    return owner

        return ""

    except Exception:
        return ""


def _get_window_at_point(x: int, y: int, exclude_window_id: int = 0) -> int:
    """Encontra a janela na posicao especificada.

    Args:
        x: Coordenada X
        y: Coordenada Y
        exclude_window_id: Window ID a excluir

    Returns:
        window_id ou 0 se nao encontrada
    """
    try:
        windows = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
            kCGNullWindowID
        )

        if not windows:
            return 0

        windows_sorted = sorted(windows, key=lambda w: w.get('kCGWindowLayer', 0))

        for window in windows_sorted:
            window_id = window.get('kCGWindowNumber', 0)
            if window_id == exclude_window_id:
                continue

            bounds = window.get('kCGWindowBounds', {})
            wx = int(bounds.get('X', 0))
            wy = int(bounds.get('Y', 0))
            ww = int(bounds.get('Width', 0))
            wh = int(bounds.get('Height', 0))

            if wx <= x < wx + ww and wy <= y < wy + wh:
                owner = window.get('kCGWindowOwnerName', '')
                if owner not in ['Window Server', 'Dock', 'SystemUIServer']:
                    return window_id

        return 0

    except Exception:
        return 0


def _cgimage_to_qpixmap(cg_image) -> QPixmap:
    """Converte CGImage para QPixmap."""
    if cg_image is None:
        return None

    try:
        width = CGImageGetWidth(cg_image)
        height = CGImageGetHeight(cg_image)
        bytes_per_row = CGImageGetBytesPerRow(cg_image)

        data_provider = CGImageGetDataProvider(cg_image)
        data = CGDataProviderCopyData(data_provider)

        img = np.frombuffer(data, dtype=np.uint8)

        if bytes_per_row == width * 4:
            img = img.reshape((height, width, 4))
        else:
            img_reshaped = np.zeros((height, width, 4), dtype=np.uint8)
            for row in range(height):
                start = row * bytes_per_row
                end = start + width * 4
                img_reshaped[row] = np.frombuffer(data[start:end], dtype=np.uint8).reshape((width, 4))
            img = img_reshaped

        # macOS CGImage usa BGRA, converte para RGBA
        img_rgba = img[:, :, [2, 1, 0, 3]].copy()

        qimage = QImage(
            img_rgba.data,
            width,
            height,
            width * 4,
            QImage.Format.Format_RGBA8888
        ).copy()

        return QPixmap.fromImage(qimage)

    except Exception as e:
        print(f"Erro ao converter CGImage: {e}")
        return None


def capture_window_region_quartz(screen_x: int, screen_y: int, width: int, height: int) -> QPixmap:
    """Captura uma regiao usando CGWindowListCreateImage da janela naquela posicao.

    Isso garante que o template capturado seja compativel com o sistema
    de matching que tambem usa CGWindowListCreateImage.

    Args:
        screen_x: Coordenada X absoluta da regiao (pontos logicos)
        screen_y: Coordenada Y absoluta da regiao (pontos logicos)
        width: Largura da regiao (pontos logicos)
        height: Altura da regiao (pontos logicos)

    Returns:
        QPixmap da regiao ou None se falhar
    """
    try:
        # Encontra a janela nessa posicao
        window_id = _get_window_at_point(screen_x, screen_y)
        if not window_id:
            return None

        # Obtem bounds da janela (em pontos logicos)
        windows = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )

        window_bounds = None
        for w in windows:
            if w.get('kCGWindowNumber', 0) == window_id:
                window_bounds = w.get('kCGWindowBounds', {})
                break

        if not window_bounds:
            return None

        win_left = int(window_bounds.get('X', 0))
        win_top = int(window_bounds.get('Y', 0))
        win_width = int(window_bounds.get('Width', 0))
        win_height = int(window_bounds.get('Height', 0))

        if win_width < 10 or win_height < 10:
            return None

        # Captura a janela inteira
        cg_image = CGWindowListCreateImage(
            CGRectNull,
            kCGWindowListOptionIncludingWindow,
            window_id,
            kCGWindowImageBoundsIgnoreFraming | kCGWindowImageDefault
        )

        if cg_image is None:
            return None

        # Converte para numpy array
        # NOTA: CGImage retorna pixels FISICOS (Retina = 2x)
        img_width = CGImageGetWidth(cg_image)
        img_height = CGImageGetHeight(cg_image)
        bytes_per_row = CGImageGetBytesPerRow(cg_image)

        # Calcula fator de escala Retina
        # A imagem tem img_width pixels, a janela tem win_width pontos
        scale_x = img_width / win_width if win_width > 0 else 1.0
        scale_y = img_height / win_height if win_height > 0 else 1.0

        data_provider = CGImageGetDataProvider(cg_image)
        data = CGDataProviderCopyData(data_provider)

        img = np.frombuffer(data, dtype=np.uint8)

        if bytes_per_row == img_width * 4:
            img_array = img.reshape((img_height, img_width, 4))
        else:
            img_array = np.zeros((img_height, img_width, 4), dtype=np.uint8)
            for row in range(img_height):
                start = row * bytes_per_row
                end = start + img_width * 4
                img_array[row] = np.frombuffer(data[start:end], dtype=np.uint8).reshape((img_width, 4))

        # Calcula regiao relativa a janela (converte pontos logicos para pixels fisicos)
        rel_x = int((screen_x - win_left) * scale_x)
        rel_y = int((screen_y - win_top) * scale_y)
        region_width = int(width * scale_x)
        region_height = int(height * scale_y)

        # Garante que a regiao esta dentro da janela
        rel_x = max(0, min(rel_x, img_width - 1))
        rel_y = max(0, min(rel_y, img_height - 1))
        end_x = min(rel_x + region_width, img_width)
        end_y = min(rel_y + region_height, img_height)

        # Extrai a regiao
        region = img_array[rel_y:end_y, rel_x:end_x].copy()

        # Converte BGRA para RGBA
        region_rgba = region[:, :, [2, 1, 0, 3]].copy()

        qimage = QImage(
            region_rgba.data,
            region_rgba.shape[1],
            region_rgba.shape[0],
            region_rgba.shape[1] * 4,
            QImage.Format.Format_RGBA8888
        ).copy()

        return QPixmap.fromImage(qimage)

    except Exception as e:
        print(f"Erro ao capturar regiao: {e}")
        return None


class SaveCaptureDialog(QDialog):
    """Dialogo para salvar captura."""

    def __init__(self, suggested_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Salvar Captura")
        self.setFixedSize(450, 120)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        label = QLabel("Nome do template:")
        layout.addWidget(label)

        self.name_edit = QLineEdit()
        self.name_edit.setText(suggested_name)
        self.name_edit.setMinimumHeight(32)
        self.name_edit.setStyleSheet("font-size: 13px; padding: 4px 8px;")
        self.name_edit.selectAll()
        layout.addWidget(self.name_edit)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(80, 32)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedSize(80, 32)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.name_edit.returnPressed.connect(self.accept)

    def get_name(self) -> str:
        return self.name_edit.text().strip()

    @staticmethod
    def get_template_name(suggested_name: str, parent=None) -> tuple:
        """Abre dialogo e retorna (nome, ok)."""
        dialog = SaveCaptureDialog(suggested_name, parent)
        result = dialog.exec()
        return dialog.get_name(), result == QDialog.DialogCode.Accepted


def extract_text_from_image(pixmap: QPixmap) -> str:
    """Extrai texto de um QPixmap usando EasyOCR."""
    try:
        import numpy as np
        import io
        from PIL import Image

        reader = _get_ocr_reader()
        if reader is None:
            return ""

        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")
        image_bytes = buffer.data().data()

        img = Image.open(io.BytesIO(image_bytes))
        img_np = np.array(img)

        results = reader.readtext(img_np)
        texts = [text for _, text, conf in results if conf > 0.3]

        if texts:
            return max(texts, key=len)
        return ""
    except Exception:
        return ""


def generate_template_name(text: str, process: str) -> str:
    """Gera nome do template baseado no texto OCR e processo."""
    parts = []

    # Texto OCR (sanitizado, max 3 palavras)
    if text:
        clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        words = clean_text.split()[:3]
        if words:
            parts.append("_".join(words))

    # Nome do processo/app
    if process:
        clean_process = re.sub(r'[^a-zA-Z0-9]', '', process)
        if clean_process:
            parts.append(clean_process)

    if parts:
        return "_".join(parts)[:50]

    return "template"


class CaptureOverlay(QWidget):
    """Overlay fullscreen para captura de regiao."""

    def __init__(self, save_dir: Path, on_complete=None, parent=None, fixed_output_path: Path = None):
        """Inicializa overlay de captura.

        Args:
            save_dir: Diretorio onde salvar capturas
            on_complete: Callback chamado apos salvar (recebe Path)
            parent: Widget pai
            fixed_output_path: Se fornecido, salva diretamente neste caminho
                              sem pedir nome (usado para recaptura)
        """
        super().__init__(parent)
        self.save_dir = save_dir
        self.on_complete = on_complete
        self._fixed_output_path = fixed_output_path

        self._start_pos = None
        self._current_pos = None
        self._selecting = False
        self._screenshot = None
        self._active_process = ""

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self._capture_screen()

    def _capture_screen(self):
        """Captura screenshot usando a melhor estrategia disponivel.

        Ordem de tentativa:
        1. MSS (multi-monitor, cross-platform)
        2. Qt multi-screen (fallback Qt nativo)
        3. Qt primary screen (ultimo recurso)

        Nota: Para templates, usamos CGWindowListCreateImage no momento de salvar
        para garantir compatibilidade com o sistema de matching.
        """
        # Estrategia 1: MSS
        if self._try_capture_mss():
            return

        # Estrategia 2: Qt multi-screen
        if self._try_capture_qt_multiscreen():
            return

        # Estrategia 3: Qt primary (ultimo recurso)
        self._capture_qt_primary()

    def _try_capture_mss(self) -> bool:
        """Tenta captura usando MSS (multi-monitor via virtual screen)."""
        try:
            import mss
            from PyQt6.QtGui import QImage

            with mss.mss() as sct:
                # Monitor 0 e o virtual screen (todas as telas combinadas)
                if len(sct.monitors) < 2:
                    return False

                monitor = sct.monitors[0]

                if monitor["width"] < 100 or monitor["height"] < 100:
                    return False

                screenshot = sct.grab(monitor)

                img = QImage(
                    screenshot.bgra,
                    screenshot.width,
                    screenshot.height,
                    screenshot.width * 4,
                    QImage.Format.Format_ARGB32
                ).copy()

                self._screenshot = QPixmap.fromImage(img)
                self._screenshot_original = self._screenshot.copy()

                # MSS captura em pixels fisicos - detecta DPI da tela primaria
                primary = QGuiApplication.primaryScreen()
                self._scale_x = primary.devicePixelRatio() if primary else 1.0
                self._scale_y = self._scale_x

                self._offset = QPoint(monitor["left"], monitor["top"])
                self.setGeometry(
                    monitor["left"],
                    monitor["top"],
                    monitor["width"],
                    monitor["height"]
                )
                return True

        except Exception:
            return False

    def _try_capture_qt_multiscreen(self) -> bool:
        """Tenta captura usando Qt com multiplas telas."""
        try:
            from PyQt6.QtGui import QImage

            screens = QGuiApplication.screens()
            if len(screens) < 2:
                return False

            # Calcula bounding box de todas as telas
            min_x = min(s.geometry().x() for s in screens)
            min_y = min(s.geometry().y() for s in screens)
            max_x = max(s.geometry().x() + s.geometry().width() for s in screens)
            max_y = max(s.geometry().y() + s.geometry().height() for s in screens)

            total_width = max_x - min_x
            total_height = max_y - min_y

            if total_width < 100 or total_height < 100:
                return False

            # Cria pixmap combinado
            combined = QPixmap(total_width, total_height)
            combined.fill(QColor(0, 0, 0))

            painter = QPainter(combined)

            # Captura cada tela e posiciona no pixmap combinado
            for screen in screens:
                geom = screen.geometry()
                grab = screen.grabWindow(0)

                # Ajusta para DPI se necessario
                dpr = screen.devicePixelRatio()
                if dpr != 1.0:
                    grab = grab.scaled(
                        int(grab.width() / dpr),
                        int(grab.height() / dpr),
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )

                # Posicao relativa ao bounding box
                rel_x = geom.x() - min_x
                rel_y = geom.y() - min_y
                painter.drawPixmap(rel_x, rel_y, grab)

            painter.end()

            self._screenshot = combined
            self._screenshot_original = combined.copy()
            self._scale_x = 1.0
            self._scale_y = 1.0

            self._offset = QPoint(min_x, min_y)
            self.setGeometry(min_x, min_y, total_width, total_height)
            return True

        except Exception:
            return False

    def _capture_qt_primary(self):
        """Fallback final: captura apenas tela primaria."""
        screen = QGuiApplication.primaryScreen()
        if not screen:
            self.close()
            return

        geom = screen.geometry()
        self._screenshot = screen.grabWindow(0)
        self._screenshot_original = self._screenshot.copy()
        self._scale_x = screen.devicePixelRatio()
        self._scale_y = screen.devicePixelRatio()

        self._offset = QPoint(geom.x(), geom.y())
        self.setGeometry(geom)

    def start(self):
        """Inicia o overlay."""
        self.show()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event):
        """Desenha overlay com selecao."""
        painter = QPainter(self)

        if self._screenshot:
            painter.drawPixmap(0, 0, self._screenshot)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if self._start_pos and self._current_pos:
            rect = self._get_selection_rect()

            if self._screenshot:
                painter.drawPixmap(rect, self._screenshot, rect)

            pen = QPen(QColor(0, 162, 232), 2)
            painter.setPen(pen)
            painter.drawRect(rect)

            # Dimensoes
            if hasattr(self, '_scale_x'):
                w = int(rect.width() * self._scale_x)
                h = int(rect.height() * self._scale_y)
            else:
                w = rect.width()
                h = rect.height()
            size_text = f"{w} x {h}"

            text_rect = painter.fontMetrics().boundingRect(size_text)
            text_x = rect.x() + 4
            text_y = rect.y() + rect.height() + 18

            painter.fillRect(
                text_x - 2, text_y - text_rect.height(),
                text_rect.width() + 4, text_rect.height() + 4,
                QColor(0, 0, 0, 180)
            )

            painter.setPen(QColor(255, 255, 255))
            painter.drawText(text_x, text_y, size_text)

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            10, 30,
            "Arraste para selecionar | ESC cancela | Botao direito reinicia"
        )

    def _get_selection_rect(self) -> QRect:
        """Retorna retangulo de selecao normalizado."""
        if not self._start_pos or not self._current_pos:
            return QRect()

        x1 = min(self._start_pos.x(), self._current_pos.x())
        y1 = min(self._start_pos.y(), self._current_pos.y())
        x2 = max(self._start_pos.x(), self._current_pos.x())
        y2 = max(self._start_pos.y(), self._current_pos.y())

        return QRect(x1, y1, x2 - x1, y2 - y1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.pos()
            self._current_pos = event.pos()
            self._selecting = True

            # Captura processo da janela sob o cursor
            global_pos = self.mapToGlobal(event.pos())
            # No macOS, usamos window ID em vez de hwnd
            overlay_window_id = 0  # Overlay nao tem window ID do sistema
            self._active_process = get_process_at_point(
                global_pos.x(), global_pos.y(), exclude_window_id=overlay_window_id
            )

        elif event.button() == Qt.MouseButton.RightButton:
            self._start_pos = None
            self._current_pos = None
            self._selecting = False
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._selecting = False
            self._current_pos = event.pos()

            rect = self._get_selection_rect()
            if rect.width() > 5 and rect.height() > 5:
                self._save_selection(rect)
            else:
                self._start_pos = None
                self._current_pos = None
                self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def _save_selection(self, rect: QRect):
        """Salva a regiao selecionada usando CGWindowListCreateImage para compatibilidade."""
        self.hide()

        if not self._screenshot:
            self.close()
            return

        # Calcula coordenadas absolutas da selecao (em pontos logicos)
        if hasattr(self, '_offset'):
            abs_x = self._offset.x() + rect.x()
            abs_y = self._offset.y() + rect.y()
        else:
            abs_x = rect.x()
            abs_y = rect.y()

        # Largura e altura em pontos logicos
        width = rect.width()
        height = rect.height()

        # Tenta capturar usando CGWindowListCreateImage (compativel com matching)
        # NOTA: capture_window_region_quartz recebe coordenadas LOGICAS e faz a conversao internamente
        cropped = capture_window_region_quartz(abs_x, abs_y, width, height)

        # Fallback: usa captura do overlay se Quartz falhar
        if cropped is None or cropped.isNull():
            if hasattr(self, '_screenshot_original') and hasattr(self, '_scale_x'):
                physical_rect = QRect(
                    int(rect.x() * self._scale_x),
                    int(rect.y() * self._scale_y),
                    int(rect.width() * self._scale_x),
                    int(rect.height() * self._scale_y)
                )
                cropped = self._screenshot_original.copy(physical_rect)
            else:
                cropped = self._screenshot.copy(rect)

        # Centro para deteccao de processo/monitor
        center_x = abs_x + width // 2
        center_y = abs_y + height // 2

        # Modo recaptura: salva diretamente sem pedir nome
        if self._fixed_output_path:
            self._save_with_dpi_metadata(cropped, self._fixed_output_path, center_x, center_y)

            if self.on_complete:
                self.on_complete(self._fixed_output_path)

            self.close()
            return

        # Modo normal: pede nome para salvar
        suggested_name = "template"
        try:
            text = extract_text_from_image(cropped)
            suggested_name = generate_template_name(text, self._active_process)
        except Exception:
            if self._active_process:
                suggested_name = self._active_process or "template"

        name, ok = SaveCaptureDialog.get_template_name(suggested_name)

        if ok and name:
            name = "".join(c for c in name if c.isalnum() or c in "._- ")
            name = name.strip() or "template"

            if not name.lower().endswith('.png'):
                name += '.png'

            path = self.save_dir / name

            # Salva com metadados de DPI para escalonamento correto no matching
            self._save_with_dpi_metadata(cropped, path, center_x, center_y)

            if self.on_complete:
                self.on_complete(path)

        self.close()

    def _save_with_dpi_metadata(self, pixmap: QPixmap, path: Path, screen_x: int = 0, screen_y: int = 0):
        """Salva imagem PNG com metadados de DPI.

        Como usamos CGWindowListCreateImage para captura (mesmo metodo do matching),
        a imagem ja esta em pixels fisicos da janela. Salvamos o DPI
        da janela para referencia futura.

        Args:
            pixmap: QPixmap com a imagem capturada
            path: Caminho onde salvar o arquivo
            screen_x: Coordenada X absoluta da selecao
            screen_y: Coordenada Y absoluta da selecao
        """
        from PIL import Image
        from PIL.PngImagePlugin import PngInfo

        # Detecta DPI da tela onde a captura foi feita
        capture_dpi = 96

        try:
            # Encontra a tela na posicao da selecao
            from PyQt6.QtCore import QPoint
            screen = QGuiApplication.screenAt(QPoint(screen_x, screen_y))
            if not screen:
                screen = QGuiApplication.primaryScreen()
            if screen:
                capture_dpi = int(96 * screen.devicePixelRatio())
        except Exception:
            pass

        # Primeiro salva com Qt
        pixmap.save(str(path), "PNG")

        # Adiciona metadados de DPI
        try:
            pil_image = Image.open(str(path))
            img_copy = pil_image.copy()
            pil_image.close()

            metadata = PngInfo()
            metadata.add_text("ImageClicker_DPI", str(capture_dpi))
            img_copy.save(str(path), "PNG", pnginfo=metadata, dpi=(capture_dpi, capture_dpi))
        except Exception:
            pass  # Arquivo ja foi salvo pelo Qt

    def closeEvent(self, event):
        """Limpa recursos ao fechar."""
        self._screenshot = None
        event.accept()
