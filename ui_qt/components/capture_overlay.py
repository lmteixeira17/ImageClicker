"""
Overlay de captura de tela com seleção de área.
"""

import re
import threading
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, QRect, QPoint, QBuffer, QIODevice
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QGuiApplication
from pathlib import Path

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


def get_process_at_point(x: int, y: int, exclude_hwnd: int = 0) -> str:
    """Retorna o nome do processo da janela em uma coordenada específica.

    Args:
        x: Coordenada X (pixels)
        y: Coordenada Y (pixels)
        exclude_hwnd: HWND a excluir da busca (ex: overlay)

    Returns:
        Nome do processo (ex: "Code.exe") ou string vazia
    """
    try:
        import win32gui
        import win32process
        import win32api
        import win32con

        # Encontra janela na coordenada especificada
        hwnd = win32gui.WindowFromPoint((x, y))

        # Se for uma janela filha, pega a janela pai (root)
        root_hwnd = win32gui.GetAncestor(hwnd, 2)  # GA_ROOT = 2
        if root_hwnd:
            hwnd = root_hwnd

        # Se a janela encontrada for a excluída (overlay), busca a próxima
        if hwnd == exclude_hwnd:
            def enum_callback(h, results):
                if h != exclude_hwnd and win32gui.IsWindowVisible(h):
                    rect = win32gui.GetWindowRect(h)
                    if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]:
                        results.append(h)
                return True

            results = []
            win32gui.EnumWindows(enum_callback, results)
            if results:
                hwnd = results[0]

        # Obtém nome do processo
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        handle = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
            False, pid
        )
        exe_path = win32process.GetModuleFileNameEx(handle, 0)
        return Path(exe_path).name

    except Exception:
        return ""


class SaveCaptureDialog(QDialog):
    """Diálogo para salvar captura."""

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
    def get_template_name(suggested_name: str, parent=None) -> tuple[str, bool]:
        """Abre diálogo e retorna (nome, ok)."""
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

    # Texto OCR (sanitizado, máx 3 palavras)
    if text:
        clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        words = clean_text.split()[:3]
        if words:
            parts.append("_".join(words))

    # Nome do processo (sem extensão .exe)
    if process:
        process_clean = process.replace('.exe', '').replace('.EXE', '')
        clean_process = re.sub(r'[^a-zA-Z0-9]', '', process_clean)
        if clean_process:
            parts.append(clean_process)

    if parts:
        return "_".join(parts)[:50]

    return "template"


