"""
Utilitarios para manipulacao de janelas macOS.
Funcoes para encontrar, listar e obter informacoes de janelas.

Usa Quartz (CoreGraphics) e AppKit via PyObjC.
"""

from typing import List, Optional, Tuple

import Quartz
from AppKit import NSScreen, NSWorkspace
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGNullWindowID,
    kCGWindowListOptionOnScreenOnly,
    kCGWindowListExcludeDesktopElements,
    kCGWindowListOptionAll,
)


# Cache para informacoes de janelas (atualizado em get_windows)
_window_cache: dict = {}


def _get_main_screen_height() -> float:
    """Retorna altura da tela principal para conversao de coordenadas."""
    main_screen = NSScreen.mainScreen()
    if main_screen:
        return main_screen.frame().size.height
    return 1080  # Fallback


def _convert_y_coordinate(y: float, height: float = 0) -> int:
    """
    Converte coordenada Y do sistema macOS (origem bottom-left)
    para sistema padrao (origem top-left).
    """
    screen_height = _get_main_screen_height()
    return int(screen_height - y - height)


def _get_all_windows_info(on_screen_only: bool = True, include_all_spaces: bool = True) -> list:
    """
    Obtem informacoes de todas as janelas via Quartz.

    Args:
        on_screen_only: Se True, retorna apenas janelas visiveis na tela
        include_all_spaces: Se True, inclui janelas de todos os Spaces (fullscreen)
                           Isso e necessario para capturar janelas em fullscreen no macOS

    Returns:
        Lista de dicionarios com informacoes das janelas
    """
    # Para incluir janelas fullscreen (outros Spaces), usamos kCGWindowListOptionAll
    # e filtramos manualmente, pois kCGWindowListOptionOnScreenOnly so retorna
    # janelas do Space atual
    if include_all_spaces:
        options = kCGWindowListOptionAll
    else:
        options = kCGWindowListOptionOnScreenOnly if on_screen_only else kCGWindowListOptionAll

    options |= kCGWindowListExcludeDesktopElements

    windows = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
    result = list(windows) if windows else []

    # Se queremos apenas janelas "on screen" mas incluindo outros Spaces,
    # filtramos janelas com dimensoes validas (>0) e layer normal (0)
    if on_screen_only and include_all_spaces:
        filtered = []
        for w in result:
            bounds = w.get('kCGWindowBounds', {})
            width = bounds.get('Width', 0)
            height = bounds.get('Height', 0)
            layer = w.get('kCGWindowLayer', 0)
            alpha = w.get('kCGWindowAlpha', 1.0)

            # Inclui se tem dimensoes validas, layer normal (0) e alpha > 0
            if width > 50 and height > 50 and layer == 0 and alpha > 0:
                filtered.append(w)
        return filtered

    return result


def is_window_minimized(window_id: int) -> bool:
    """
    Verifica se a janela esta minimizada.

    No macOS, janelas minimizadas nao aparecem na lista OnScreenOnly,
    entao verificamos se a janela existe mas nao esta na tela.

    Args:
        window_id: ID da janela (kCGWindowNumber)

    Returns:
        True se a janela esta minimizada
    """
    try:
        # Busca todas as janelas (incluindo minimizadas)
        all_windows = _get_all_windows_info(on_screen_only=False)
        on_screen_windows = _get_all_windows_info(on_screen_only=True)

        all_ids = {w.get('kCGWindowNumber', 0) for w in all_windows}
        on_screen_ids = {w.get('kCGWindowNumber', 0) for w in on_screen_windows}

        # Se existe em all mas nao em on_screen, esta minimizada
        if window_id in all_ids and window_id not in on_screen_ids:
            return True
        return False
    except Exception:
        return False


