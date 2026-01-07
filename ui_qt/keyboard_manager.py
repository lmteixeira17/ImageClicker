"""
Gerenciador de atalhos de teclado para a aplicação.
Define todos os shortcuts globais e fornece configuração centralizada.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget


@dataclass
class ShortcutDefinition:
    """Definição de um atalho de teclado."""
    key: str  # Ex: "Ctrl+N", "F1", "D"
    action_id: str  # ID único da ação
    description: str  # Descrição para exibição
    category: str  # Categoria (navigation, actions, etc)
    callback: Optional[Callable] = None  # Função a executar
    enabled: bool = True


class KeyboardManager:
    """
    Gerenciador centralizado de atalhos de teclado.

    Permite:
    - Definir shortcuts globais
    - Ativar/desativar shortcuts
    - Listar todos os shortcuts disponíveis
    - Detectar conflitos
    """

    # Categorias de atalhos
    CATEGORY_NAVIGATION = "Navegação"
    CATEGORY_ACTIONS = "Ações"
    CATEGORY_TASKS = "Tasks"
    CATEGORY_HELP = "Ajuda"

    def __init__(self, parent: QWidget):
        self.parent = parent
        self._shortcuts: Dict[str, ShortcutDefinition] = {}
        self._qt_shortcuts: Dict[str, QShortcut] = {}
        self._setup_default_shortcuts()

    def _setup_default_shortcuts(self):
        """Define os atalhos padrão da aplicação."""
        defaults = [
            # Navegação
            ShortcutDefinition(
                key="Ctrl+1", action_id="nav_dashboard",
                description="Ir para Dashboard",
                category=self.CATEGORY_NAVIGATION
            ),
            ShortcutDefinition(
                key="Ctrl+2", action_id="nav_tasks",
                description="Ir para Tasks",
                category=self.CATEGORY_NAVIGATION
            ),
            ShortcutDefinition(
                key="Ctrl+3", action_id="nav_templates",
                description="Ir para Templates",
                category=self.CATEGORY_NAVIGATION
            ),
            ShortcutDefinition(
                key="Ctrl+4", action_id="nav_settings",
                description="Ir para Configurações",
                category=self.CATEGORY_NAVIGATION
            ),

            # Ações principais
            ShortcutDefinition(
                key="Ctrl+Shift+C", action_id="capture",
                description="Capturar template",
                category=self.CATEGORY_ACTIONS
            ),
            ShortcutDefinition(
                key="Ctrl+N", action_id="new_task",
                description="Nova task",
                category=self.CATEGORY_ACTIONS
            ),

            # Tasks
            ShortcutDefinition(
                key="Ctrl+E", action_id="start_all",
                description="Executar todas as tasks",
                category=self.CATEGORY_TASKS
            ),
            ShortcutDefinition(
                key="Ctrl+Shift+S", action_id="stop_all",
                description="Parar todas as tasks",
                category=self.CATEGORY_TASKS
            ),

            # Ajuda
            ShortcutDefinition(
                key="F1", action_id="show_help",
                description="Mostrar ajuda",
                category=self.CATEGORY_HELP
            ),
            ShortcutDefinition(
                key="Ctrl+H", action_id="show_shortcuts",
                description="Mostrar atalhos",
                category=self.CATEGORY_HELP
            ),
            ShortcutDefinition(
                key="Ctrl+,", action_id="show_settings",
                description="Configurações",
                category=self.CATEGORY_HELP
            ),
        ]

        for shortcut_def in defaults:
            self._shortcuts[shortcut_def.action_id] = shortcut_def

    def register_callback(self, action_id: str, callback: Callable):
        """
        Registra callback para um atalho.

        Args:
            action_id: ID da ação
            callback: Função a ser chamada
        """
        if action_id in self._shortcuts:
            self._shortcuts[action_id].callback = callback
            self._create_qt_shortcut(action_id)

    def _create_qt_shortcut(self, action_id: str):
        """Cria o QShortcut real para um atalho."""
        if action_id not in self._shortcuts:
            return

        shortcut_def = self._shortcuts[action_id]

        if not shortcut_def.callback or not shortcut_def.enabled:
            return

        # Remove shortcut existente
        if action_id in self._qt_shortcuts:
            self._qt_shortcuts[action_id].deleteLater()

        # Cria novo
        qt_shortcut = QShortcut(
            QKeySequence(shortcut_def.key),
            self.parent
        )
        qt_shortcut.activated.connect(shortcut_def.callback)
        self._qt_shortcuts[action_id] = qt_shortcut

    def enable(self, action_id: str):
        """Ativa um atalho."""
        if action_id in self._shortcuts:
            self._shortcuts[action_id].enabled = True
            if action_id in self._qt_shortcuts:
                self._qt_shortcuts[action_id].setEnabled(True)

    def disable(self, action_id: str):
        """Desativa um atalho."""
        if action_id in self._shortcuts:
            self._shortcuts[action_id].enabled = False
            if action_id in self._qt_shortcuts:
                self._qt_shortcuts[action_id].setEnabled(False)

    def get_all_shortcuts(self) -> List[ShortcutDefinition]:
        """Retorna todos os atalhos definidos."""
        return list(self._shortcuts.values())

    def get_shortcuts_by_category(self) -> Dict[str, List[ShortcutDefinition]]:
        """Retorna atalhos agrupados por categoria."""
        by_category: Dict[str, List[ShortcutDefinition]] = {}

        for shortcut in self._shortcuts.values():
            if shortcut.category not in by_category:
                by_category[shortcut.category] = []
            by_category[shortcut.category].append(shortcut)

        return by_category

    def get_key_for_action(self, action_id: str) -> Optional[str]:
        """Retorna a tecla associada a uma ação."""
        if action_id in self._shortcuts:
            return self._shortcuts[action_id].key
        return None

    def format_shortcut_key(self, key: str) -> str:
        """
        Formata a tecla para exibição.
        Ex: "Ctrl+Shift+C" -> "Ctrl + Shift + C"
        """
        return key.replace("+", " + ")

    def activate_all(self):
        """Ativa todos os atalhos com callbacks registrados."""
        for action_id, shortcut_def in self._shortcuts.items():
            if shortcut_def.callback and shortcut_def.enabled:
                self._create_qt_shortcut(action_id)

    def deactivate_all(self):
        """Desativa todos os atalhos temporariamente."""
        for qt_shortcut in self._qt_shortcuts.values():
            qt_shortcut.setEnabled(False)

    def cleanup(self):
        """Limpa todos os shortcuts."""
        for qt_shortcut in self._qt_shortcuts.values():
            qt_shortcut.deleteLater()
        self._qt_shortcuts.clear()
