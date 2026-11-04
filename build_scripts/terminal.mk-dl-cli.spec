# Build with:  pyinstaller build_scripts/terminal.mk-dl-cli.spec
# Run this ON each target OS (Windows/macOS/Linux) -- PyInstaller does not
# cross-compile. Produces a single-file executable in dist/.
#
#   Windows:  dist\terminal.mk-dl.exe
#   macOS:    dist/terminal.mk-dl
#   Linux:    dist/terminal.mk-dl

# -*- mode: python ; coding: utf-8 -*-
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))

a = Analysis(
    [os.path.join(SPECPATH, 'entry_cli.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[(os.path.join(ROOT, 'terminalmk_downloader', 'assets'), 'terminalmk_downloader/assets')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    # The CLI never touches Tk, and leaving it out lets the binary run on
    # headless machines with a much smaller download.
    excludes=['tkinter', 'tkinterdnd2'],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='terminal.mk-dl',
    console=True,
    upx=False,
    icon=os.path.join(ROOT, 'terminalmk_downloader', 'assets', 'icon.ico'),
)