class CaptureOverlay(QWidget):
    """Overlay fullscreen para captura de região."""

    def __init__(self, save_dir: Path, on_complete=None, parent=None, fixed_output_path: Path = None):
        """Inicializa overlay de captura.

        Args:
            save_dir: Diretório onde salvar capturas
            on_complete: Callback chamado após salvar (recebe Path)
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
        """Captura screenshot usando a melhor estratégia disponível.

        Ordem de tentativa:
        1. MSS (multi-monitor, funciona bem com USB docks)
        2. Win32 API (multi-GPU, funciona com NVIDIA/AMD)
        3. Qt multi-screen (fallback Qt nativo)
        4. Qt primary screen (último recurso)
        """
        # Estratégia 1: MSS
        if self._try_capture_mss():
            return

        # Estratégia 2: Win32 API (melhor para multi-GPU)
        if self._try_capture_win32():
            return

        # Estratégia 3: Qt multi-screen
        if self._try_capture_qt_multiscreen():
            return

        # Estratégia 4: Qt primary (último recurso)
        self._capture_qt_primary()

    def _try_capture_mss(self) -> bool:
        """Tenta captura usando MSS (multi-monitor via virtual screen)."""
        try:
            import mss
            from PyQt6.QtGui import QImage

            with mss.mss() as sct:
                # Monitor 0 é o virtual screen (todas as telas combinadas)
                if len(sct.monitors) < 2:
                    return False  # MSS não detectou múltiplos monitores

                monitor = sct.monitors[0]

                # Verifica se é um virtual screen válido (dimensões razoáveis)
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

                # MSS captura em pixels físicos - detecta DPI da tela primária
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

    def _try_capture_win32(self) -> bool:
        """Tenta captura usando Win32 API (melhor para multi-GPU/desktop).

        Usa GetSystemMetrics para obter virtual screen e BitBlt para captura.
        Funciona mesmo quando MSS falha em configurações multi-GPU.
        """
        try:
            import win32gui
            import win32ui
            import win32con
            import win32api
            from PyQt6.QtGui import QImage

            # SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = coordenadas do canto superior esquerdo
            # SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = dimensões totais
            left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
            width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)

            if width < 100 or height < 100:
                return False

            # Cria DC do desktop
            desktop_dc = win32gui.GetDC(0)
            img_dc = win32ui.CreateDCFromHandle(desktop_dc)
            mem_dc = img_dc.CreateCompatibleDC()

            # Cria bitmap
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(img_dc, width, height)
            mem_dc.SelectObject(bitmap)

            # Captura com BitBlt (funciona com multi-GPU)
            mem_dc.BitBlt(
                (0, 0), (width, height),
                img_dc, (left, top),
                win32con.SRCCOPY
            )

            # Converte para QImage
            bmp_info = bitmap.GetInfo()
            bmp_bits = bitmap.GetBitmapBits(True)

            # Limpa recursos Win32
            win32gui.DeleteObject(bitmap.GetHandle())
            mem_dc.DeleteDC()
            img_dc.DeleteDC()
            win32gui.ReleaseDC(0, desktop_dc)

            # Cria QImage do buffer (formato BGRA)
            import numpy as np
            img_array = np.frombuffer(bmp_bits, dtype=np.uint8)
            img_array = img_array.reshape((bmp_info['bmHeight'], bmp_info['bmWidth'], 4))

            # Converte numpy array para QImage
            qimg = QImage(
                img_array.data,
                bmp_info['bmWidth'],
                bmp_info['bmHeight'],
                bmp_info['bmWidth'] * 4,
                QImage.Format.Format_ARGB32
            ).copy()

            self._screenshot = QPixmap.fromImage(qimg)
            self._screenshot_original = self._screenshot.copy()

            # Win32 captura em pixels físicos - detecta DPI da tela primária
            primary = QGuiApplication.primaryScreen()
            self._scale_x = primary.devicePixelRatio() if primary else 1.0
            self._scale_y = self._scale_x

            self._offset = QPoint(left, top)
            self.setGeometry(left, top, width, height)
            return True

        except Exception:
            return False

    def _try_capture_qt_multiscreen(self) -> bool:
        """Tenta captura usando Qt com múltiplas telas."""
        try:
            from PyQt6.QtGui import QImage

            screens = QGuiApplication.screens()
            if len(screens) < 2:
                return False  # Apenas uma tela, usa método simples

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

                # Ajusta para DPI se necessário
                dpr = screen.devicePixelRatio()
                if dpr != 1.0:
                    grab = grab.scaled(
                        int(grab.width() / dpr),
                        int(grab.height() / dpr),
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )

                # Posição relativa ao bounding box
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
        """Fallback final: captura apenas tela primária."""
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
        """Desenha overlay com seleção."""
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

            # Dimensões
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
            "Arraste para selecionar | ESC cancela | Botão direito reinicia"
        )

    def _get_selection_rect(self) -> QRect:
        """Retorna retângulo de seleção normalizado."""
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
            overlay_hwnd = int(self.winId())
            self._active_process = get_process_at_point(
                global_pos.x(), global_pos.y(), exclude_hwnd=overlay_hwnd
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
        """Salva a região selecionada."""
        self.hide()

        if not self._screenshot:
            self.close()
            return

        # Extrai região
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

        # Modo recaptura: salva diretamente sem pedir nome
        if self._fixed_output_path:
            self._save_with_dpi_metadata(cropped, self._fixed_output_path)

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
                process_clean = self._active_process.replace('.exe', '').replace('.EXE', '')
                suggested_name = process_clean or "template"

        name, ok = SaveCaptureDialog.get_template_name(suggested_name)

        if ok and name:
            name = "".join(c for c in name if c.isalnum() or c in "._- ")
            name = name.strip() or "template"

            if not name.lower().endswith('.png'):
                name += '.png'

            path = self.save_dir / name

            # Salva com metadados de DPI para escalonamento correto no matching
            self._save_with_dpi_metadata(cropped, path)

            if self.on_complete:
                self.on_complete(path)

        self.close()

    def _save_with_dpi_metadata(self, pixmap: QPixmap, path: Path):
        """Salva imagem PNG com metadados de DPI para escalonamento correto.

        Armazena o DPI de captura nos metadados PNG (campo pHYs) para que
        o sistema de matching possa calcular a escala correta quando a
        janela alvo tiver DPI diferente.

        Args:
            pixmap: QPixmap com a imagem capturada
            path: Caminho onde salvar o arquivo
        """
        # Detecta DPI do sistema usando Win32 API
        # GetDeviceCaps é mais confiável que GetDpiForSystem em apps Qt
        try:
            import ctypes
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
            hdc = user32.GetDC(0)
            capture_dpi = gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX = 88
            user32.ReleaseDC(0, hdc)
            if capture_dpi < 96:
                capture_dpi = 96
        except Exception:
            capture_dpi = 96  # Fallback para 100%

        from PIL import Image
        from PIL.PngImagePlugin import PngInfo

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
            pass  # Arquivo já foi salvo pelo Qt

    def closeEvent(self, event):
        """Limpa recursos ao fechar."""
        self._screenshot = None
        event.accept()
