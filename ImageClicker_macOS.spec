# -*- mode: python ; coding: utf-8 -*-
"""
ImageClicker PyInstaller Spec File - macOS
Gera um aplicativo .app nativo para macOS.
"""

import sys
from pathlib import Path

block_cipher = None

# Diretorio base
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
        # Inclui scripts se existir
        ('scripts', 'scripts') if (BASE_DIR / 'scripts').exists() else ('', ''),
        # Inclui o icone
        ('ImageClicker.icns', '.'),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        # Image processing
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        # Automation
        'pyautogui',
        'mss',
        'mss.darwin',
        # macOS APIs (PyObjC)
        'objc',
        'Quartz',
        'Quartz.CoreGraphics',
        'Quartz.ImageIO',
        'AppKit',
        'Cocoa',
        'Foundation',
        'ApplicationServices',
        # Standard library
        'ctypes',
        'json',
        'threading',
        'concurrent.futures',
        'queue',
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Qt5 - DEVE ser excluido (conflita com PyQt6)
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PySide2',
        'PySide6',
        # Windows-specific (nao necessarios no macOS)
        'win32gui',
        'win32con',
        'win32api',
        'win32process',
        'pywin32',
        # Outros nao usados
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

# Remove entradas vazias de datas
a.datas = [d for d in a.datas if d[0] and d[1]]

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
    upx=False,  # UPX pode causar problemas no macOS
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # None = arquitetura atual (arm64 ou x86_64)
    codesign_identity=None,  # Adicione sua identidade de code signing aqui se necessario
    entitlements_file=None,
    icon='ImageClicker.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ImageClicker',
)

# Gera o bundle .app nativo do macOS
app = BUNDLE(
    coll,
    name='ImageClicker.app',
    icon='ImageClicker.icns',
    bundle_identifier='com.imageclicker.app',
    info_plist={
        'CFBundleName': 'ImageClicker',
        'CFBundleDisplayName': 'ImageClicker',
        'CFBundleGetInfoString': 'ImageClicker - Automacao de cliques baseada em imagem',
        'CFBundleIdentifier': 'com.imageclicker.app',
        'CFBundleVersion': '3.2.0',
        'CFBundleShortVersionString': '3.2.0',
        'NSHumanReadableCopyright': 'Copyright 2026 ImageClicker',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,  # Suporta Dark Mode
        # Permissoes necessarias
        'NSAccessibilityUsageDescription': 'ImageClicker precisa de acesso para automatizar cliques.',
        'NSScreenCaptureUsageDescription': 'ImageClicker precisa de acesso para capturar a tela e encontrar imagens.',
        # LSMinimumSystemVersion para macOS 10.15+
        'LSMinimumSystemVersion': '10.15',
        # Ambiente de execucao
        'LSEnvironment': {
            'QT_ENABLE_HIGHDPI_SCALING': '0',
        },
    },
)
