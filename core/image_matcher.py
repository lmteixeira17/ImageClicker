"""
Funcoes para template matching e clique em imagens.
Usa OpenCV para deteccao e Quartz/CGEvent para cliques no macOS.
Suporta captura de janelas em background usando CGWindowListCreateImage.
"""

import time
from pathlib import Path
from typing import Callable, Optional, Tuple

import cv2
import numpy as np

from Quartz import (
    CGWindowListCreateImage,
    CGRectNull,
    kCGWindowListOptionIncludingWindow,
    kCGWindowImageBoundsIgnoreFraming,
    kCGWindowImageDefault,
    CGImageGetWidth,
    CGImageGetHeight,
    CGImageGetBytesPerRow,
    CGImageGetDataProvider,
    CGDataProviderCopyData,
    CGEventCreateMouseEvent,
    CGEventPost,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGEventRightMouseDown,
    kCGEventRightMouseUp,
    kCGHIDEventTap,
    kCGMouseButtonLeft,
    kCGMouseButtonRight,
    CGEventSetIntegerValueField,
    kCGMouseEventClickState,
    CGEventGetLocation,
    CGWarpMouseCursorPosition,
)
from Quartz.CoreGraphics import CGPointMake

from .window_utils import get_window_dpi_scale, get_window_rect, is_window_visible

# Threshold minimo para considerar um match valido (85%)
MATCH_THRESHOLD = 0.85


def get_template_dpi(template_path: Path) -> float:
    """Le o DPI de captura dos metadados do template PNG.

    O DPI e salvo durante a captura para permitir escalonamento
    correto quando a janela alvo tem DPI diferente.

    Args:
        template_path: Caminho para o arquivo PNG do template

    Returns:
        Escala DPI (1.0 = 96 DPI/100%, 1.25 = 120 DPI/125%, etc.)
        Retorna 1.0 se nao encontrar metadados (assume 100%)
    """
    try:
        from PIL import Image

        with Image.open(template_path) as img:
            # Primeiro tenta metadado customizado ImageClicker_DPI
            if hasattr(img, 'text') and 'ImageClicker_DPI' in img.text:
                dpi_value = int(img.text['ImageClicker_DPI'])
                return dpi_value / 96.0

            # Fallback: usa DPI do campo pHYs/dpi
            if hasattr(img, 'info') and 'dpi' in img.info:
                dpi_x = img.info['dpi'][0]
                if dpi_x > 0:
                    return dpi_x / 96.0

    except Exception:
        pass

    # Assume 100% DPI se nao conseguir ler (templates antigos)
    return 1.0


def _is_window_valid_for_capture(window_id: int) -> bool:
    """
    Verifica se a janela esta em um estado valido para captura.

    Args:
        window_id: ID da janela

    Returns:
        True se a janela pode ser capturada
    """
    try:
        # Verifica se esta visivel
        if not is_window_visible(window_id):
            return False

        # Verifica dimensoes validas
        rect = get_window_rect(window_id)
        if not rect:
            return False

        left, top, right, bottom = rect
        if right <= left or bottom <= top:
            return False

        return True
    except Exception:
        return False


def _cgimage_to_numpy(cg_image) -> Optional[np.ndarray]:
    """
    Converte CGImage para numpy array (BGR).

    Args:
        cg_image: CGImage do Quartz

    Returns:
        numpy array BGR ou None se falhar
    """
    if cg_image is None:
        return None

    try:
        width = CGImageGetWidth(cg_image)
        height = CGImageGetHeight(cg_image)
        bytes_per_row = CGImageGetBytesPerRow(cg_image)

        # Obtem dados do provider
        data_provider = CGImageGetDataProvider(cg_image)
        data = CGDataProviderCopyData(data_provider)

        # Converte para numpy
        img = np.frombuffer(data, dtype=np.uint8)

        # CGImage retorna RGBA ou BGRA dependendo da fonte
        # bytes_per_row pode incluir padding
        if bytes_per_row == width * 4:
            img = img.reshape((height, width, 4))
        else:
            # Com padding, precisamos processar linha por linha
            img_reshaped = np.zeros((height, width, 4), dtype=np.uint8)
            for row in range(height):
                start = row * bytes_per_row
                end = start + width * 4
                img_reshaped[row] = np.frombuffer(data[start:end], dtype=np.uint8).reshape((width, 4))
            img = img_reshaped

        # Converte RGBA para BGR (OpenCV format)
        # macOS CGImage usa BGRA por padrao
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        return img_bgr

    except Exception as e:
        print(f"Erro ao converter CGImage: {e}")
        return None


