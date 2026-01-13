# -*- mode: python ; coding: utf-8 -*-
"""
ImageClicker PyInstaller Spec File
Gera um executável standalone para Windows.
"""

import sys
from pathlib import Path

block_cipher = None

# Diretório base
BASE_DIR = Path(SPECPATH)

a = Analysis(
    ['app_qt.py'],
    pathex=[str(BASE_DIR)],
    binaries=[],
    datas=[
        # Inclui a pasta de imagens (templates)
        ('images', 'images'),
        # Inclui tasks.json se existir
        ('tasks.json', '.'),
        # Inclui o ícone
        ('final_icon.ico', '.'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        'pyautogui',
        'win32gui',
        'win32con',
        'win32api',
        'win32process',
        'ctypes',
        'json',
        'threading',
        'concurrent.futures',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Qt5 - DEVE ser excluído (conflita com PyQt6)
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PySide2',
        'PySide6',
        # Outros não usados
        'tkinter',
        'customtkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'easyocr',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ImageClicker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # False = sem janela de console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='final_icon.ico',
    version='version_info.txt' if Path('version_info.txt').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ImageClicker',
)
