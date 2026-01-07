#!/usr/bin/env python3
"""
ImageClicker - PyQt6 GUI
Entry point para a nova interface.
"""

import sys
from pathlib import Path

# Configura AppUserModelID para ícone correto na taskbar do Windows
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ImageClicker.App.1.0")
except Exception:
    pass

# Adiciona diretório ao path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from ui_qt.main_window import run

if __name__ == "__main__":
    run()
