"""
🖱️ Image-Based Click Automation Tool
=====================================

Este script permite automatizar cliques baseados em reconhecimento de imagem.
Suporta execução em janelas específicas (multi-window) e scripts paralelos.

Uso:
    python iclick.py capture <nome>              # Captura uma região da tela
    python iclick.py click <nome>                # Clica onde encontrar a imagem
    python iclick.py click <nome> --window "App" # Clica na janela específica
    python iclick.py wait <nome>                 # Espera a imagem aparecer e clica
    python iclick.py run <script>                # Executa um script de automação
    python iclick.py tasks                       # Executa tasks.json (multi-window)
    python iclick.py list                        # Lista recursos disponíveis

Exemplos:
    python iclick.py capture botao_salvar
    python iclick.py click botao_salvar --window "Chrome*"
    python iclick.py run deploy_sequence
    python iclick.py tasks
"""

import pyautogui
import time
import sys
import os
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

# Tenta importar win32gui para suporte a janelas específicas
try:
    import win32gui
    import win32con
    import win32api
    import cv2
    import numpy as np
    from PIL import ImageGrab
    import ctypes
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("⚠️  win32gui/cv2 não disponível. Modo janela específica desativado.")

# Configurações
BASE_DIR = Path(r"C:\Users\catar\OneDrive\3. Projetos\ProjetosPessoais\ImageClicker")
IMAGES_DIR = BASE_DIR / "images"
SCRIPTS_DIR = BASE_DIR / "scripts"
TASKS_FILE = BASE_DIR / "tasks.json"
CONFIDENCE = 0.9  # 90% de precisão no reconhecimento
TIMEOUT = 30  # Segundos para esperar uma imagem

# Segurança: pause antes de cada ação
pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True  # Mova o mouse para o canto superior esquerdo para parar

def ensure_dirs():
    """Garante que os diretórios existam"""
    IMAGES_DIR.mkdir(exist_ok=True)
    SCRIPTS_DIR.mkdir(exist_ok=True)

# ============== Window-specific functions (require win32gui) ==============

def get_windows():
    """Retorna lista de janelas visíveis (hwnd, título)"""
    if not HAS_WIN32:
        return []
    windows = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and len(title) > 2:
                windows.append((hwnd, title))
    win32gui.EnumWindows(cb, None)
    return sorted(windows, key=lambda x: x[1].lower())

def get_window_dpi_scale(hwnd: int) -> float:
    """
    Detecta a escala DPI da janela (Windows 10+).
    Retorna: 1.0 (100%), 1.25 (125%), 1.5 (150%), etc.
    """
    if not HAS_WIN32:
        return 1.0

    try:
        # Método 1: GetDpiForWindow (Windows 10 1607+)
        user32 = ctypes.windll.user32
        dpi = user32.GetDpiForWindow(hwnd)
        if dpi > 0:
            scale = dpi / 96.0  # 96 DPI = 100%
            return scale
    except:
        pass

    try:
        # Método 2: GetDeviceCaps (fallback para Windows mais antigos)
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        hdc = user32.GetDC(hwnd)
        dpi = gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX = 88
        user32.ReleaseDC(hwnd, hdc)
        if dpi > 0:
            scale = dpi / 96.0
            return scale
    except:
        pass

    # Fallback: assume 100% se não conseguir detectar
    return 1.0

def find_window_by_title(pattern: str):
    """Encontra janela pelo título (suporta wildcards simples com *)"""
    if not HAS_WIN32:
        return None
    pattern_lower = pattern.lower().replace("*", "")
    for hwnd, title in get_windows():
        if pattern.startswith("*") and pattern.endswith("*"):
            if pattern_lower in title.lower():
                return hwnd
        elif pattern.startswith("*"):
            if title.lower().endswith(pattern_lower):
                return hwnd
        elif pattern.endswith("*"):
            if title.lower().startswith(pattern_lower):
                return hwnd
        elif title.lower() == pattern.lower():
            return hwnd
        elif pattern.lower() in title.lower():
            return hwnd
    return None

