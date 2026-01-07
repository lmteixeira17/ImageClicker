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
    task_click = pyqtSignal(int)  # task_id - emitido quando uma task faz um clique

from .theme import get_stylesheet
from .components.sidebar import Sidebar
from .components.toast_notification import ToastManager
from .components.help_dialog import HelpDialog
from .components.onboarding import OnboardingState, WelcomeDialog, TourOverlay
from .keyboard_manager import KeyboardManager
from .pages.dashboard import DashboardPage
from .pages.tasks import TasksPage
from .pages.templates import TemplatesPage
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
        self._log_signals.task_click.connect(self._handle_task_click)

        # Toast Manager
        self.toast = ToastManager(self)

        # Keyboard Manager
        self.keyboard = KeyboardManager(self)

        # Onboarding State
        self.onboarding = OnboardingState(self.base_dir / ".imageclicker_config.json")

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

        # Configura atalhos de teclado
        self._setup_shortcuts()

        # Pré-carrega OCR em background para capturas mais rápidas
        self._preload_ocr()

        # Mostra onboarding se for novo usuário
        self._check_onboarding()

    def _setup_shortcuts(self):
        """Configura todos os atalhos de teclado."""
        # Navegação
        self.keyboard.register_callback("nav_dashboard", lambda: self.navigate("dashboard"))
        self.keyboard.register_callback("nav_tasks", lambda: self.navigate("tasks"))
        self.keyboard.register_callback("nav_templates", lambda: self.navigate("templates"))
        self.keyboard.register_callback("nav_settings", lambda: self.navigate("settings"))

        # Ações
        self.keyboard.register_callback("capture", self.start_capture)
        self.keyboard.register_callback("new_task", self._shortcut_new_task)

        # Tasks
        self.keyboard.register_callback("start_all", self._shortcut_start_all)
        self.keyboard.register_callback("stop_all", self._shortcut_stop_all)

        # Ajuda
        self.keyboard.register_callback("show_help", self.show_help)
        self.keyboard.register_callback("show_shortcuts", self.show_help)
        self.keyboard.register_callback("show_settings", lambda: self.navigate("settings"))

    def _shortcut_new_task(self):
        """Atalho para criar nova task."""
        self.navigate("tasks")
        if "tasks" in self._pages:
            self._pages["tasks"].open_new_task_dialog()

    def _shortcut_start_all(self):
        """Atalho para iniciar todas as tasks."""
        if self.task_manager:
            count = 0
            for task in self.task_manager.tasks:
                if not task.is_running:
                    self.task_manager.start(task.id)
                    count += 1
            if count > 0:
                self.toast.success(f"{count} tasks iniciadas")
            else:
                self.toast.info("Nenhuma task para iniciar")

    def _shortcut_stop_all(self):
        """Atalho para parar todas as tasks."""
        if self.task_manager:
            count = 0
            for task in self.task_manager.tasks:
                if task.is_running:
                    self.task_manager.stop(task.id)
                    count += 1
            if count > 0:
                self.toast.warning(f"{count} tasks paradas")
            else:
                self.toast.info("Nenhuma task rodando")

    def show_help(self):
        """Mostra dialog de ajuda com atalhos."""
        dialog = HelpDialog(self.keyboard, self)
        dialog.exec()

    def _check_onboarding(self):
        """Verifica e mostra onboarding se necessário."""
        from PyQt6.QtCore import QTimer

        if self.onboarding.is_new_user():
            # Delay pequeno para janela estar visível
            QTimer.singleShot(500, self._show_welcome)

    def _show_welcome(self):
        """Mostra dialog de boas-vindas."""
        dialog = WelcomeDialog(self)
        dialog.start_tour.connect(self._start_tour)
        dialog.skip_tour.connect(self._skip_onboarding)
        dialog.exec()

    def _start_tour(self):
        """Inicia tour guiado."""
        self.onboarding.welcome_shown = True

        tour = TourOverlay(self.navigate, self)
        tour.tour_completed.connect(self._on_tour_complete)
        tour.tour_skipped.connect(self._on_tour_skipped)
        tour.start()

    def _skip_onboarding(self):
        """Pula onboarding."""
        self.onboarding.welcome_shown = True
        self.toast.info("Use Ctrl+H para ver atalhos a qualquer momento")

    def _on_tour_complete(self):
        """Callback quando tour é completado."""
        self.onboarding.tour_completed = True
        self.toast.success("Tour concluído! Você está pronto para começar.")
        self.navigate("dashboard")

    def _on_tour_skipped(self):
        """Callback quando tour é pulado."""
        self.toast.info("Use Ctrl+H para ver atalhos a qualquer momento")

    def complete_onboarding_step(self, step: str):
        """Marca um passo do onboarding como completo."""
        self.onboarding.complete_checklist_item(step)

        # Atualiza checklist no dashboard se visível
        if "dashboard" in self._pages:
            dashboard = self._pages["dashboard"]
            if hasattr(dashboard, 'refresh_checklist'):
                dashboard.refresh_checklist()

    def _preload_ocr(self):
        """Pré-carrega modelo OCR em background."""
        import threading

        def _load():
            try:
                from .components.capture_overlay import _get_ocr_reader
                reader = _get_ocr_reader()
                if reader:
                    self._log_signals.log_message.emit("OCR carregado e pronto", "success")
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
                on_status_update=self._on_status_update,
                on_execution=self._on_execution
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
        # Detecta nível pelo conteúdo da mensagem
        level = "info"
        msg_lower = message.lower()

        # Detecta tipo de mensagem para escolher emoji/cor apropriados
        if "clicou" in msg_lower:
            level = "click"
        elif "detectado" in msg_lower or "visível" in msg_lower:
            level = "found"
        elif "thread iniciada" in msg_lower or "iniciando" in msg_lower:
            level = "start"
        elif "thread parada" in msg_lower or "parado" in msg_lower or "finalizada" in msg_lower:
            level = "stop"
        elif "buscando" in msg_lower or "aguardando" in msg_lower:
            level = "search"
        elif "não encontr" in msg_lower or "não visível" in msg_lower:
            level = "notfound"
        elif "erro" in msg_lower or "falha" in msg_lower or "não existe" in msg_lower:
            level = "error"
        elif "janela" in msg_lower and "não" not in msg_lower:
            level = "window"
        elif "task #" in msg_lower:
            level = "task"

        # Usa signal para thread-safety
        self._log_signals.log_message.emit(message, level)

    def _on_status_update(self, task_id: int, status: str):
        """Callback de status do TaskManager."""
        # Atualiza páginas se necessário
        pass

    def _on_execution(self, task_id: int, success: bool, elapsed_ms: float):
        """Callback de execução do TaskManager (chamado após cada tentativa)."""
        if success:
            # Emite signal para incrementar contador (thread-safe)
            self._log_signals.task_click.emit(task_id)

    def _handle_log(self, message: str, level: str):
        """Handler de log na thread principal (slot)."""
        print(f"[{level.upper()}] {message}")

        # Envia para o LogPanel do Dashboard
        if "dashboard" in self._pages:
            self._pages["dashboard"].add_log(message, level)

    def _handle_task_click(self, task_id: int):
        """Handler de clique de task na thread principal (slot)."""
        # Incrementa contador na página Tasks
        if "tasks" in self._pages:
            self._pages["tasks"].increment_click_count(task_id)

        # Incrementa contador na página Dashboard
        if "dashboard" in self._pages:
            self._pages["dashboard"].increment_click_count(task_id)

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
