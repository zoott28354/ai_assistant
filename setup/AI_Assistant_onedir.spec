# -*- mode: python ; coding: utf-8 -*-

import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(SPECPATH, ".."))
sys.path.insert(0, ROOT_DIR)

from core.app_meta import APP_SLUG

app_name = APP_SLUG

a = Analysis(
    [os.path.join(ROOT_DIR, 'main.py')],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=[
        (os.path.join(ROOT_DIR, 'ai_assistant.ico'), '.'),
        (os.path.join(ROOT_DIR, 'LICENSE'), '.'),
        (os.path.join(ROOT_DIR, 'README.md'), '.'),
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name=app_name,
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
    icon=[os.path.join(ROOT_DIR, 'ai_assistant.ico')],
    version=os.path.join(SPECPATH, 'version_info.py'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)