def find_and_click_window(hwnd: int, template_path: Path, action: str = "click"):
    """
    Encontra template em janela específica e clica (usando OpenCV).
    Retorna: (sucesso, mensagem, match_percentage)
    """
    if not HAS_WIN32:
        return False, "win32gui não disponível", 0.0
    
    try:
        rect = win32gui.GetWindowRect(hwnd)
        # OTIMIZAÇÃO: Removido SetForegroundWindow - testa se funciona sem trazer janela para frente
        # try:
        #     win32gui.SetForegroundWindow(hwnd)
        # except:
        #     pass
        # time.sleep(0.1)

        screenshot = ImageGrab.grab(rect)
        screenshot_np = np.array(screenshot)
        screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)

        template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
        if template is None:
            return False, 'Template não encontrado', 0.0

        # Detecta DPI e escala template se necessário
        dpi_scale = get_window_dpi_scale(hwnd)
        if abs(dpi_scale - 1.0) > 0.05:  # Diferença significativa (>5%)
            original_h, original_w = template.shape
            new_w = int(original_w * dpi_scale)
            new_h = int(original_h * dpi_scale)
            template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)
            print(f"  Template escalado: {original_w}x{original_h} → {new_w}x{new_h} (DPI: {int(dpi_scale * 100)}%)")

        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= 0.85:
            h, w = template.shape
            cx = rect[0] + max_loc[0] + w // 2
            cy = rect[1] + max_loc[1] + h // 2

            old_pos = win32api.GetCursorPos()
            win32api.SetCursorPos((cx, cy))

            # OTIMIZAÇÃO: Delays reduzidos de 50ms → 10ms
            if action == "double_click":
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
                time.sleep(0.01)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            elif action == "right_click":
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
                time.sleep(0.01)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
            else:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                time.sleep(0.01)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

            win32api.SetCursorPos(old_pos)
            return True, f'{action} OK', max_val
        
        return False, 'Não encontrado', max_val
    except Exception as e:
        return False, str(e), 0.0

# ============== Original pyautogui functions ==============

def capture_region(name: str):
    """
    Captura uma região da tela para usar como referência de clique.
    Após executar, você tem 3 segundos para posicionar o mouse no canto superior esquerdo
    da região, depois mais 3 segundos para o canto inferior direito.
    """
    print(f"📸 Capturando região: {name}")
    print("   Posicione o mouse no CANTO SUPERIOR ESQUERDO da região...")
    print("   Aguardando 3 segundos...")
    time.sleep(3)
    
    start_x, start_y = pyautogui.position()
    print(f"   ✓ Ponto inicial: ({start_x}, {start_y})")
    
    print("   Agora posicione no CANTO INFERIOR DIREITO...")
    print("   Aguardando 3 segundos...")
    time.sleep(3)
    
    end_x, end_y = pyautogui.position()
    print(f"   ✓ Ponto final: ({end_x}, {end_y})")
    
    # Captura a região
    width = abs(end_x - start_x)
    height = abs(end_y - start_y)
    x = min(start_x, end_x)
    y = min(start_y, end_y)
    
    if width < 5 or height < 5:
        print("   ❌ Região muito pequena! Tente novamente.")
        return
    
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    image_path = IMAGES_DIR / f"{name}.png"
    screenshot.save(image_path)
    
    print(f"   ✅ Imagem salva: {image_path}")
    print(f"   📐 Dimensões: {width}x{height}")

def find_image(name: str, timeout: float = 0):
    """Encontra uma imagem na tela"""
    image_path = IMAGES_DIR / f"{name}.png"
    
    if not image_path.exists():
        print(f"   ❌ Imagem não encontrada: {image_path}")
        return None
    
    start_time = time.time()
    while True:
        try:
            location = pyautogui.locateOnScreen(str(image_path), confidence=CONFIDENCE)
            if location:
                return location
        except pyautogui.ImageNotFoundException:
            pass
        
        if timeout <= 0 or (time.time() - start_time) >= timeout:
            break
        
        time.sleep(0.5)
    
    return None

def click_image(name: str, wait: bool = False):
    """Clica em uma imagem na tela"""
    print(f"🔍 Procurando: {name}")
    
    timeout = TIMEOUT if wait else 0
    location = find_image(name, timeout)
    
    if location:
        center = pyautogui.center(location)
        print(f"   ✓ Encontrado em: ({center.x}, {center.y})")
        pyautogui.click(center)
        print(f"   ✅ Clique realizado!")
        return True
    else:
        print(f"   ❌ Imagem '{name}' não encontrada na tela")
        return False

def double_click_image(name: str, wait: bool = False):
    """Duplo clique em uma imagem"""
    print(f"🔍 Procurando (double-click): {name}")
    
    timeout = TIMEOUT if wait else 0
    location = find_image(name, timeout)
    
    if location:
        center = pyautogui.center(location)
        pyautogui.doubleClick(center)
        print(f"   ✅ Duplo clique realizado!")
        return True
    return False

def right_click_image(name: str, wait: bool = False):
    """Clique direito em uma imagem"""
    print(f"🔍 Procurando (right-click): {name}")
    
    timeout = TIMEOUT if wait else 0
    location = find_image(name, timeout)
    
    if location:
        center = pyautogui.center(location)
        pyautogui.rightClick(center)
        print(f"   ✅ Clique direito realizado!")
        return True
    return False

