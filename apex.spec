# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['apps/desktop_client/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('models/hand_landmarker.task', 'models'),
        ('models/face_landmarker.task', 'models'),
        ('config/gestures.yaml', 'config'),
        ('config/voice_commands.yaml', 'config'),
    ],
    hiddenimports=[
        'mediapipe',
        'mediapipe.tasks.python.vision',
        'mediapipe.tasks.python.core',
        'cv2',
        'numpy',
        'yaml',
        'sounddevice',
        'faster_whisper',
        'websockets',
        'keyboard',
        'pygetwindow',
        'comtypes',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ApexControl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if Path('assets/icon.ico').exists() else None,
)
