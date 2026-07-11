# Build with:  pyinstaller build_scripts/terminalmk-downloader-cli.spec
# Run this ON each target OS (Windows/macOS/Linux) -- PyInstaller does not
# cross-compile. Produces a single-file executable in dist/.
#
#   Windows:  dist\terminalmk-downloader.exe
#   macOS:    dist/terminalmk-downloader
#   Linux:    dist/terminalmk-downloader

# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['../terminalmk_downloader/__main__.py'],
    pathex=['..'],
    binaries=[],
    datas=[],
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
    name='terminalmk-downloader',
    console=True,
    onefile=True,
    upx=False,
)