def type_text(text: str, interval: float = 0.05):
    """Digita um texto"""
    print(f"⌨️  Digitando: {text[:30]}...")
    pyautogui.typewrite(text, interval=interval)
    print("   ✅ Texto digitado!")

def press_key(key: str):
    """Pressiona uma tecla"""
    print(f"⌨️  Pressionando: {key}")
    pyautogui.press(key)

def hotkey(*keys):
    """Pressiona uma combinação de teclas"""
    print(f"⌨️  Hotkey: {'+'.join(keys)}")
    pyautogui.hotkey(*keys)

def wait_seconds(seconds: float):
    """Aguarda N segundos"""
    print(f"⏳ Aguardando {seconds} segundos...")
    time.sleep(seconds)

def run_script(script_name: str):
    """
    Executa um script de automação (arquivo JSON com sequência de ações)
    """
    script_path = SCRIPTS_DIR / f"{script_name}.json"
    
    if not script_path.exists():
        print(f"❌ Script não encontrado: {script_path}")
        print("\n📝 Criando script de exemplo...")
        create_example_script()
        return
    
    with open(script_path, 'r', encoding='utf-8') as f:
        script = json.load(f)
    
    print(f"🚀 Executando script: {script_name}")
    print(f"   Descrição: {script.get('description', 'Sem descrição')}")
    print(f"   Ações: {len(script.get('actions', []))}")
    print("-" * 50)
    
    for i, action in enumerate(script.get('actions', []), 1):
        action_type = action.get('type')
        print(f"\n[{i}/{len(script['actions'])}] {action_type}")
        
        if action_type == 'click':
            if not click_image(action['image'], action.get('wait', False)):
                if action.get('required', True):
                    print("   ⚠️  Ação obrigatória falhou! Abortando...")
                    return False
        
        elif action_type == 'double_click':
            double_click_image(action['image'], action.get('wait', False))
        
        elif action_type == 'right_click':
            right_click_image(action['image'], action.get('wait', False))
        
        elif action_type == 'type':
            type_text(action['text'], action.get('interval', 0.05))
        
        elif action_type == 'press':
            press_key(action['key'])
        
        elif action_type == 'hotkey':
            hotkey(*action['keys'])
        
        elif action_type == 'wait':
            wait_seconds(action['seconds'])
        
        elif action_type == 'wait_for':
            print(f"   Esperando imagem: {action['image']}")
            if not find_image(action['image'], action.get('timeout', TIMEOUT)):
                print(f"   ❌ Timeout esperando: {action['image']}")
                return False
            print(f"   ✓ Imagem encontrada!")
        
        else:
            print(f"   ⚠️  Tipo de ação desconhecido: {action_type}")
    
    print("\n" + "=" * 50)
    print("✅ Script executado com sucesso!")
    return True

