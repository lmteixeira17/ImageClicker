"""
py2app build script for ImageClicker
Usage: python setup.py py2app
"""

from setuptools import setup

APP = ['app_qt.py']
DATA_FILES = [
    ('images', ['images/']),
    ('scripts', ['scripts/']),
    ('', ['tasks.json']),
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'ImageClicker.icns',
    'plist': {
        'CFBundleName': 'ImageClicker',
        'CFBundleDisplayName': 'ImageClicker',
        'CFBundleIdentifier': 'com.imageclicker.app',
        'CFBundleVersion': '3.1.0',
        'CFBundleShortVersionString': '3.1.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '10.15',
    },
    'packages': [
        'PyQt6',
        'cv2',
        'numpy',
        'PIL',
        'mss',
        'Quartz',
        'AppKit',
        'Foundation',
        'objc',
        'pyautogui',
    ],
    'includes': [
        'core',
        'ui_qt',
        'ui_qt.pages',
        'ui_qt.components',
    ],
    'excludes': ['tkinter', 'matplotlib', 'scipy'],
}

setup(
    app=APP,
    name='ImageClicker',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
