# Build with:  pyinstaller build_scripts/terminalmk-downloader-gui.spec
# Run this ON each target OS -- PyInstaller does not cross-compile.
#   Windows:  dist\terminalmk-downloader-gui.exe
#   macOS:    dist/terminalmk-downloader-gui  (wrap into a .app for the
#             terminalmk-dl:// Info.plist registration -- see README)
#   Linux:    dist/terminalmk-downloader-gui

# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

a = Analysis(
    ['../terminalmk_downloader/gui.py'],
    pathex=['..'],
    binaries=[],
    datas=collect_data_files('tkinterdnd2'),
    hiddenimports=collect_submodules('terminalmk_downloader') + ['tkinterdnd2'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='terminalmk-downloader-gui',
    console=False,
    onefile=True,
    upx=False,
)
