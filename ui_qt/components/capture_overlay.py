"""
Overlay de captura de tela com seleção de área.
"""

import re
import threading
from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QInputDialog
from PyQt6.QtCore import Qt, QRect, QPoint, QBuffer, QIODevice
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QScreen, QGuiApplication
from pathlib import Path

# Cache global do EasyOCR reader (carrega apenas uma vez)
_ocr_reader = None
_ocr_loading = False
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


def get_foreground_window_info() -> tuple[str, int]:
    """Retorna o nome do processo e DPI da janela ativa."""
    process_name = ""
    dpi_scale = 100  # Default 100%

    try:
        import win32gui
        import win32process
        import win32api
        import win32con
        import ctypes

        hwnd = win32gui.GetForegroundWindow()

        # Obtém nome do processo
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        handle = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
            False, pid
        )
        exe_path = win32process.GetModuleFileNameEx(handle, 0)
        process_name = Path(exe_path).stem  # Nome sem extensão

        # Obtém DPI da janela
        try:
            # GetDpiForWindow (Windows 10 1607+)
            dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
            if dpi > 0:
                dpi_scale = round(dpi / 96 * 100)  # 96 DPI = 100%
        except Exception:
            pass

    except Exception:
        pass

    return process_name, dpi_scale


def extract_text_from_image(pixmap: QPixmap) -> str:
    """
    Extrai texto de um QPixmap usando EasyOCR.

    Args:
        pixmap: Imagem para extrair texto

    Returns:
        Texto extraído ou string vazia
    """
    try:
        import numpy as np
        import io
        from PIL import Image

        reader = _get_ocr_reader()
        if reader is None:
            return ""

        # Converte QPixmap para bytes
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")
        image_bytes = buffer.data().data()

        # Converte para numpy array
        img = Image.open(io.BytesIO(image_bytes))
        img_np = np.array(img)

        # OCR (com reader em cache é rápido)
        results = reader.readtext(img_np)

        # Extrai textos com confiança > 0.3
        texts = [text for _, text, conf in results if conf > 0.3]

        # Retorna o texto mais relevante (mais longo)
        if texts:
            return max(texts, key=len)
        return ""
    except Exception:
        return ""


def generate_template_name(text: str, process: str, dpi_scale: int = 100) -> str:
    """Gera nome do template baseado no texto, processo e DPI."""
    parts = []

    # Adiciona texto (limitado e sanitizado)
    if text:
        # Remove caracteres especiais, mantém apenas alfanuméricos
        clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # Pega as primeiras palavras (máx 3)
        words = clean_text.split()[:3]
        if words:
            parts.append("_".join(words))

    # Adiciona nome do processo
    if process:
        clean_process = re.sub(r'[^a-zA-Z0-9]', '', process)
        if clean_process:
            parts.append(clean_process)

    # Adiciona DPI se diferente de 100%
    if dpi_scale != 100:
        parts.append(f"{dpi_scale}DPI")

    if parts:
        name = "_".join(parts)
        # Limita tamanho
        return name[:50]

    return "template"


class CaptureOverlay(QWidget):
    """Overlay fullscreen para captura de região."""

    def __init__(self, save_dir: Path, on_complete=None, parent=None):
        super().__init__(parent)
        self.save_dir = save_dir
        self.on_complete = on_complete

        # Estado da seleção
        self._start_pos = None
        self._current_pos = None
        self._selecting = False
        self._screenshot = None

        # Captura processo ativo e DPI ANTES de mostrar overlay
        self._active_process, self._active_dpi = get_foreground_window_info()

        # Config da janela
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Captura tela e configura overlay
        self._capture_screen()

    def _capture_screen(self):
        """Captura screenshot de todas as telas."""
        # Obtém geometria virtual (todas as telas)
        screens = QGuiApplication.screens()

        if not screens:
            self.close()
            return

        # Calcula bounding box de todas as telas
        min_x = min(s.geometry().x() for s in screens)
        min_y = min(s.geometry().y() for s in screens)
        max_x = max(s.geometry().x() + s.geometry().width() for s in screens)
        max_y = max(s.geometry().y() + s.geometry().height() for s in screens)

        total_width = max_x - min_x
        total_height = max_y - min_y

        # Cria pixmap do tamanho total
        self._screenshot = QPixmap(total_width, total_height)
        self._screenshot.fill(Qt.GlobalColor.black)

        painter = QPainter(self._screenshot)

        # Captura cada tela
        for screen in screens:
            geom = screen.geometry()
            pixmap = screen.grabWindow(0)

            # Posiciona no pixmap total
            x = geom.x() - min_x
            y = geom.y() - min_y
            painter.drawPixmap(x, y, pixmap)

        painter.end()

        # Posiciona overlay
        self._offset = QPoint(min_x, min_y)
        self.setGeometry(min_x, min_y, total_width, total_height)

    def start(self):
        """Inicia o overlay cobrindo todas as telas."""
        # Usa show() ao invés de showFullScreen() para suportar multi-monitor
        # A geometria já foi configurada em _capture_screen()
        self.show()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event):
        """Desenha overlay com seleção."""
        painter = QPainter(self)

        # Desenha screenshot como fundo
        if self._screenshot:
            painter.drawPixmap(0, 0, self._screenshot)

        # Overlay escuro
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        # Se selecionando, mostra área clara
        if self._start_pos and self._current_pos:
            rect = self._get_selection_rect()

            # Limpa área selecionada (mostra imagem original)
            if self._screenshot:
                painter.drawPixmap(rect, self._screenshot, rect)

            # Borda da seleção
            pen = QPen(QColor(0, 162, 232), 2)  # Azul
            painter.setPen(pen)
            painter.drawRect(rect)

            # Dimensões
            w = rect.width()
            h = rect.height()
            size_text = f"{w} x {h}"

            # Fundo do texto
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

        # Instruções
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            10, 30,
            "Arraste para selecionar área | ESC para cancelar | Botão direito para reiniciar"
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
        elif event.button() == Qt.MouseButton.RightButton:
            # Reset seleção
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
                # Seleção muito pequena
                self._start_pos = None
                self._current_pos = None
                self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def _save_selection(self, rect: QRect):
        """Salva a região selecionada."""
        self.hide()

        # Extrai região do screenshot
        if not self._screenshot:
            self.close()
            return

        cropped = self._screenshot.copy(rect)

        # Tenta gerar nome automático
        suggested_name = "template"
        try:
            # Extrai texto da imagem (pode demorar na primeira vez)
            text = extract_text_from_image(cropped)
            suggested_name = generate_template_name(text, self._active_process, self._active_dpi)
        except Exception:
            # Fallback: usa processo + DPI
            if self._active_process:
                if self._active_dpi != 100:
                    suggested_name = f"{self._active_process}_{self._active_dpi}DPI"
                else:
                    suggested_name = self._active_process

        # Pede confirmação/edição do nome
        name, ok = QInputDialog.getText(
            None,
            "Salvar Captura",
            "Nome do template:",
            text=suggested_name
        )

        if ok and name:
            # Sanitiza nome
            name = "".join(c for c in name if c.isalnum() or c in "._- ")
            name = name.strip() or "template"

            # Garante extensão .png
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