def get_windows(include_minimized: bool = True) -> List[Tuple[int, str]]:
    """
    Retorna lista de janelas visiveis.

    Args:
        include_minimized: Se True, inclui janelas minimizadas

    Returns:
        Lista de tuplas (window_id, titulo) ordenadas por titulo
    """
    global _window_cache
    windows = []
    _window_cache.clear()

    try:
        # Pega janelas na tela
        on_screen = _get_all_windows_info(on_screen_only=True)

        if include_minimized:
            # Tambem pega todas para incluir minimizadas
            all_windows = _get_all_windows_info(on_screen_only=False)
            on_screen_ids = {w.get('kCGWindowNumber', 0) for w in on_screen}

            # Combina: on_screen + minimizadas (que existem mas nao estao on_screen)
            combined = list(on_screen)
            for w in all_windows:
                wid = w.get('kCGWindowNumber', 0)
                if wid not in on_screen_ids:
                    combined.append(w)
            window_list = combined
        else:
            window_list = on_screen

        for window in window_list:
            window_id = window.get('kCGWindowNumber', 0)
            title = window.get('kCGWindowName', '') or ''
            owner = window.get('kCGWindowOwnerName', '') or ''

            # Filtra janelas sem titulo ou muito curto
            # Usa owner name se title estiver vazio
            display_title = title if title else owner
            if display_title and len(display_title) > 2:
                # Cache para lookup rapido
                _window_cache[window_id] = window
                windows.append((window_id, display_title))

        # Remove duplicatas mantendo primeira ocorrencia
        seen = set()
        unique_windows = []
        for wid, title in windows:
            if wid not in seen:
                seen.add(wid)
                unique_windows.append((wid, title))

        return sorted(unique_windows, key=lambda x: x[1].lower())

    except Exception as e:
        print(f"Erro ao listar janelas: {e}")
        return []


def get_window_title(window_id: int) -> str:
    """
    Retorna o titulo de uma janela.

    Args:
        window_id: ID da janela

    Returns:
        Titulo da janela ou string vazia se falhar
    """
    try:
        # Tenta do cache primeiro
        if window_id in _window_cache:
            window = _window_cache[window_id]
            title = window.get('kCGWindowName', '') or ''
            if not title:
                title = window.get('kCGWindowOwnerName', '') or ''
            return title

        # Busca na lista de janelas
        windows = _get_all_windows_info(on_screen_only=False)
        for window in windows:
            if window.get('kCGWindowNumber', 0) == window_id:
                title = window.get('kCGWindowName', '') or ''
                if not title:
                    title = window.get('kCGWindowOwnerName', '') or ''
                return title
        return ""
    except Exception:
        return ""


def get_window_dpi_scale(window_id: int) -> float:
    """
    Detecta a escala DPI da tela onde a janela esta.

    No macOS, usa backingScaleFactor (1.0 para telas normais, 2.0 para Retina).

    Args:
        window_id: ID da janela

    Returns:
        Escala DPI: 1.0 (normal) ou 2.0 (Retina)
    """
    try:
        # Obtem bounds da janela
        bounds = get_window_rect(window_id)
        if not bounds:
            return NSScreen.mainScreen().backingScaleFactor()

        window_x = bounds[0]
        window_y = bounds[1]

        # Encontra qual tela contem a janela
        for screen in NSScreen.screens():
            frame = screen.frame()
            # Converte coordenadas
            screen_x = int(frame.origin.x)
            screen_y = _convert_y_coordinate(frame.origin.y, frame.size.height)
            screen_w = int(frame.size.width)
            screen_h = int(frame.size.height)

            if (screen_x <= window_x < screen_x + screen_w and
                screen_y <= window_y < screen_y + screen_h):
                return screen.backingScaleFactor()

        # Fallback: usa tela principal
        return NSScreen.mainScreen().backingScaleFactor()

    except Exception:
        return 1.0


def find_window_by_title(pattern: str, include_minimized: bool = False) -> Optional[int]:
    """
    Encontra janela pelo titulo com suporte a wildcards.

    Suporta:
        - "Chrome*" - Comeca com "Chrome"
        - "*YouTube*" - Contem "YouTube"
        - "*Notepad" - Termina com "Notepad"
        - "Exact Title" - Match exato (case-insensitive)

    Args:
        pattern: Padrao de busca com wildcards opcionais
        include_minimized: Se True, inclui janelas minimizadas na busca

    Returns:
        window_id da janela ou None se nao encontrada
    """
    windows = find_all_windows_by_title(pattern, include_minimized=include_minimized)
    return windows[0] if windows else None


