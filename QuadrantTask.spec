# -*- mode: python ; coding: utf-8 -*-

import os
pathex=[os.path.abspath('.')]

a = Analysis(
    ['main.py'],
    binaries=[],
    datas=[('source', 'source')],
    hiddenimports=['constants', 'task_card', 'quadrant_panel', 'dialogs', 'data'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='QuadrantTask',
    icon='source/icon.ico',
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
    onefile=True,
)
