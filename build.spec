# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 配置文件
import os

block_cipher = None

# 获取src目录路径
src_path = os.path.join(os.getcwd(), 'src')
ui_path = os.path.join(src_path, 'ui')

a = Analysis(
    ['src/main.py'],
    pathex=[src_path],
    binaries=[],
    datas=[
        (os.path.join(ui_path, '*.py'), 'ui'),
        (os.path.join(src_path, 'scanner.py'), '.'),
        (os.path.join(src_path, 'validator.py'), '.'),
        (os.path.join(src_path, 'clipboard.py'), '.'),
        (os.path.join(src_path, 'browser.py'), '.'),
        (os.path.join(src_path, 'firewall.py'), '.'),
        (os.path.join(src_path, 'connectivity_test.py'), '.'),
    ],
    hiddenimports=[
        'PyQt6.sip',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
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
    name='mc_ipv6_V1.3.4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