def find_all_windows_by_title(pattern: str, include_minimized: bool = False) -> List[int]:
    """
    Encontra TODAS as janelas que correspondem ao padrao.

    Suporta:
        - "Chrome*" - Comeca com "Chrome"
        - "*YouTube*" - Contem "YouTube"
        - "*Notepad" - Termina com "Notepad"
        - "Exact Title" - Match exato (case-insensitive)

    Args:
        pattern: Padrao de busca com wildcards opcionais
        include_minimized: Se True, inclui janelas minimizadas na busca.
                          Para automacao (cliques), use False (padrao).
                          Para listagem na UI, use True.

    Returns:
        Lista de window_ids das janelas encontradas
    """
    pattern_lower = pattern.lower().replace("*", "")
    matching = []

    for window_id, title in get_windows(include_minimized=include_minimized):
        title_lower = title.lower()
        matched = False

        if pattern.startswith("*") and pattern.endswith("*"):
            # *pattern* - contem
            matched = pattern_lower in title_lower
        elif pattern.startswith("*"):
            # *pattern - termina com
            matched = title_lower.endswith(pattern_lower)
        elif pattern.endswith("*"):
            # pattern* - comeca com
            matched = title_lower.startswith(pattern_lower)
        elif title_lower == pattern.lower():
            # Match exato
            matched = True
        elif pattern.lower() in title_lower or title_lower in pattern.lower():
            # Match parcial (para titulos truncados)
            matched = True

        if matched:
            matching.append(window_id)

    return matching


def get_windows_by_process(
    process_name: str,
    title_filter: Optional[str] = None,
    include_minimized: bool = False
) -> List[Tuple[int, str, str]]:
    """
    Encontra todas as janelas de um processo especifico.

    Args:
        process_name: Nome do app (ex: "Visual Studio Code", "Google Chrome", "Safari")
        title_filter: Filtro opcional no titulo (ex: "Chat")
        include_minimized: Se True, inclui janelas minimizadas

    Returns:
        Lista de tuplas (window_id, titulo, app_name)
    """
    matching = []
    process_lower = process_name.lower()

    try:
        if include_minimized:
            windows = _get_all_windows_info(on_screen_only=False, include_all_spaces=True)
        else:
            # Inclui todos os Spaces para suportar janelas fullscreen
            windows = _get_all_windows_info(on_screen_only=True, include_all_spaces=True)

        for window in windows:
            owner = window.get('kCGWindowOwnerName', '') or ''
            title = window.get('kCGWindowName', '') or ''
            window_id = window.get('kCGWindowNumber', 0)

            # Verifica se o processo corresponde
            if process_lower in owner.lower():
                display_title = title if title else owner

                if len(display_title) > 2:
                    # Aplica filtro de titulo se especificado
                    if title_filter is None or title_filter.lower() in display_title.lower():
                        matching.append((window_id, display_title, owner))

        # Remove duplicatas
        seen = set()
        unique = []
        for item in matching:
            if item[0] not in seen:
                seen.add(item[0])
                unique.append(item)

        return unique

    except Exception as e:
        print(f"Erro ao buscar janelas por processo: {e}")
        return []


def find_window_by_process(
    process_name: str,
    title_filter: Optional[str] = None,
    index: int = 0,
    include_minimized: bool = False
) -> Optional[int]:
    """
    Encontra UMA janela por processo.

    Args:
        process_name: Nome do app (ex: "Visual Studio Code")
        title_filter: Filtro opcional no titulo
        index: Qual janela retornar (0=primeira, 1=segunda, etc.)
        include_minimized: Se True, inclui janelas minimizadas

    Returns:
        window_id ou None
    """
    windows = get_windows_by_process(process_name, title_filter, include_minimized)
    if windows and index < len(windows):
        return windows[index][0]
    return None


def find_all_windows_by_process(
    process_name: str,
    title_filter: Optional[str] = None,
    include_minimized: bool = False
) -> List[int]:
    """
    Encontra TODAS as janelas de um processo.

    Args:
        process_name: Nome do app (ex: "Visual Studio Code")
        title_filter: Filtro opcional no titulo
        include_minimized: Se True, inclui janelas minimizadas.
                          Para automacao (cliques), use False (padrao).
                          Para listagem na UI, use True.

    Returns:
        Lista de window_ids das janelas encontradas
    """
    windows = get_windows_by_process(process_name, title_filter, include_minimized)
    return [window_id for window_id, _, _ in windows]


