"""
Sistema de onboarding para novos usuários.
Inclui welcome modal, tour guiado e checklist de início rápido.
"""

import json
from pathlib import Path
from typing import Optional, Callable, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget, QCheckBox
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont

from ..theme import Theme


class OnboardingState:
    """Gerencia estado do onboarding persistido em arquivo."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._state = self._load()

    def _load(self) -> dict:
        """Carrega estado do arquivo."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "welcome_shown": False,
            "tour_completed": False,
            "checklist": {
                "capture_template": False,
                "create_task": False,
                "run_automation": False,
                "explore_settings": False
            }
        }

    def save(self):
        """Salva estado no arquivo."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, indent=2)
        except Exception:
            pass

    @property
    def welcome_shown(self) -> bool:
        return self._state.get("welcome_shown", False)

    @welcome_shown.setter
    def welcome_shown(self, value: bool):
        self._state["welcome_shown"] = value
        self.save()

    @property
    def tour_completed(self) -> bool:
        return self._state.get("tour_completed", False)

    @tour_completed.setter
    def tour_completed(self, value: bool):
        self._state["tour_completed"] = value
        self.save()

    def is_checklist_item_done(self, item: str) -> bool:
        return self._state.get("checklist", {}).get(item, False)

    def complete_checklist_item(self, item: str):
        if "checklist" not in self._state:
            self._state["checklist"] = {}
        self._state["checklist"][item] = True
        self.save()

    def get_checklist_progress(self) -> tuple[int, int]:
        """Retorna (completos, total)."""
        checklist = self._state.get("checklist", {})
        total = len(checklist)
        done = sum(1 for v in checklist.values() if v)
        return done, total

    def is_new_user(self) -> bool:
        """Verifica se é um usuário novo."""
        return not self.welcome_shown


class WelcomeDialog(QDialog):
    """Modal de boas-vindas para primeira execução."""

    start_tour = pyqtSignal()
    skip_tour = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        """Constrói a interface do dialog."""
        self.setWindowTitle("Bem-vindo ao ImageClicker")
        self.setFixedSize(520, 420)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_PRIMARY};
                border: 1px solid {Theme.GLASS_BORDER};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # Ícone/Logo
        logo_label = QLabel("🖱️")
        logo_label.setStyleSheet("font-size: 64px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        # Título
        title = QLabel("Bem-vindo ao ImageClicker")
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {Theme.TEXT_PRIMARY};
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Descrição
        desc = QLabel(
            "Automatize cliques em qualquer aplicação usando\n"
            "reconhecimento de imagem. Simples e poderoso."
        )
        desc.setStyleSheet(f"""
            font-size: 14px;
            color: {Theme.TEXT_SECONDARY};
            line-height: 1.5;
        """)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(10)

        # Features rápidas
        features_frame = QFrame()
        features_frame.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BG_GLASS_LIGHT};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        features_layout = QVBoxLayout(features_frame)
        features_layout.setSpacing(12)

        features = [
            ("📸", "Capture", "Selecione áreas da tela como templates"),
            ("🎯", "Detecte", "O app encontra os templates automaticamente"),
            ("🖱️", "Clique", "Cliques fantasma sem roubar foco"),
        ]

        for emoji, title, desc in features:
            row = QHBoxLayout()
            row.setSpacing(12)

            icon = QLabel(emoji)
            icon.setStyleSheet("font-size: 20px; background: transparent;")
            icon.setFixedWidth(30)
            row.addWidget(icon)

            text_layout = QVBoxLayout()
            text_layout.setSpacing(2)

            title_lbl = QLabel(title)
            title_lbl.setStyleSheet(f"""
                font-size: 13px;
                font-weight: bold;
                color: {Theme.TEXT_PRIMARY};
                background: transparent;
            """)
            text_layout.addWidget(title_lbl)

            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"""
                font-size: 11px;
                color: {Theme.TEXT_MUTED};
                background: transparent;
            """)
            text_layout.addWidget(desc_lbl)

            row.addLayout(text_layout, 1)
            features_layout.addLayout(row)

        layout.addWidget(features_frame)

        layout.addStretch()

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        skip_btn = QPushButton("Pular")
        skip_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.GLASS_BORDER};
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {Theme.BG_GLASS_LIGHT};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        skip_btn.clicked.connect(self._on_skip)
        btn_layout.addWidget(skip_btn)

        start_btn = QPushButton("Começar Tour  →")
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT_PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 32px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {Theme.ACCENT_PRIMARY_HOVER};
            }}
        """)
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.clicked.connect(self._on_start)
        btn_layout.addWidget(start_btn)

        layout.addLayout(btn_layout)

    def _on_skip(self):
        self.skip_tour.emit()
        self.accept()

    def _on_start(self):
        self.start_tour.emit()
        self.accept()


