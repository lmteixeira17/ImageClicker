"""
Image-Based Click Automation Tool (macOS)
==========================================

Este script permite automatizar cliques baseados em reconhecimento de imagem.
Suporta execucao em janelas especificas (multi-window) e scripts paralelos.

Uso:
    python iclick.py capture <nome>              # Captura uma regiao da tela
    python iclick.py click <nome>                # Clica onde encontrar a imagem
    python iclick.py click <nome> --window "App" # Clica na janela especifica
    python iclick.py wait <nome>                 # Espera a imagem aparecer e clica
    python iclick.py run <script>                # Executa um script de automacao
    python iclick.py tasks                       # Executa tasks.json (multi-window)
    python iclick.py list                        # Lista recursos disponiveis

Exemplos:
    python iclick.py capture botao_salvar
    python iclick.py click botao_salvar --window "Safari*"
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

# Importa funcoes do core (macOS)
try:
    from core.window_utils import (
        get_windows, find_window_by_title, get_window_dpi_scale,
        get_window_rect, is_window_visible
    )
    from core.image_matcher import find_and_click, capture_window
    import cv2
    import numpy as np
    HAS_QUARTZ = True
except ImportError as e:
    HAS_QUARTZ = False
    print(f"Aviso: Modo janela especifica desativado. {e}")

# Configuracoes
BASE_DIR = Path(__file__).parent
IMAGES_DIR = BASE_DIR / "images"
SCRIPTS_DIR = BASE_DIR / "scripts"
TASKS_FILE = BASE_DIR / "tasks.json"
CONFIDENCE = 0.9  # 90% de precisao no reconhecimento
TIMEOUT = 30  # Segundos para esperar uma imagem

# Seguranca: pause antes de cada acao
pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True  # Mova o mouse para o canto superior esquerdo para parar


def ensure_dirs():
    """Garante que os diretorios existam"""
    IMAGES_DIR.mkdir(exist_ok=True)
    SCRIPTS_DIR.mkdir(exist_ok=True)


# ============== Window-specific functions (macOS) ==============

def find_and_click_window(window_id: int, template_path: Path, action: str = "click"):
    """
    Encontra template em janela especifica e clica (usando Quartz/OpenCV).
    Retorna: (sucesso, mensagem, match_percentage)
    """
    if not HAS_QUARTZ:
        return False, "Quartz nao disponivel", 0.0

    try:
        return find_and_click(window_id, template_path, action)
    except Exception as e:
        return False, str(e), 0.0


# ============== Original pyautogui functions ==============

def capture_region(name: str):
    """
    Captura uma regiao da tela para usar como referencia de clique.
    Apos executar, voce tem 3 segundos para posicionar o mouse no canto superior esquerdo
    da regiao, depois mais 3 segundos para o canto inferior direito.
    """
    print(f"Capturando regiao: {name}")
    print("   Posicione o mouse no CANTO SUPERIOR ESQUERDO da regiao...")
    print("   Aguardando 3 segundos...")
    time.sleep(3)

    start_x, start_y = pyautogui.position()
    print(f"   Ponto inicial: ({start_x}, {start_y})")

    print("   Agora posicione no CANTO INFERIOR DIREITO...")
    print("   Aguardando 3 segundos...")
    time.sleep(3)

    end_x, end_y = pyautogui.position()
    print(f"   Ponto final: ({end_x}, {end_y})")

    # Captura a regiao
    width = abs(end_x - start_x)
    height = abs(end_y - start_y)
    x = min(start_x, end_x)
    y = min(start_y, end_y)

    if width < 5 or height < 5:
        print("   Regiao muito pequena! Tente novamente.")
        return

    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    image_path = IMAGES_DIR / f"{name}.png"
    screenshot.save(image_path)

    print(f"   Imagem salva: {image_path}")
    print(f"   Dimensoes: {width}x{height}")


def find_image(name: str, timeout: float = 0):
    """Encontra uma imagem na tela"""
    image_path = IMAGES_DIR / f"{name}.png"

    if not image_path.exists():
        print(f"   Imagem nao encontrada: {image_path}")
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
    print(f"Procurando: {name}")

    timeout = TIMEOUT if wait else 0
    location = find_image(name, timeout)

    if location:
        center = pyautogui.center(location)
        print(f"   Encontrado em: ({center.x}, {center.y})")
        pyautogui.click(center)
        print(f"   Clique realizado!")
        return True
    else:
        print(f"   Imagem '{name}' nao encontrada na tela")
        return False


def double_click_image(name: str, wait: bool = False):
    """Duplo clique em uma imagem"""
    print(f"Procurando (double-click): {name}")

    timeout = TIMEOUT if wait else 0
    location = find_image(name, timeout)

    if location:
        center = pyautogui.center(location)
        pyautogui.doubleClick(center)
        print(f"   Duplo clique realizado!")
        return True
    return False


def right_click_image(name: str, wait: bool = False):
    """Clique direito em uma imagem"""
    print(f"Procurando (right-click): {name}")

    timeout = TIMEOUT if wait else 0
    location = find_image(name, timeout)

    if location:
        center = pyautogui.center(location)
        pyautogui.rightClick(center)
        print(f"   Clique direito realizado!")
        return True
    return False


def type_text(text: str, interval: float = 0.05):
    """Digita um texto"""
    print(f"Digitando: {text[:30]}...")
    pyautogui.typewrite(text, interval=interval)
    print("   Texto digitado!")


def press_key(key: str):
    """Pressiona uma tecla"""
    print(f"Pressionando: {key}")
    pyautogui.press(key)


def hotkey(*keys):
    """Pressiona uma combinacao de teclas"""
    print(f"Hotkey: {'+'.join(keys)}")
    pyautogui.hotkey(*keys)


def wait_seconds(seconds: float):
    """Aguarda N segundos"""
    print(f"Aguardando {seconds} segundos...")
    time.sleep(seconds)


def run_script(script_name: str):
    """
    Executa um script de automacao (arquivo JSON com sequencia de acoes)
    """
    script_path = SCRIPTS_DIR / f"{script_name}.json"

    if not script_path.exists():
        print(f"Script nao encontrado: {script_path}")
        print("\nCriando script de exemplo...")
        create_example_script()
        return

    with open(script_path, 'r', encoding='utf-8') as f:
        script = json.load(f)

    print(f"Executando script: {script_name}")
    print(f"   Descricao: {script.get('description', 'Sem descricao')}")
    print(f"   Acoes: {len(script.get('actions', []))}")
    print("-" * 50)

    for i, action in enumerate(script.get('actions', []), 1):
        action_type = action.get('type')
        print(f"\n[{i}/{len(script['actions'])}] {action_type}")

        if action_type == 'click':
            if not click_image(action['image'], action.get('wait', False)):
                if action.get('required', True):
                    print("   Acao obrigatoria falhou! Abortando...")
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
                print(f"   Timeout esperando: {action['image']}")
                return False
            print(f"   Imagem encontrada!")

        else:
            print(f"   Tipo de acao desconhecido: {action_type}")

    print("\n" + "=" * 50)
    print("Script executado com sucesso!")
    return True


def create_example_script():
    """Cria um script de exemplo"""
    example = {
        "name": "exemplo",
        "description": "Script de exemplo - clica no botao e digita texto",
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
                "keys": ["command", "s"]  # macOS usa command em vez de ctrl
            }
        ]
    }

    script_path = SCRIPTS_DIR / "exemplo.json"
    with open(script_path, 'w', encoding='utf-8') as f:
        json.dump(example, f, indent=2, ensure_ascii=False)

    print(f"Script de exemplo criado: {script_path}")


def list_images():
    """Lista todas as imagens capturadas"""
    print("Imagens disponiveis:")
    for img in IMAGES_DIR.glob("*.png"):
        print(f"   - {img.stem}")


def list_scripts():
    """Lista todos os scripts disponiveis"""
    print("Scripts disponiveis:")
    for script in SCRIPTS_DIR.glob("*.json"):
        print(f"   - {script.stem}")


def list_tasks():
    """Lista tasks do arquivo tasks.json"""
    if not TASKS_FILE.exists():
        print("Nenhuma task configurada (tasks.json nao existe)")
        return

    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    print(f"Tasks configuradas ({len(tasks)}):")
    for task in tasks:
        repeat = f" (intervalo {task.get('interval', 5)}s)" if task.get('repeat') else ""
        enabled = "[ON]" if task.get('enabled', True) else "[OFF]"
        window = task.get('window_title', task.get('process', 'N/A'))
        print(f"   {enabled} #{task['id']}: {window[:30]} -> {task['image_name']}{repeat}")


def run_tasks():
    """
    Executa todas as tasks do arquivo tasks.json em paralelo.
    Cada task roda em sua propria janela.
    """
    if not TASKS_FILE.exists():
        print("Arquivo tasks.json nao encontrado!")
        print("   Use a GUI para criar tasks ou crie manualmente.")
        return

    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    enabled_tasks = [t for t in tasks if t.get('enabled', True)]

    if not enabled_tasks:
        print("Nenhuma task habilitada!")
        return

    print(f"Iniciando {len(enabled_tasks)} tasks em paralelo...")
    print("   Pressione Ctrl+C para parar")
    print("-" * 50)

    stop_event = threading.Event()

    def run_single_task(task):
        task_id = task['id']
        window_title = task.get('window_title', '')
        process = task.get('process', '')
        image_name = task['image_name']
        action = task.get('action', 'click')
        repeat = task.get('repeat', False)
        interval = task.get('interval', 5.0)

        template_path = IMAGES_DIR / f"{image_name}.png"

        while not stop_event.is_set():
            # Encontra janela
            window_id = None
            if window_title:
                window_id = find_window_by_title(window_title)
            elif process:
                from core.window_utils import find_window_by_process
                window_id = find_window_by_process(process)

            if not window_id:
                target = window_title or process
                print(f"   [#{task_id}] Janela nao encontrada: {target[:30]}")
                if not repeat:
                    break
                time.sleep(2)
                continue

            # Executa click
            if not template_path.exists():
                print(f"   [#{task_id}] Imagem nao existe: {image_name}")
                if not repeat:
                    break
                time.sleep(2)
                continue

            success, msg, match = find_and_click_window(window_id, template_path, action)

            if success:
                print(f"   [#{task_id}] OK {image_name} ({match:.0%})")
            else:
                print(f"   [#{task_id}] Nao encontrado {image_name} ({match:.0%})")

            if not repeat:
                break

            # Aguarda intervalo
            stop_event.wait(interval)

        print(f"   [#{task_id}] Parado")

    try:
        with ThreadPoolExecutor(max_workers=len(enabled_tasks)) as executor:
            futures = [executor.submit(run_single_task, task) for task in enabled_tasks]

            # Aguarda ate Ctrl+C
            while not stop_event.is_set():
                time.sleep(0.5)
                # Verifica se todas terminaram (tasks nao-repeat)
                if all(f.done() for f in futures):
                    break

    except KeyboardInterrupt:
        print("\nParando todas as tasks...")
        stop_event.set()

    print("\nExecucao finalizada!")


def show_help():
    """Mostra ajuda"""
    print(__doc__)
    print("\nComandos disponiveis:")
    print("  capture <nome>              - Captura uma regiao da tela")
    print("  click <nome>                - Clica onde encontrar a imagem (tela toda)")
    print("  click <nome> --window \"App\" - Clica na janela especifica")
    print("  wait <nome>                 - Espera a imagem aparecer e clica")
    print("  run <script>                - Executa um script de automacao sequencial")
    print("  tasks                       - Executa tasks.json (multi-window paralelo)")
    print("  list                        - Lista imagens, scripts e tasks")
    print("  help                        - Mostra esta ajuda")
    print("\nWildcards para janelas:")
    print("  --window \"Safari*\"         - Comeca com 'Safari'")
    print("  --window \"*YouTube*\"       - Contem 'YouTube'")
    print("  --window \"*- Preview\"      - Termina com '- Preview'")


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
        if window_pattern and HAS_QUARTZ:
            # Modo janela especifica
            window_id = find_window_by_title(window_pattern)
            if window_id:
                template_path = IMAGES_DIR / f"{image_name}.png"
                success, msg, match = find_and_click_window(window_id, template_path)
                if success:
                    print(f"OK {msg} ({match:.0%})")
                else:
                    print(f"Falha: {msg} ({match:.0%})")
            else:
                print(f"Janela nao encontrada: {window_pattern}")
        else:
            # Modo tela toda (original)
            click_image(image_name)

    elif command == 'wait' and len(sys.argv) >= 3:
        click_image(sys.argv[2], wait=True)

    elif command == 'run' and len(sys.argv) >= 3:
        run_script(sys.argv[2])

    elif command == 'tasks':
        if not HAS_QUARTZ:
            print("Comando 'tasks' requer Quartz/OpenCV!")
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