def capture_window(window_id: int, restore_if_minimized: bool = False) -> Optional[np.ndarray]:
    """
    Captura o conteudo de uma janela usando CGWindowListCreateImage.
    Funciona mesmo quando a janela esta atras de outras ou parcialmente coberta.

    IMPORTANTE: Janelas minimizadas sao ignoradas silenciosamente (retorna None).

    Args:
        window_id: ID da janela (kCGWindowNumber)
        restore_if_minimized: IGNORADO - mantido para compatibilidade de API

    Returns:
        numpy array BGR da imagem ou None se janela minimizada/invalida
    """
    try:
        # Verifica se a janela esta em estado valido para captura
        if not _is_window_valid_for_capture(window_id):
            return None

        # Captura a janela usando CGWindowListCreateImage
        # CGRectNull captura a janela inteira
        # kCGWindowListOptionIncludingWindow inclui apenas a janela especificada
        # kCGWindowImageBoundsIgnoreFraming ignora sombras e decoracoes
        cg_image = CGWindowListCreateImage(
            CGRectNull,
            kCGWindowListOptionIncludingWindow,
            window_id,
            kCGWindowImageBoundsIgnoreFraming | kCGWindowImageDefault
        )

        if cg_image is None:
            return None

        # Converte para numpy BGR
        return _cgimage_to_numpy(cg_image)

    except Exception as e:
        print(f"Erro ao capturar janela: {e}")
        return None


def _perform_ghost_click(window_id: int, x: int, y: int, action: str):
    """
    Executa clique via CGEvent.

    No macOS, CGEvent move o cursor. Para minimizar o impacto:
    1. Salva posicao atual do cursor
    2. Move para posicao alvo
    3. Executa clique
    4. Restaura posicao do cursor

    Args:
        window_id: ID da janela alvo
        x: Coordenada X relativa a janela
        y: Coordenada Y relativa a janela
        action: "click", "double_click" ou "right_click"
    """
    try:
        # Obtem coordenadas absolutas da janela
        rect = get_window_rect(window_id)
        if not rect:
            return

        # Converte coordenadas relativas para absolutas
        abs_x = rect[0] + x
        abs_y = rect[1] + y

        # Salva posicao atual do cursor
        # (infelizmente CGEvent sempre move o cursor)
        # Comentado por enquanto - pode causar efeitos indesejados
        # original_pos = CGEventGetLocation(CGEventCreate(None))

        point = CGPointMake(float(abs_x), float(abs_y))

        if action == "double_click":
            # Primeiro clique
            down1 = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, point, kCGMouseButtonLeft)
            up1 = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, point, kCGMouseButtonLeft)
            CGEventPost(kCGHIDEventTap, down1)
            time.sleep(0.01)
            CGEventPost(kCGHIDEventTap, up1)

            time.sleep(0.05)

            # Segundo clique (com click state = 2 para double click)
            down2 = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, point, kCGMouseButtonLeft)
            up2 = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, point, kCGMouseButtonLeft)
            CGEventSetIntegerValueField(down2, kCGMouseEventClickState, 2)
            CGEventSetIntegerValueField(up2, kCGMouseEventClickState, 2)
            CGEventPost(kCGHIDEventTap, down2)
            time.sleep(0.01)
            CGEventPost(kCGHIDEventTap, up2)

        elif action == "right_click":
            down = CGEventCreateMouseEvent(None, kCGEventRightMouseDown, point, kCGMouseButtonRight)
            up = CGEventCreateMouseEvent(None, kCGEventRightMouseUp, point, kCGMouseButtonRight)
            CGEventPost(kCGHIDEventTap, down)
            time.sleep(0.01)
            CGEventPost(kCGHIDEventTap, up)

        else:  # click
            down = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, point, kCGMouseButtonLeft)
            up = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, point, kCGMouseButtonLeft)
            CGEventPost(kCGHIDEventTap, down)
            time.sleep(0.01)
            CGEventPost(kCGHIDEventTap, up)

        # Pequeno delay apos o clique
        time.sleep(0.05)

    except Exception as e:
        print(f"Erro ao executar clique: {e}")


