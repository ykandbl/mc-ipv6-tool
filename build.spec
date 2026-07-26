# -*- mode: python ; coding: utf-8 -*-
import os

src_path = os.path.join(os.getcwd(), "src")
version_context = {}
with open(os.path.join(src_path, "app_version.py"), encoding="utf-8") as version_file:
    exec(version_file.read(), version_context)
artifact_name = f"IPv6Tool-v{version_context['APP_VERSION']}"

a = Analysis(
    ["src/main.py"],
    pathex=[src_path],
    binaries=[],
    datas=[],
    hiddenimports=["PyQt6.sip"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=artifact_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    uac_admin=True,
    disable_windowed_traceback=False,
)
