"""
Utilitários para manipulação de janelas Windows.
Funções para encontrar, listar e obter informações de janelas.
"""

import ctypes
from typing import List, Optional, Tuple

import win32api
import win32con
import win32gui
import win32process


def get_windows() -> List[Tuple[int, str]]:
    """
    Retorna lista de janelas visíveis.

    Returns:
        Lista de tuplas (hwnd, título) ordenadas por título
    """
    windows = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and len(title) > 2:
                windows.append((hwnd, title))
        return True

    win32gui.EnumWindows(callback, None)
    return sorted(windows, key=lambda x: x[1].lower())


def get_window_dpi_scale(hwnd: int) -> float:
    """
    Detecta a escala DPI da janela (Windows 10+).

    Args:
        hwnd: Handle da janela

    Returns:
        Escala DPI: 1.0 (100%), 1.25 (125%), 1.5 (150%), etc.
    """
    try:
        # Método 1: GetDpiForWindow (Windows 10 1607+)
        user32 = ctypes.windll.user32
        dpi = user32.GetDpiForWindow(hwnd)
        if dpi > 0:
            return dpi / 96.0  # 96 DPI = 100%
    except Exception:
        pass

    try:
        # Método 2: GetDeviceCaps (fallback para Windows mais antigos)
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        hdc = user32.GetDC(hwnd)
        dpi = gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX = 88
        user32.ReleaseDC(hwnd, hdc)
        if dpi > 0:
            return dpi / 96.0
    except Exception:
        pass

    # Fallback: assume 100% se não conseguir detectar
    return 1.0


def find_window_by_title(pattern: str) -> Optional[int]:
    """
    Encontra janela pelo título com suporte a wildcards.

    Suporta:
        - "Chrome*" - Começa com "Chrome"
        - "*YouTube*" - Contém "YouTube"
        - "*Notepad" - Termina com "Notepad"
        - "Exact Title" - Match exato (case-insensitive)

    Args:
        pattern: Padrão de busca com wildcards opcionais

    Returns:
        hwnd da janela ou None se não encontrada
    """
    windows = find_all_windows_by_title(pattern)
    return windows[0] if windows else None


def find_all_windows_by_title(pattern: str) -> List[int]:
    """
    Encontra TODAS as janelas que correspondem ao padrão.

    Suporta:
        - "Chrome*" - Começa com "Chrome"
        - "*YouTube*" - Contém "YouTube"
        - "*Notepad" - Termina com "Notepad"
        - "Exact Title" - Match exato (case-insensitive)

    Args:
        pattern: Padrão de busca com wildcards opcionais

    Returns:
        Lista de hwnds das janelas encontradas
    """
    pattern_lower = pattern.lower().replace("*", "")
    matching = []

    for hwnd, title in get_windows():
        title_lower = title.lower()
        matched = False

        if pattern.startswith("*") and pattern.endswith("*"):
            # *pattern* - contém
            matched = pattern_lower in title_lower
        elif pattern.startswith("*"):
            # *pattern - termina com
            matched = title_lower.endswith(pattern_lower)
        elif pattern.endswith("*"):
            # pattern* - começa com
            matched = title_lower.startswith(pattern_lower)
        elif title_lower == pattern.lower():
            # Match exato
            matched = True
        elif pattern.lower() in title_lower or title_lower in pattern.lower():
            # Match parcial (para títulos truncados)
            matched = True

        if matched:
            matching.append(hwnd)

    return matching


def get_windows_by_process(process_name: str, title_filter: Optional[str] = None) -> List[Tuple[int, str, str]]:
    """
    Encontra todas as janelas de um processo específico.

    Args:
        process_name: Nome do executável (ex: "Code.exe", "chrome.exe")
        title_filter: Filtro opcional no título (ex: "Chat")

    Returns:
        Lista de tuplas (hwnd, título, exe_path)
    """
    matching = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True

        title = win32gui.GetWindowText(hwnd)
        if not title or len(title) < 2:
            return True

        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            handle = win32api.OpenProcess(
                win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
                False, pid
            )
            exe_path = win32process.GetModuleFileNameEx(handle, 0)
            exe_name = exe_path.split("\\")[-1].lower()

            if process_name.lower() in exe_name:
                if title_filter is None or title_filter.lower() in title.lower():
                    matching.append((hwnd, title, exe_path))
        except Exception:
            pass
        return True

    win32gui.EnumWindows(callback, None)
    return matching


def find_window_by_process(
    process_name: str,
    title_filter: Optional[str] = None,
    index: int = 0
) -> Optional[int]:
    """
    Encontra UMA janela por processo.

    Args:
        process_name: Nome do executável (ex: "Code.exe")
        title_filter: Filtro opcional no título
        index: Qual janela retornar (0=primeira, 1=segunda, etc.)

    Returns:
        hwnd ou None
    """
    windows = get_windows_by_process(process_name, title_filter)
    if windows and index < len(windows):
        return windows[index][0]
    return None


def find_all_windows_by_process(
    process_name: str,
    title_filter: Optional[str] = None
) -> List[int]:
    """
    Encontra TODAS as janelas de um processo.

    Args:
        process_name: Nome do executável (ex: "Code.exe")
        title_filter: Filtro opcional no título

    Returns:
        Lista de hwnds das janelas encontradas
    """
    windows = get_windows_by_process(process_name, title_filter)
    return [hwnd for hwnd, _, _ in windows]


def get_available_processes() -> List[str]:
    """
    Retorna lista de processos únicos com janelas visíveis.

    Returns:
        Lista de nomes de executáveis ordenados
    """
    processes = set()

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and len(title) > 2:
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    handle = win32api.OpenProcess(
                        win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
                        False, pid
                    )
                    exe_path = win32process.GetModuleFileNameEx(handle, 0)
                    exe_name = exe_path.split("\\")[-1]
                    processes.add(exe_name)
                except Exception:
                    pass
        return True

    win32gui.EnumWindows(callback, None)
    return sorted(list(processes))


def get_window_rect(hwnd: int) -> Tuple[int, int, int, int]:
    """
    Obtém as coordenadas da janela.

    Args:
        hwnd: Handle da janela

    Returns:
        Tupla (left, top, right, bottom)
    """
    return win32gui.GetWindowRect(hwnd)


def is_window_visible(hwnd: int) -> bool:
    """
    Verifica se a janela está visível.

    Args:
        hwnd: Handle da janela

    Returns:
        True se visível
    """
    return win32gui.IsWindowVisible(hwnd)
