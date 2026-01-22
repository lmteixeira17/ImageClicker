# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

a = Analysis(
    ['app_qt.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('images', 'images'),
        ('scripts', 'scripts'),
        ('tasks.json', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'numpy',
        'PIL',
        'PIL.Image',
        'Quartz',
        'Quartz.CoreGraphics',
        'AppKit',
        'Foundation',
        'objc',
        'cv2',
        'mss',
        'mss.darwin',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['cv2.cv2'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['ImageClicker.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ImageClicker',
)
app = BUNDLE(
    coll,
    name='ImageClicker.app',
    icon='ImageClicker.icns',
    bundle_identifier='com.imageclicker.app',
)
