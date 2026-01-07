"""
Gerenciador de tasks para automação paralela.
Suporta tasks simples (clique único) e prompt handlers (múltiplas opções).
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .image_matcher import find_and_click, check_template_visible
from .window_utils import (
    find_window_by_title, find_window_by_process,
    find_all_windows_by_title, find_all_windows_by_process
)


@dataclass
class Task:
    """Representa uma tarefa de automação."""

    id: int
    window_title: str
    hwnd: Optional[int]
    image_name: str
    action: str = "click"  # click, double_click, right_click
    repeat: bool = False
    interval: float = 5.0  # segundos entre repetições
    enabled: bool = True
    last_status: str = "Aguardando"
    threshold: float = 0.85  # Threshold de detecção (0.0 a 1.0)

    # Prompt Handler fields
    task_type: str = "simple"  # "simple" ou "prompt_handler"
    options: Optional[List[dict]] = None  # [{"name": "Sim", "image": "btn_sim"}, ...]
    selected_option: int = 0  # índice da opção selecionada

    # Window selector fields
    window_method: str = "title"  # "title" ou "process"
    process_name: str = ""  # Nome do processo (ex: "Code.exe")
    title_filter: str = ""  # Filtro de título quando usa process
    window_index: int = 0  # Qual janela quando múltiplas (0, 1, 2...)

    def to_dict(self) -> dict:
        """Serializa task para dicionário."""
        data = {
            "id": self.id,
            "window_title": self.window_title,
            "image_name": self.image_name,
            "action": self.action,
            "repeat": self.repeat,
            "interval": self.interval,
            "enabled": self.enabled,
            "task_type": self.task_type,
            "window_method": self.window_method,
            "threshold": self.threshold
        }
        if self.window_method == "process":
            data["process_name"] = self.process_name
            data["title_filter"] = self.title_filter
            data["window_index"] = self.window_index
        if self.task_type == "prompt_handler" and self.options:
            data["options"] = self.options
            data["selected_option"] = self.selected_option
        return data

    @staticmethod
    def from_dict(data: dict) -> 'Task':
        """Cria task a partir de dicionário."""
        return Task(
            id=data["id"],
            window_title=data.get("window_title", ""),
            hwnd=None,
            image_name=data.get("image_name", ""),
            action=data.get("action", "click"),
            repeat=data.get("repeat", False),
            interval=data.get("interval", 5.0),
            enabled=data.get("enabled", True),
            threshold=data.get("threshold", 0.85),
            task_type=data.get("task_type", "simple"),
            options=data.get("options"),
            selected_option=data.get("selected_option", 0),
            window_method=data.get("window_method", "title"),
            process_name=data.get("process_name", ""),
            title_filter=data.get("title_filter", ""),
            window_index=data.get("window_index", 0)
        )

    def find_window(self) -> Optional[int]:
        """Encontra a janela usando o método configurado (retorna a primeira)."""
        if self.window_method == "process":
            return find_window_by_process(
                self.process_name,
                self.title_filter if self.title_filter else None,
                self.window_index
            )
        else:  # title
            return find_window_by_title(self.window_title)

    def find_all_windows(self) -> List[int]:
        """Encontra TODAS as janelas que correspondem ao padrão."""
        if self.window_method == "process":
            return find_all_windows_by_process(
                self.process_name,
                self.title_filter if self.title_filter else None
            )
        else:  # title
            return find_all_windows_by_title(self.window_title)


class TaskManager:
    """Gerencia execução paralela de múltiplas tasks."""

    def __init__(
        self,
        images_dir: Path,
        on_status_update: Optional[Callable[[int, str], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
        on_execution: Optional[Callable[[int, bool, float], None]] = None
    ):
        """
        Inicializa o gerenciador de tasks.

        Args:
            images_dir: Diretório onde estão os templates de imagem
            on_status_update: Callback chamado quando status de task muda
            on_log: Callback para mensagens de log
            on_execution: Callback chamado após cada execução (task_id, success, match_time_ms)
        """
        self.images_dir = images_dir
        self.tasks: Dict[int, Task] = {}
        self.running = False
        self.executor: Optional[ThreadPoolExecutor] = None
        self.task_threads: Dict[int, threading.Event] = {}
        self.on_status_update = on_status_update
        self.on_log = on_log
        self.on_execution = on_execution
        self._next_id = 1
        self._lock = threading.Lock()
        self._last_log_status: Dict[int, str] = {}  # Guarda último status logado por task

    def add_task(
        self,
        window_title: str,
        image_name: str = "",
        action: str = "click",
        repeat: bool = False,
        interval: float = 5.0,
        window_method: str = "title",
        process_name: str = "",
        title_filter: str = "",
        window_index: int = 0,
        threshold: float = 0.85,
        options: Optional[List[dict]] = None,
        selected_option: int = 0
    ) -> Task:
        """
        Adiciona nova task (unificado para simples e múltiplas opções).

        Args:
            window_title: Título da janela (ou nome se usa processo)
            image_name: Nome do template (modo simples)
            action: Tipo de clique (click, double_click, right_click)
            repeat: Se deve repetir continuamente
            interval: Intervalo entre repetições em segundos
            window_method: "title" ou "process"
            process_name: Nome do processo (ex: "Code.exe")
            title_filter: Filtro adicional de título
            window_index: Índice da janela quando múltiplas
            threshold: Threshold de detecção (0.0 a 1.0)
            options: Lista de opções [{"name": str, "image": str}, ...] (modo múltiplas)
            selected_option: Índice da opção selecionada (modo múltiplas)

        Se `options` for fornecido, cria uma task com múltiplas opções.
        Caso contrário, cria uma task simples com template único.
        """
        with self._lock:
            # Determina tipo baseado em options
            if options and len(options) > 0:
                task_type = "prompt_handler"
                # Múltiplas opções sempre repetem
                repeat = True
            else:
                task_type = "simple"
                options = None

            task = Task(
                id=self._next_id,
                window_title=window_title,
                hwnd=None,
                image_name=image_name,
                action=action,
                repeat=repeat,
                interval=interval,
                threshold=threshold,
                task_type=task_type,
                options=options,
                selected_option=selected_option,
                window_method=window_method,
                process_name=process_name,
                title_filter=title_filter,
                window_index=window_index
            )
            self.tasks[task.id] = task
            self._next_id += 1
            return task

    def add_prompt_handler(
        self,
        window_title: str,
        options: List[dict],
        action: str = "click",
        interval: float = 1.0,
        window_method: str = "title",
        process_name: str = "",
        title_filter: str = "",
        window_index: int = 0,
        threshold: float = 0.85
    ) -> Task:
        """
        Adiciona nova task do tipo prompt_handler.

        DEPRECATED: Use add_task() com parâmetro options.
        Mantido para compatibilidade.
        """
        return self.add_task(
            window_title=window_title,
            image_name="",
            action=action,
            repeat=True,
            interval=interval,
            window_method=window_method,
            process_name=process_name,
            title_filter=title_filter,
            window_index=window_index,
            threshold=threshold,
            options=options,
            selected_option=0
        )

    def remove_task(self, task_id: int):
        """Remove task."""
        if task_id in self.task_threads:
            self.task_threads[task_id].set()  # Sinaliza para parar
        with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]

    def get_task(self, task_id: int) -> Optional[Task]:
        """Retorna task por ID."""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        """Retorna todas as tasks."""
        return list(self.tasks.values())

    def update_task(self, task_id: int, **kwargs):
        """Atualiza campos de uma task."""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)

    def set_selected_option(self, task_id: int, option_index: int):
        """Atualiza a opção selecionada de um prompt_handler."""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.task_type == "prompt_handler" and task.options:
                    if 0 <= option_index < len(task.options):
                        task.selected_option = option_index
                        self._log(f"Task #{task_id}: Opção alterada para '{task.options[option_index]['name']}'")

    def start(self):
        """Inicia execução de todas as tasks habilitadas."""
        if self.running:
            return

        self.running = True
        enabled_tasks = [t for t in self.tasks.values() if t.enabled]

        if not enabled_tasks:
            self._log("Nenhuma task habilitada!")
            return

        self.executor = ThreadPoolExecutor(max_workers=len(enabled_tasks) + 1)

        for task in enabled_tasks:
            stop_event = threading.Event()
            self.task_threads[task.id] = stop_event
            self.executor.submit(self._run_task, task, stop_event)
            self._log(f"Task #{task.id} iniciada")

    def start_single(self, task_id: int):
        """Inicia execução de uma única task."""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]

        # Se já está rodando, não inicia de novo
        if task_id in self.task_threads:
            self._log(f"Task #{task_id} já está rodando")
            return

        self.running = True

        if not self.executor:
            self.executor = ThreadPoolExecutor(max_workers=10)

        stop_event = threading.Event()
        self.task_threads[task_id] = stop_event
        self.executor.submit(self._run_task, task, stop_event)

    def stop_single(self, task_id: int) -> bool:
        """Para execução de uma única task."""
        if task_id in self.task_threads:
            self.task_threads[task_id].set()  # Sinaliza para parar
            del self.task_threads[task_id]
            self._last_log_status.pop(task_id, None)  # Limpa histórico de log
            self._log(f"Task #{task_id} parada")
            if task_id in self.tasks:
                self._update_status(self.tasks[task_id], "Parado")
            return True
        return False

    def is_task_running(self, task_id: int) -> bool:
        """Verifica se uma task está rodando."""
        return task_id in self.task_threads

    def stop(self):
        """Para todas as tasks."""
        self.running = False

        # Sinaliza todas as threads para parar
        for event in self.task_threads.values():
            event.set()

        self.task_threads.clear()
        self._last_log_status.clear()  # Limpa histórico de log

        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None

    def _run_task(self, task: Task, stop_event: threading.Event):
        """Executa uma task individual em loop."""
        self._log(f"Task #{task.id}: Thread iniciada")

        while not stop_event.is_set() and self.running:
            import time
            start_time = time.time()

            # Busca TODAS as janelas que correspondem ao padrão
            all_windows = task.find_all_windows()

            if not all_windows:
                self._update_status(task, "Janela?")
                # Log diferente dependendo do método (apenas se mudou desde o último log)
                status_key = "window_not_found"
                if self._last_log_status.get(task.id) != status_key:
                    if task.window_method == "process":
                        self._log(f"Task #{task.id}: Processo '{task.process_name}' não encontrado")
                    else:
                        self._log(f"Task #{task.id}: Janela '{task.window_title[:30]}' não encontrada")
                    self._last_log_status[task.id] = status_key
                if not task.repeat:
                    break
                stop_event.wait(2)
                continue

            # Busca template em TODAS as janelas (para quando há múltiplas instâncias)
            success = False
            match = 0.0
            num_windows = len(all_windows)

            # Reseta status de "janela não encontrada" quando encontrar janelas
            if self._last_log_status.get(task.id) == "window_not_found":
                self._last_log_status.pop(task.id, None)

            self._update_status(task, f"Buscando ({num_windows})...")

            for hwnd in all_windows:
                if stop_event.is_set():
                    break

                task.hwnd = hwnd

                # Executa de acordo com o tipo de task
                if task.task_type == "prompt_handler":
                    found, m = self._run_prompt_handler(task, stop_event)
                else:
                    found, m = self._run_simple_task(task)

                if found:
                    success = True
                    match = m
                    break  # Encontrou em uma janela, para de buscar
                elif m > match:
                    match = m  # Guarda o melhor match encontrado

            # Calcula tempo de execução
            elapsed_ms = (time.time() - start_time) * 1000

            # Notifica execução para estatísticas
            if self.on_execution:
                self.on_execution(task.id, success, elapsed_ms)

            if success:
                self._update_status(task, f"{match:.0%}")
            else:
                self._update_status(task, f"{match:.0%}")

            if not task.repeat:
                self._log(f"Task #{task.id}: Execução única finalizada")
                break

            # Aguarda intervalo
            self._update_status(task, f"{task.interval}s")
            stop_event.wait(task.interval)

        self._update_status(task, "Parado")
        self._log(f"Task #{task.id}: Thread parada")

    def _run_simple_task(self, task: Task, silent: bool = False) -> tuple:
        """
        Executa uma task simples (busca uma imagem e clica).

        Args:
            task: Task a executar
            silent: Se True, não gera logs de "não encontrou" (usado em busca multi-janela)
        """
        template_path = self.images_dir / f"{task.image_name}.png"
        if not template_path.exists():
            if not silent:
                self._update_status(task, "Img?")
                self._log(f"Task #{task.id}: Imagem '{task.image_name}' não existe")
            return False, 0.0

        # Executa busca (sem debug_callback para evitar logs excessivos)
        success, msg, match = find_and_click(
            task.hwnd, template_path, task.action,
            threshold=task.threshold
        )

        if success:
            self._log(f"Task #{task.id}: Clicou! ({match:.0%})")

        return success, match

    def _run_prompt_handler(self, task: Task, stop_event: threading.Event, silent: bool = False) -> tuple:
        """
        Executa uma task do tipo prompt_handler.
        1. Verifica se TODAS as opções estão visíveis (confirma que é o prompt correto)
        2. Se todas visíveis, clica no botão da opção selecionada

        Args:
            task: Task a executar
            stop_event: Evento de parada
            silent: Se True, não gera logs de "não encontrou" (usado em busca multi-janela)
        """
        if not task.options:
            if not silent:
                self._log(f"Task #{task.id}: Nenhuma opção configurada")
            return False, 0.0

        # Verifica se TODAS as opções estão visíveis (garante que é o prompt correto)
        all_visible = True
        best_match = 0.0
        visible_count = 0
        total_options = len(task.options)

        for opt in task.options:
            if stop_event.is_set():
                return False, 0.0
            template_path = self.images_dir / f"{opt['image']}.png"
            if template_path.exists():
                visible, match = check_template_visible(task.hwnd, template_path, threshold=task.threshold)
                if match > best_match:
                    best_match = match
                if visible:
                    visible_count += 1
                else:
                    all_visible = False
            else:
                all_visible = False
                if not silent:
                    self._log(f"Task #{task.id}: Template '{opt['image']}' não encontrado")

        if not all_visible:
            # Log parcial se algumas foram encontradas (apenas se mudou desde o último log)
            if visible_count > 0 and not silent:
                status_key = f"partial_{visible_count}_{total_options}"
                if self._last_log_status.get(task.id) != status_key:
                    self._log(f"Task #{task.id}: {visible_count}/{total_options} opções visíveis (aguardando todas)")
                    self._last_log_status[task.id] = status_key
            return False, best_match

        # Todas as opções visíveis - prompt confirmado!
        self._log(f"Task #{task.id}: Prompt confirmado! ({total_options}/{total_options} opções visíveis)")
        # Reseta status de log para permitir novos logs quando voltar ao estado parcial
        self._last_log_status.pop(task.id, None)

        # Prompt visível - clica na opção selecionada
        selected_idx = task.selected_option
        if selected_idx < 0 or selected_idx >= len(task.options):
            selected_idx = 0

        selected_opt = task.options[selected_idx]
        selected_template = self.images_dir / f"{selected_opt['image']}.png"

        if not selected_template.exists():
            if not silent:
                self._update_status(task, "Img?")
                self._log(f"Task #{task.id}: Imagem da opção '{selected_opt['name']}' não existe")
            return False, best_match

        self._update_status(task, f"{selected_opt['name']}")
        success, msg, match = find_and_click(
            task.hwnd, selected_template, task.action,
            threshold=task.threshold
        )

        if success:
            self._log(f"Task #{task.id}: Clicou em '{selected_opt['name']}' ({match:.0%})")

        return success, match if success else best_match

    def _update_status(self, task: Task, status: str):
        """Atualiza status da task."""
        task.last_status = status
        if self.on_status_update:
            self.on_status_update(task.id, status)

    def _log(self, msg: str):
        """Envia mensagem para log."""
        if self.on_log:
            self.on_log(msg)

    def save_tasks(self, filepath: Path):
        """Salva tasks em JSON."""
        with self._lock:
            data = [task.to_dict() for task in self.tasks.values()]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_tasks(self, filepath: Path):
        """Carrega tasks de JSON."""
        if not filepath.exists():
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with self._lock:
                self.tasks.clear()
                for item in data:
                    task = Task.from_dict(item)
                    self.tasks[task.id] = task
                    self._next_id = max(self._next_id, task.id + 1)
        except Exception as e:
            print(f"Erro ao carregar tasks: {e}")

    def clear_tasks(self):
        """Remove todas as tasks."""
        self.stop()
        with self._lock:
            self.tasks.clear()
            self._next_id = 1
