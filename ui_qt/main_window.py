"""
Janela principal da aplicação.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon
from pathlib import Path
import sys


class LogSignals(QObject):
    """Signals para log thread-safe."""
    log_message = pyqtSignal(str, str)  # message, level

from .theme import get_stylesheet
from .components.sidebar import Sidebar
from .pages.dashboard import DashboardPage
from .pages.tasks import TasksPage
from .pages.templates import TemplatesPage
from .pages.prompts import PromptsPage
from .pages.settings import SettingsPage


class MainWindow(QMainWindow):
    """Janela principal ImageClicker."""

    def __init__(self):
        super().__init__()

        # Paths
        self.base_dir = Path(__file__).parent.parent
        self.images_dir = self.base_dir / "images"
        self.tasks_file = self.base_dir / "tasks.json"

        # Garante que diretório existe
        self.images_dir.mkdir(exist_ok=True)

        # Log signals (thread-safe)
        self._log_signals = LogSignals()
        self._log_signals.log_message.connect(self._handle_log)

        # TaskManager
        self.task_manager = None
        self._init_task_manager()

        # Window setup
        self.setWindowTitle("ImageClicker")
        self.setMinimumSize(1024, 600)
        self.resize(1280, 800)

        # Ícone da janela
        icon_path = self.base_dir / "final_icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Aplica tema
        self.setStyleSheet(get_stylesheet())

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self.navigate)
        layout.addWidget(self.sidebar)

        # Content area (stacked pages)
        self.pages = QStackedWidget()
        layout.addWidget(self.pages, 1)

        # Cria páginas
        self._pages = {}
        self._create_pages()

        # Seleciona dashboard
        self.navigate("dashboard")

        # Pré-carrega OCR em background para capturas mais rápidas
        self._preload_ocr()

    def _preload_ocr(self):
        """Pré-carrega modelo OCR em background."""
        import threading

        def _load():
            try:
                from .components.capture_overlay import _get_ocr_reader
                reader = _get_ocr_reader()
                if reader:
                    self._log_signals.log_message.emit("OCR pronto para uso", "info")
            except Exception:
                pass

        thread = threading.Thread(target=_load, daemon=True)
        thread.start()

    def _init_task_manager(self):
        """Inicializa TaskManager."""
        try:
            from core import TaskManager
            self.task_manager = TaskManager(
                images_dir=self.images_dir,
                on_log=self._on_log,
                on_status_update=self._on_status_update
            )
            self.task_manager.load_tasks(self.tasks_file)
        except Exception as e:
            print(f"Erro ao inicializar TaskManager: {e}")

    def _create_pages(self):
        """Cria todas as páginas."""
        pages_config = [
            ("dashboard", DashboardPage),
            ("tasks", TasksPage),
            ("templates", TemplatesPage),
            ("prompts", PromptsPage),
            ("settings", SettingsPage),
        ]

        for page_id, page_class in pages_config:
            page = page_class(app=self)
            self._pages[page_id] = page
            self.pages.addWidget(page)

    def navigate(self, page_id: str):
        """Navega para página."""
        if page_id in self._pages:
            page = self._pages[page_id]
            self.pages.setCurrentWidget(page)
            self.sidebar.set_current(page_id)
            page.on_show()

    def start_capture(self):
        """Inicia captura de tela com seleção de área."""
        # Minimiza janela
        self.showMinimized()

        # Pequeno delay para garantir que a janela minimizou
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(200, self._show_capture_overlay)

    def _show_capture_overlay(self):
        """Mostra overlay de captura."""
        from .components.capture_overlay import CaptureOverlay

        self._capture_overlay = CaptureOverlay(
            save_dir=self.images_dir,
            on_complete=self._on_capture_complete
        )
        self._capture_overlay.start()

    def _on_capture_complete(self, path: Path):
        """Callback quando captura termina."""
        self.showNormal()
        self.log(f"Captura salva: {path.name}")
        self.navigate("templates")
        self._pages["templates"].refresh()

    def _on_log(self, message: str):
        """Callback de log do TaskManager (pode ser chamado de outra thread)."""
        # Detecta nível pelo conteúdo
        level = "info"
        msg_lower = message.lower()
        if "erro" in msg_lower or "falha" in msg_lower or "não encontr" in msg_lower:
            level = "error"
        elif "encontr" in msg_lower or "clicou" in msg_lower or "sucesso" in msg_lower:
            level = "success"
        elif "buscando" in msg_lower or "aguardando" in msg_lower:
            level = "info"

        # Usa signal para thread-safety
        self._log_signals.log_message.emit(message, level)

    def _on_status_update(self, task_id: int, status: str):
        """Callback de status do TaskManager."""
        # Atualiza páginas se necessário
        pass

    def _handle_log(self, message: str, level: str):
        """Handler de log na thread principal (slot)."""
        print(f"[{level.upper()}] {message}")

        # Envia para o LogPanel do Dashboard
        if "dashboard" in self._pages:
            self._pages["dashboard"].add_log(message, level)

    def log(self, message: str, level: str = "info"):
        """Log na interface (chamado da thread principal)."""
        self._handle_log(message, level)

    def closeEvent(self, event):
        """Ao fechar janela."""
        # Para todas as tasks
        if self.task_manager:
            self.task_manager.stop()

        event.accept()


def run():
    """Entry point da aplicação."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Estilo consistente

    # Define ícone do app (aparece na taskbar)
    base_dir = Path(__file__).parent.parent
    icon_path = base_dir / "final_icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run()
