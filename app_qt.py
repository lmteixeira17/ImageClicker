#!/usr/bin/env python3
"""
ImageClicker - PyQt6 GUI
Entry point para a nova interface.
"""

import os
import sys
from pathlib import Path

# CRÍTICO: Desabilita Qt High DPI Scaling ANTES de qualquer import do Qt
# Isso garante que Qt e MSS usem as mesmas coordenadas (pixels físicos)
os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0'

# Configura DPI awareness ANTES de qualquer outra coisa (Windows)
# Isso é crítico para captura de tela correta em multi-monitor com DPIs diferentes
try:
    import ctypes
    # Per-monitor DPI aware v2 (Windows 10 1703+)
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        # Fallback para versões anteriores do Windows
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Configura AppUserModelID para ícone correto na taskbar do Windows
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ImageClicker.App.1.0")
except Exception:
    pass

# Adiciona diretório ao path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from ui_qt.main_window import run

if __name__ == "__main__":
    run()