class QuickStartChecklist(QFrame):
    """Widget de checklist compacto para o Dashboard - layout horizontal."""

    item_clicked = pyqtSignal(str)  # item_id

    def __init__(self, state: OnboardingState, parent=None):
        super().__init__(parent)
        self.state = state
        self._build_ui()

    def _build_ui(self):
        """Constrói a interface do checklist compacto."""
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BG_GLASS};
                border: 1px solid {Theme.GLASS_BORDER};
                border-radius: 8px;
            }}
        """)
        self.setFixedHeight(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Título
        title = QLabel("🚀 Início Rápido")
        title.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {Theme.TEXT_PRIMARY};
            background: transparent;
        """)
        layout.addWidget(title)

        # Progresso
        done, total = self.state.get_checklist_progress()
        self.progress_label = QLabel(f"{done}/{total}")
        self.progress_label.setStyleSheet(f"""
            font-size: 11px;
            color: {Theme.ACCENT_PRIMARY};
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(self.progress_label)

        layout.addSpacing(8)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"background: {Theme.GLASS_BORDER}; max-width: 1px;")
        layout.addWidget(sep)

        layout.addSpacing(8)

        # Itens em linha
        items = [
            ("capture_template", "📸", "Capturar"),
            ("create_task", "➕", "Criar Task"),
            ("run_automation", "▶️", "Executar"),
            ("explore_settings", "⚙️", "Configurar"),
        ]

        self._item_widgets = {}

        for item_id, emoji, text in items:
            is_done = self.state.is_checklist_item_done(item_id)
            item = self._create_item(item_id, emoji, text, is_done)
            layout.addWidget(item)
            self._item_widgets[item_id] = item

        layout.addStretch()

    def _create_item(self, item_id: str, emoji: str, text: str, is_done: bool) -> QFrame:
        """Cria um item compacto do checklist."""
        item = QFrame()
        item.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BG_GLASS_LIGHT if is_done else "transparent"};
                border-radius: 6px;
                padding: 2px 6px;
            }}
            QFrame:hover {{
                background: {Theme.BG_GLASS_LIGHTER};
            }}
        """)
        item.setCursor(Qt.CursorShape.PointingHandCursor)

        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(6, 4, 8, 4)
        item_layout.setSpacing(4)

        # Checkbox
        check = QLabel("✓" if is_done else "○")
        check.setStyleSheet(f"""
            font-size: 11px;
            color: {Theme.SUCCESS if is_done else Theme.TEXT_MUTED};
            background: transparent;
        """)
        item_layout.addWidget(check)

        # Emoji + Texto
        label = QLabel(f"{emoji} {text}")
        label.setStyleSheet(f"""
            font-size: 11px;
            color: {Theme.TEXT_MUTED if is_done else Theme.TEXT_PRIMARY};
            background: transparent;
            {"text-decoration: line-through;" if is_done else ""}
        """)
        item_layout.addWidget(label)

        # Click handler
        item.setProperty("item_id", item_id)
        item.mousePressEvent = lambda e, id=item_id: self.item_clicked.emit(id)

        return item

    def mark_complete(self, item_id: str):
        """Marca um item como completo."""
        self.state.complete_checklist_item(item_id)
        self.refresh()

    def refresh(self):
        """Atualiza visual do checklist."""
        done, total = self.state.get_checklist_progress()
        self.progress_label.setText(f"{done}/{total}")

        # Oculta se tudo completo
        if done >= total:
            self.hide()

    def is_all_complete(self) -> bool:
        """Verifica se todos os itens estão completos."""
        done, total = self.state.get_checklist_progress()
        return done >= total