def get_available_processes() -> List[str]:
    """
    Retorna lista de processos unicos com janelas visiveis.

    Returns:
        Lista de nomes de apps ordenados
    """
    processes = set()

    try:
        windows = _get_all_windows_info(on_screen_only=True)

        for window in windows:
            owner = window.get('kCGWindowOwnerName', '') or ''
            title = window.get('kCGWindowName', '') or ''

            # Filtra janelas sem titulo significativo
            display_title = title if title else owner
            if owner and len(display_title) > 2:
                processes.add(owner)

        return sorted(list(processes))

    except Exception as e:
        print(f"Erro ao listar processos: {e}")
        return []


def get_window_rect(window_id: int) -> Optional[Tuple[int, int, int, int]]:
    """
    Obtem as coordenadas da janela.

    Args:
        window_id: ID da janela

    Returns:
        Tupla (left, top, right, bottom) ou None se nao encontrada
        Coordenadas convertidas para sistema top-left origin
    """
    try:
        # Tenta do cache primeiro
        window = _window_cache.get(window_id)

        if not window:
            # Busca na lista de janelas
            windows = _get_all_windows_info(on_screen_only=False)
            for w in windows:
                if w.get('kCGWindowNumber', 0) == window_id:
                    window = w
                    break

        if not window:
            return None

        bounds = window.get('kCGWindowBounds', {})
        x = int(bounds.get('X', 0))
        y = int(bounds.get('Y', 0))
        width = int(bounds.get('Width', 0))
        height = int(bounds.get('Height', 0))

        # macOS ja usa top-left origin para kCGWindowBounds
        # (diferente de NSWindow.frame que usa bottom-left)
        left = x
        top = y
        right = x + width
        bottom = y + height

        return (left, top, right, bottom)

    except Exception as e:
        print(f"Erro ao obter rect da janela: {e}")
        return None


def is_window_visible(window_id: int) -> bool:
    """
    Verifica se a janela esta visivel (incluindo fullscreen em outros Spaces).

    Args:
        window_id: ID da janela

    Returns:
        True se visivel (nao minimizada)
    """
    try:
        # Inclui janelas de todos os Spaces para suportar fullscreen
        all_windows = _get_all_windows_info(on_screen_only=True, include_all_spaces=True)
        visible_ids = {w.get('kCGWindowNumber', 0) for w in all_windows}
        return window_id in visible_ids
    except Exception:
        return False


def get_window_at_point(x: int, y: int) -> Optional[int]:
    """
    Encontra a janela na posicao especificada.

    Args:
        x: Coordenada X (screen coordinates, top-left origin)
        y: Coordenada Y (screen coordinates, top-left origin)

    Returns:
        window_id da janela na posicao ou None
    """
    try:
        windows = _get_all_windows_info(on_screen_only=True)

        # Ordena por layer (janelas mais na frente primeiro)
        # kCGWindowLayer: menor = mais na frente
        windows_sorted = sorted(windows, key=lambda w: w.get('kCGWindowLayer', 0))

        for window in windows_sorted:
            bounds = window.get('kCGWindowBounds', {})
            wx = int(bounds.get('X', 0))
            wy = int(bounds.get('Y', 0))
            ww = int(bounds.get('Width', 0))
            wh = int(bounds.get('Height', 0))

            if wx <= x < wx + ww and wy <= y < wy + wh:
                window_id = window.get('kCGWindowNumber', 0)
                # Ignora janelas do sistema (Dock, Menu Bar, etc)
                owner = window.get('kCGWindowOwnerName', '')
                if owner not in ['Window Server', 'Dock', 'SystemUIServer']:
                    return window_id

        return None

    except Exception as e:
        print(f"Erro ao buscar janela na posicao: {e}")
        return None


def get_process_at_point(x: int, y: int) -> str:
    """
    Obtem o nome do processo/app na posicao especificada.

    Args:
        x: Coordenada X
        y: Coordenada Y

    Returns:
        Nome do app ou string vazia
    """
    try:
        windows = _get_all_windows_info(on_screen_only=True)

        # Ordena por layer
        windows_sorted = sorted(windows, key=lambda w: w.get('kCGWindowLayer', 0))

        for window in windows_sorted:
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

        return ''

    except Exception:
        return ''