def find_and_click(
    window_id: int,
    template_path: Path,
    action: str = "click",
    debug_callback: Optional[Callable[[str], None]] = None,
    threshold: Optional[float] = None
) -> Tuple[bool, str, float]:
    """
    Encontra template na janela e executa clique.

    Args:
        window_id: ID da janela alvo
        template_path: Caminho para o arquivo de imagem do template
        action: Tipo de clique - "click", "double_click", "right_click"
        debug_callback: Funcao opcional para debug logging
        threshold: Threshold de deteccao (0.0 a 1.0). Se None, usa MATCH_THRESHOLD

    Returns:
        Tupla (sucesso, mensagem, percentual_match)
    """
    def debug(msg: str):
        if debug_callback:
            debug_callback(msg)

    try:
        # Obtem coordenadas da janela
        rect = get_window_rect(window_id)
        if not rect:
            return False, 'Janela nao encontrada', 0.0
        debug(f"  Window rect: {rect}")

        # Captura janela usando CGWindowListCreateImage
        screenshot_bgr = capture_window(window_id)

        if screenshot_bgr is None:
            return False, 'Falha ao capturar janela', 0.0

        debug(f"  Screenshot shape: {screenshot_bgr.shape}")
        screenshot_gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

        # Carrega template
        template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
        if template is None:
            return False, 'Template nao encontrado', 0.0
        debug(f"  Template shape original: {template.shape}, path: {template_path.name}")

        # Calcula escala necessaria baseado no DPI do template vs DPI da janela
        template_dpi = get_template_dpi(template_path)
        window_dpi = get_window_dpi_scale(window_id)
        dpi_scale = window_dpi / template_dpi  # Escala relativa
        debug(f"  Template DPI: {template_dpi:.2f} ({int(template_dpi * 100)}%), Window DPI: {window_dpi:.2f} ({int(window_dpi * 100)}%), Scale: {dpi_scale:.2f}")

        if abs(dpi_scale - 1.0) > 0.05:  # Diferenca significativa (>5%)
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
            # Coordenadas em pixels fisicos (da imagem capturada)
            pixel_x = max_loc[0] + w // 2
            pixel_y = max_loc[1] + h // 2

            # Converte para pontos logicos (CGEvent espera pontos, nao pixels)
            # A imagem capturada esta em pixels fisicos (Retina = 2x)
            # As coordenadas da janela (kCGWindowBounds) estao em pontos logicos
            window_rect = get_window_rect(window_id)
            if window_rect:
                win_width_points = window_rect[2] - window_rect[0]
                win_height_points = window_rect[3] - window_rect[1]
                img_height, img_width = screenshot_gray.shape

                # Fator de escala: pixels fisicos -> pontos logicos
                scale_x = win_width_points / img_width if img_width > 0 else 1.0
                scale_y = win_height_points / img_height if img_height > 0 else 1.0

                rel_x = int(pixel_x * scale_x)
                rel_y = int(pixel_y * scale_y)
                debug(f"  Click: pixel({pixel_x}, {pixel_y}) -> points({rel_x}, {rel_y}), scale=({scale_x:.2f}, {scale_y:.2f})")
            else:
                rel_x = pixel_x
                rel_y = pixel_y

            # Executa clique
            _perform_ghost_click(window_id, rel_x, rel_y, action)

            return True, f'{action} OK', max_val

        return False, 'Nao encontrado', max_val

    except Exception as e:
        return False, str(e), 0.0


def check_template_visible(
    window_id: int,
    template_path: Path,
    threshold: Optional[float] = None
) -> Tuple[bool, float]:
    """
    Verifica se um template esta visivel na janela SEM clicar.

    Args:
        window_id: ID da janela alvo
        template_path: Caminho para o arquivo de imagem do template
        threshold: Threshold de deteccao (0.0 a 1.0). Se None, usa MATCH_THRESHOLD

    Returns:
        Tupla (visivel, percentual_match)
    """
    try:
        # Captura janela
        screenshot_bgr = capture_window(window_id)
        if screenshot_bgr is None:
            return False, 0.0

        screenshot_gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

        template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
        if template is None:
            return False, 0.0

        # Calcula escala baseado no DPI do template vs DPI da janela
        template_dpi = get_template_dpi(template_path)
        window_dpi = get_window_dpi_scale(window_id)
        dpi_scale = window_dpi / template_dpi

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
    window_id: int,
    template_path: Path
) -> Optional[Tuple[int, int, int, int]]:
    """
    Encontra a localizacao do template na janela.

    Args:
        window_id: ID da janela alvo
        template_path: Caminho para o arquivo de imagem do template

    Returns:
        Tupla (x, y, width, height) da posicao do template ou None se nao encontrado
        Coordenadas sao absolutas (screen coordinates)
    """
    try:
        rect = get_window_rect(window_id)
        if not rect:
            return None

        screenshot_bgr = capture_window(window_id)
        if screenshot_bgr is None:
            return None
        screenshot_gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

        template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
        if template is None:
            return None

        # Calcula escala baseado no DPI do template vs DPI da janela
        template_dpi = get_template_dpi(template_path)
        window_dpi = get_window_dpi_scale(window_id)
        dpi_scale = window_dpi / template_dpi

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