def create_example_script():
    """Cria um script de exemplo"""
    example = {
        "name": "exemplo",
        "description": "Script de exemplo - clica no botão e digita texto",
        "actions": [
            {
                "type": "click",
                "image": "botao_exemplo",
                "wait": True,
                "required": True
            },
            {
                "type": "wait",
                "seconds": 1
            },
            {
                "type": "type",
                "text": "Texto de exemplo"
            },
            {
                "type": "hotkey",
                "keys": ["ctrl", "s"]
            }
        ]
    }
    
    script_path = SCRIPTS_DIR / "exemplo.json"
    with open(script_path, 'w', encoding='utf-8') as f:
        json.dump(example, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Script de exemplo criado: {script_path}")

def list_images():
    """Lista todas as imagens capturadas"""
    print("📷 Imagens disponíveis:")
    for img in IMAGES_DIR.glob("*.png"):
        print(f"   - {img.stem}")

def list_scripts():
    """Lista todos os scripts disponíveis"""
    print("📜 Scripts disponíveis:")
    for script in SCRIPTS_DIR.glob("*.json"):
        print(f"   - {script.stem}")

def list_tasks():
    """Lista tasks do arquivo tasks.json"""
    if not TASKS_FILE.exists():
        print("📋 Nenhuma task configurada (tasks.json não existe)")
        return
    
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    print(f"📋 Tasks configuradas ({len(tasks)}):")
    for task in tasks:
        repeat = f" ↻{task.get('interval', 5)}s" if task.get('repeat') else ""
        enabled = "✓" if task.get('enabled', True) else "✗"
        print(f"   [{enabled}] #{task['id']}: {task['window_title'][:30]} → {task['image_name']}{repeat}")

def run_tasks():
    """
    Executa todas as tasks do arquivo tasks.json em paralelo.
    Cada task roda em sua própria janela.
    """
    if not TASKS_FILE.exists():
        print("❌ Arquivo tasks.json não encontrado!")
        print("   Use a GUI para criar tasks ou crie manualmente.")
        return
    
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    enabled_tasks = [t for t in tasks if t.get('enabled', True)]
    
    if not enabled_tasks:
        print("❌ Nenhuma task habilitada!")
        return
    
    print(f"🚀 Iniciando {len(enabled_tasks)} tasks em paralelo...")
    print("   Pressione Ctrl+C para parar")
    print("-" * 50)
    
    stop_event = threading.Event()
    
    def run_single_task(task):
        task_id = task['id']
        window_title = task['window_title']
        image_name = task['image_name']
        action = task.get('action', 'click')
        repeat = task.get('repeat', False)
        interval = task.get('interval', 5.0)
        
        template_path = IMAGES_DIR / f"{image_name}.png"
        
        while not stop_event.is_set():
            # Encontra janela
            hwnd = find_window_by_title(window_title)
            if not hwnd:
                print(f"   [#{task_id}] ⚠️  Janela não encontrada: {window_title[:30]}")
                if not repeat:
                    break
                time.sleep(2)
                continue
            
            # Executa click
            if not template_path.exists():
                print(f"   [#{task_id}] ⚠️  Imagem não existe: {image_name}")
                if not repeat:
                    break
                time.sleep(2)
                continue
            
            success, msg, match = find_and_click_window(hwnd, template_path, action)
            
            if success:
                print(f"   [#{task_id}] ✓ {image_name} ({match:.0%})")
            else:
                print(f"   [#{task_id}] ✗ {image_name} ({match:.0%})")
            
            if not repeat:
                break
            
            # Aguarda intervalo
            stop_event.wait(interval)
        
        print(f"   [#{task_id}] Parado")
    
    try:
        with ThreadPoolExecutor(max_workers=len(enabled_tasks)) as executor:
            futures = [executor.submit(run_single_task, task) for task in enabled_tasks]
            
            # Aguarda até Ctrl+C
            while not stop_event.is_set():
                time.sleep(0.5)
                # Verifica se todas terminaram (tasks não-repeat)
                if all(f.done() for f in futures):
                    break
    
    except KeyboardInterrupt:
        print("\n⏹ Parando todas as tasks...")
        stop_event.set()
    
    print("\n✅ Execução finalizada!")

def show_help():
    """Mostra ajuda"""
    print(__doc__)
    print("\nComandos disponíveis:")
    print("  capture <nome>              - Captura uma região da tela")
    print("  click <nome>                - Clica onde encontrar a imagem (tela toda)")
    print("  click <nome> --window \"App\" - Clica na janela específica")
    print("  wait <nome>                 - Espera a imagem aparecer e clica")
    print("  run <script>                - Executa um script de automação sequencial")
    print("  tasks                       - Executa tasks.json (multi-window paralelo)")
    print("  list                        - Lista imagens, scripts e tasks")
    print("  help                        - Mostra esta ajuda")
    print("\nWildcards para janelas:")
    print("  --window \"Chrome*\"         - Começa com 'Chrome'")
    print("  --window \"*YouTube*\"       - Contém 'YouTube'")
    print("  --window \"*- Notepad\"      - Termina com '- Notepad'")

def main():
    ensure_dirs()
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    # Procura por --window na linha de comando
    window_pattern = None
    if '--window' in sys.argv:
        idx = sys.argv.index('--window')
        if idx + 1 < len(sys.argv):
            window_pattern = sys.argv[idx + 1]
    
    if command == 'capture' and len(sys.argv) >= 3:
        capture_region(sys.argv[2])
    
    elif command == 'click' and len(sys.argv) >= 3:
        image_name = sys.argv[2]
        if window_pattern and HAS_WIN32:
            # Modo janela específica
            hwnd = find_window_by_title(window_pattern)
            if hwnd:
                template_path = IMAGES_DIR / f"{image_name}.png"
                success, msg, match = find_and_click_window(hwnd, template_path)
                if success:
                    print(f"✅ {msg} ({match:.0%})")
                else:
                    print(f"❌ {msg} ({match:.0%})")
            else:
                print(f"❌ Janela não encontrada: {window_pattern}")
        else:
            # Modo tela toda (original)
            click_image(image_name)
    
    elif command == 'wait' and len(sys.argv) >= 3:
        click_image(sys.argv[2], wait=True)
    
    elif command == 'run' and len(sys.argv) >= 3:
        run_script(sys.argv[2])
    
    elif command == 'tasks':
        if not HAS_WIN32:
            print("❌ Comando 'tasks' requer win32gui/opencv!")
            return
        run_tasks()
    
    elif command == 'list':
        list_images()
        print()
        list_scripts()
        print()
        list_tasks()
    
    elif command == 'help':
        show_help()
    
    else:
        show_help()

if __name__ == "__main__":
    main()
