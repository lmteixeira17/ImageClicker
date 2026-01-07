"""
Funções para template matching e clique em imagens.
Usa OpenCV para detecção e pywin32 para cliques "fantasma" (sem roubar foco).
Suporta captura de janelas em background usando PrintWindow API.
"""

import ctypes
import time
from pathlib import Path
from typing import Callable, Optional, Tuple

import cv2
import numpy as np
import win32api
import win32con
import win32gui
import win32ui

from .window_utils import get_window_dpi_scale

# Threshold mínimo para considerar um match válido (85%)
MATCH_THRESHOLD = 0.85

# PrintWindow flags
PW_CLIENTONLY = 1
PW_RENDERFULLCONTENT = 2  # Windows 8.1+, captura conteúdo mesmo em background


def capture_window(hwnd: int) -> Optional[np.ndarray]:
    """
    Captura o conteúdo de uma janela usando PrintWindow API.
    Funciona mesmo quando a janela está atrás de outras ou parcialmente coberta.

    Args:
        hwnd: Handle da janela

    Returns:
        numpy array BGR da imagem ou None se falhar
    """
    try:
        # Obtém dimensões da janela
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        if width <= 0 or height <= 0:
            return None

        # Cria DC e bitmap compatíveis
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)

        # PrintWindow com flag para capturar conteúdo em background
        # Flag 2 (PW_RENDERFULLCONTENT) funciona melhor para janelas modernas
        result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), PW_RENDERFULLCONTENT)

        if result == 0:
            # Fallback: tenta sem flag (para janelas mais antigas)
            result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 0)

        # Converte bitmap para numpy array
        bmp_info = bitmap.GetInfo()
        bmp_bits = bitmap.GetBitmapBits(True)

        img = np.frombuffer(bmp_bits, dtype=np.uint8)
        img = img.reshape((bmp_info['bmHeight'], bmp_info['bmWidth'], 4))

        # Limpa recursos
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)

        # Converte BGRA para BGR (remove canal alpha)
        img_bgr = img[:, :, :3]

        return img_bgr

    except Exception as e:
        return None


# Constantes para mensagens de mouse
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002


def find_and_click(
    hwnd: int,
    template_path: Path,
    action: str = "click",
    debug_callback: Optional[Callable[[str], None]] = None,
    threshold: Optional[float] = None
) -> Tuple[bool, str, float]:
    """
    Encontra template na janela e executa clique.

    Args:
        hwnd: Handle da janela alvo
        template_path: Caminho para o arquivo de imagem do template
        action: Tipo de clique - "click", "double_click", "right_click"
        debug_callback: Função opcional para debug logging
        threshold: Threshold de detecção (0.0 a 1.0). Se None, usa MATCH_THRESHOLD

    Returns:
        Tupla (sucesso, mensagem, percentual_match)
    """
    def debug(msg: str):
        if debug_callback:
            debug_callback(msg)

    try:
        # Obtém coordenadas da janela
        rect = win32gui.GetWindowRect(hwnd)
        debug(f"  Window rect: {rect}")

        # Captura janela usando PrintWindow (funciona em background)
        screenshot_bgr = capture_window(hwnd)

        if screenshot_bgr is None:
            return False, 'Falha ao capturar janela', 0.0

        debug(f"  Screenshot shape: {screenshot_bgr.shape}")
        screenshot_gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

        # Carrega template
        template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
        if template is None:
            return False, 'Template não encontrado', 0.0
        debug(f"  Template shape original: {template.shape}, path: {template_path.name}")

        # Detecta DPI e escala template se necessário
        dpi_scale = get_window_dpi_scale(hwnd)
        debug(f"  DPI scale detectado: {dpi_scale:.2f} ({int(dpi_scale * 100)}%)")

        if abs(dpi_scale - 1.0) > 0.05:  # Diferença significativa (>5%)
            original_h, original_w = template.shape
            new_w = int(original_w * dpi_scale)
            new_h = int(original_h * dpi_scale)
            template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)
            debug(f"  Template escalado: {original_w}x{original_h} -> {new_w}x{new_h}")

        # Verifica se template cabe na screenshot
        if template.shape[0] > screenshot_gray.shape[0] or template.shape[1] > screenshot_gray.shape[1]:
            return False, f'Template maior que janela ({template.shape} > {screenshot_gray.shape})', 0.0

        # Template matching
        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        # Usa threshold passado ou o global
        match_threshold = threshold if threshold is not None else MATCH_THRESHOLD

        if max_val >= match_threshold:
            h, w = template.shape
            # Coordenadas relativas à janela (para clique fantasma)
            rel_x = max_loc[0] + w // 2
            rel_y = max_loc[1] + h // 2

            # Clique fantasma - envia mensagem direto para a janela sem mover mouse
            _perform_ghost_click(hwnd, rel_x, rel_y, action)

            return True, f'{action} OK', max_val

        return False, 'Não encontrado', max_val

    except Exception as e:
        return False, str(e), 0.0


def _make_lparam(x: int, y: int) -> int:
    """Cria lParam para mensagens de mouse (coordenadas empacotadas)."""
    return (y << 16) | (x & 0xFFFF)