class TourStep:
    """Define um passo do tour guiado."""

    def __init__(
        self,
        target_page: str,
        title: str,
        description: str,
        position: str = "center"  # center, top, bottom
    ):
        self.target_page = target_page
        self.title = title
        self.description = description
        self.position = position


class TourOverlay(QDialog):
    """Overlay para tour guiado."""

    tour_completed = pyqtSignal()
    tour_skipped = pyqtSignal()

    STEPS = [
        TourStep(
            "dashboard",
            "Dashboard",
            "Aqui você vê o resumo das suas automações,\n"
            "estatísticas e o log de atividades."
        ),
        TourStep(
            "templates",
            "Templates",
            "Capture imagens da tela para usar como\n"
            "alvos de clique. Use Ctrl+Shift+C."
        ),
        TourStep(
            "tasks",
            "Tasks",
            "Crie automações que buscam templates\n"
            "e executam cliques automaticamente."
        ),
        TourStep(
            "prompts",
            "Prompts",
            "Configure sequências de ações para\n"
            "automações mais complexas."
        ),
        TourStep(
            "settings",
            "Configurações",
            "Personalize o comportamento do app\n"
            "conforme suas preferências."
        ),
    ]

    def __init__(self, navigate_callback: Callable, parent=None):
        super().__init__(parent)
        self.navigate = navigate_callback
        self.current_step = 0
        self._build_ui()

    def _build_ui(self):
        """Constrói a interface do tour."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedSize(400, 200)

        # Container
        container = QFrame(self)
        container.setGeometry(0, 0, 400, 200)
        container.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BG_PRIMARY};
                border: 2px solid {Theme.ACCENT_PRIMARY};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Step indicator
        self.step_label = QLabel()
        self.step_label.setStyleSheet(f"""
            font-size: 11px;
            color: {Theme.ACCENT_PRIMARY};
            font-weight: bold;
        """)
        layout.addWidget(self.step_label)

        # Título
        self.title_label = QLabel()
        self.title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {Theme.TEXT_PRIMARY};
        """)
        layout.addWidget(self.title_label)

        # Descrição
        self.desc_label = QLabel()
        self.desc_label.setStyleSheet(f"""
            font-size: 13px;
            color: {Theme.TEXT_SECONDARY};
            line-height: 1.4;
        """)
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        layout.addStretch()

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.skip_btn = QPushButton("Pular Tour")
        self.skip_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_MUTED};
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        self.skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.skip_btn.clicked.connect(self._skip)
        btn_layout.addWidget(self.skip_btn)

        btn_layout.addStretch()

        self.prev_btn = QPushButton("← Anterior")
        self.prev_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.BG_GLASS_LIGHT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.GLASS_BORDER};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {Theme.BG_GLASS};
            }}
        """)
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self._prev)
        btn_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Próximo →")
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT_PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {Theme.ACCENT_PRIMARY_HOVER};
            }}
        """)
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.clicked.connect(self._next)
        btn_layout.addWidget(self.next_btn)

        layout.addLayout(btn_layout)

        self._update_step()

    def _update_step(self):
        """Atualiza conteúdo para o step atual."""
        step = self.STEPS[self.current_step]

        self.step_label.setText(f"Passo {self.current_step + 1} de {len(self.STEPS)}")
        self.title_label.setText(step.title)
        self.desc_label.setText(step.description)

        # Navega para a página
        self.navigate(step.target_page)

        # Atualiza botões
        self.prev_btn.setVisible(self.current_step > 0)

        if self.current_step >= len(self.STEPS) - 1:
            self.next_btn.setText("Concluir ✓")
        else:
            self.next_btn.setText("Próximo →")

        # Posiciona o overlay
        self._position_overlay()

    def _position_overlay(self):
        """Posiciona overlay no centro da janela pai."""
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

    def _next(self):
        """Vai para próximo step."""
        if self.current_step >= len(self.STEPS) - 1:
            self.tour_completed.emit()
            self.accept()
        else:
            self.current_step += 1
            self._update_step()

    def _prev(self):
        """Vai para step anterior."""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_step()

    def _skip(self):
        """Pula o tour."""
        self.tour_skipped.emit()
        self.reject()

    def start(self):
        """Inicia o tour."""
        self.current_step = 0
        self._update_step()
        self.show()
