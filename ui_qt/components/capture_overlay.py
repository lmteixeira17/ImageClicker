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

    def __init__(self, save_dir: Path, on_complete=None, parent=None):
        super().__init__(parent)
        self.save_dir = save_dir
        self.on_complete = on_complete

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
        """Captura screenshot usando MSS ou fallback Qt."""
        try:
            self._capture_screen_mss()
        except ImportError:
            self._capture_screen_qt_fallback()
        except Exception:
            self._capture_screen_qt_fallback()

    def _capture_screen_mss(self):
        """Captura usando MSS (multi-monitor)."""
        import mss
        from PyQt6.QtGui import QImage

        with mss.mss() as sct:
            monitor = sct.monitors[0]
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
            self._scale_x = 1.0
            self._scale_y = 1.0

            self._offset = QPoint(monitor["left"], monitor["top"])
            self.setGeometry(
                monitor["left"],
                monitor["top"],
                monitor["width"],
                monitor["height"]
            )

    def _capture_screen_qt_fallback(self):
        """Fallback usando Qt (tela primária)."""
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

        # Gera nome sugerido
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
            cropped.save(str(path), "PNG")

            if self.on_complete:
                self.on_complete(path)

        self.close()

    def closeEvent(self, event):
        """Limpa recursos ao fechar."""
        self._screenshot = None
        event.accept()