def _get_child_at_point(hwnd: int, x: int, y: int) -> tuple[int, int, int]:
    """
    Encontra o controle filho na posição especificada.

    Args:
        hwnd: Handle da janela pai
        x: Coordenada X relativa à janela pai
        y: Coordenada Y relativa à janela pai

    Returns:
        Tupla (child_hwnd, child_x, child_y) onde child_x/y são coordenadas relativas ao filho
    """
    # Converte para coordenadas de tela
    rect = win32gui.GetWindowRect(hwnd)
    screen_x = rect[0] + x
    screen_y = rect[1] + y

    # Encontra a janela/controle mais profundo naquele ponto
    child = win32gui.WindowFromPoint((screen_x, screen_y))

    if child and child != hwnd:
        # Converte coordenadas para serem relativas ao filho
        child_rect = win32gui.GetWindowRect(child)
        child_x = screen_x - child_rect[0]
        child_y = screen_y - child_rect[1]
        return child, child_x, child_y

    # Se não encontrou filho, usa a janela principal
    return hwnd, x, y


def _perform_ghost_click(hwnd: int, x: int, y: int, action: str):
    """
    Executa clique "fantasma" - envia mensagem direto para a janela sem mover mouse.
    Não rouba foco nem altera a posição do cursor.

    Args:
        hwnd: Handle da janela alvo
        x: Coordenada X relativa à janela
        y: Coordenada Y relativa à janela
        action: "click", "double_click" ou "right_click"
    """
    # Envia direto para a janela principal para evitar roubo de foco
    # Não usamos _get_child_at_point pois WindowFromPoint pode ativar janelas
    lparam = _make_lparam(x, y)

    if action == "double_click":
        # Double click usa mensagem específica WM_LBUTTONDBLCLK
        win32gui.PostMessage(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        win32gui.PostMessage(hwnd, WM_LBUTTONUP, 0, lparam)
        time.sleep(0.01)
        win32gui.PostMessage(hwnd, WM_LBUTTONDBLCLK, MK_LBUTTON, lparam)
        win32gui.PostMessage(hwnd, WM_LBUTTONUP, 0, lparam)
    elif action == "right_click":
        win32gui.PostMessage(hwnd, WM_RBUTTONDOWN, MK_RBUTTON, lparam)
        time.sleep(0.01)
        win32gui.PostMessage(hwnd, WM_RBUTTONUP, 0, lparam)
    else:  # click
        win32gui.PostMessage(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        time.sleep(0.01)
        win32gui.PostMessage(hwnd, WM_LBUTTONUP, 0, lparam)


def check_template_visible(
    hwnd: int,
    template_path: Path,
    threshold: Optional[float] = None
) -> Tuple[bool, float]:
    """
    Verifica se um template está visível na janela SEM clicar.

    Args:
        hwnd: Handle da janela alvo
        template_path: Caminho para o arquivo de imagem do template
        threshold: Threshold de detecção (0.0 a 1.0). Se None, usa MATCH_THRESHOLD

    Returns:
        Tupla (visível, percentual_match)
    """
    try:
        # Captura janela usando PrintWindow (funciona em background)
        screenshot_bgr = capture_window(hwnd)
        if screenshot_bgr is None:
            return False, 0.0

        screenshot_gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

        template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
        if template is None:
            return False, 0.0

        # Detecta DPI e escala template se necessário
        dpi_scale = get_window_dpi_scale(hwnd)
        if abs(dpi_scale - 1.0) > 0.05:
            new_w = int(template.shape[1] * dpi_scale)
            new_h = int(template.shape[0] * dpi_scale)
            template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)

        if template.shape[0] > screenshot_gray.shape[0] or template.shape[1] > screenshot_gray.shape[1]:
            return False, 0.0

        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        # Usa threshold passado ou o global
        match_threshold = threshold if threshold is not None else MATCH_THRESHOLD

        return max_val >= match_threshold, max_val

    except Exception:
        return False, 0.0


def find_template_location(
    hwnd: int,
    template_path: Path
) -> Optional[Tuple[int, int, int, int]]:
    """
    Encontra a localização do template na janela.

    Args:
        hwnd: Handle da janela alvo
        template_path: Caminho para o arquivo de imagem do template

    Returns:
        Tupla (x, y, width, height) da posição do template ou None se não encontrado
    """
    try:
        rect = win32gui.GetWindowRect(hwnd)
        screenshot_bgr = capture_window(hwnd)
        if screenshot_bgr is None:
            return None
        screenshot_gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

        template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
        if template is None:
            return None

        dpi_scale = get_window_dpi_scale(hwnd)
        if abs(dpi_scale - 1.0) > 0.05:
            new_w = int(template.shape[1] * dpi_scale)
            new_h = int(template.shape[0] * dpi_scale)
            template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)

        if template.shape[0] > screenshot_gray.shape[0] or template.shape[1] > screenshot_gray.shape[1]:
            return None

        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= MATCH_THRESHOLD:
            h, w = template.shape
            return (rect[0] + max_loc[0], rect[1] + max_loc[1], w, h)

        return None

    except Exception:
        return None
