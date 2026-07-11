# Build with:  pyinstaller build_scripts/terminal.mk-dl-cli.spec
# Run this ON each target OS (Windows/macOS/Linux) -- PyInstaller does not
# cross-compile. Produces a single-file executable in dist/.
#
#   Windows:  dist\terminal.mk-dl.exe
#   macOS:    dist/terminal.mk-dl
#   Linux:    dist/terminal.mk-dl

# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['../terminalmk_downloader/__main__.py'],
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
    name='terminal.mk-dl',
    console=True,
    onefile=True,
    upx=False,
    icon='../terminalmk_downloader/assets/icon.ico',
)
