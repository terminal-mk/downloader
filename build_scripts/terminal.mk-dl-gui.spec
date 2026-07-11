# Build with:  pyinstaller build_scripts/terminal.mk-dl-gui.spec
# Run this ON each target OS -- PyInstaller does not cross-compile.
#   Windows:  dist\terminal.mk-dl-gui.exe
#   macOS:    dist/terminal.mk-dl-gui  (wrap into a .app for the
#             terminalmk-dl:// Info.plist registration -- see README)
#   Linux:    dist/terminal.mk-dl-gui

# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['../terminalmk_downloader/gui.py'],
    pathex=['..'],
    binaries=[],
    datas=[('../terminalmk_downloader/assets', 'terminalmk_downloader/assets')],
    hiddenimports=collect_submodules('terminalmk_downloader'),
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
    name='terminal.mk-dl-gui',
    console=False,
    onefile=True,
    upx=False,
    # Windows/macOS onefile exe icon. Tk's own title-bar/taskbar icon is
    # set separately at runtime from the bundled PNG (see gui.py).
    icon='../terminalmk_downloader/assets/icon.ico',
)
