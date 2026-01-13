#!/usr/bin/env python3
"""
ImageClicker - PyQt6 GUI (macOS)
Entry point para a interface grafica.
"""

import os
import sys
from pathlib import Path

# CRITICO: Desabilita Qt High DPI Scaling ANTES de qualquer import do Qt
# Isso garante que Qt e MSS usem as mesmas coordenadas (pixels fisicos)
os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0'

# Adiciona diretorio ao path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from ui_qt.main_window import run

if __name__ == "__main__":
    run()
