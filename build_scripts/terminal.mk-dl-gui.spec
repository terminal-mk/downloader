# Build with:  pyinstaller build_scripts/terminal.mk-dl-gui.spec
# Run this ON each target OS -- PyInstaller does not cross-compile.
#   Windows:  dist\terminal.mk-dl-gui.exe
#   macOS:    dist/terminal.mk-dl.app  (registers terminal.mk-dl:// through
#             the Info.plist below)
#   Linux:    dist/terminal.mk-dl-gui

# -*- mode: python ; coding: utf-8 -*-
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))
ASSETS = os.path.join(ROOT, 'terminalmk_downloader', 'assets')
IS_MACOS = sys.platform == 'darwin'

with open(os.path.join(ROOT, 'terminalmk_downloader', '__init__.py'), encoding='utf-8') as f:
    VERSION = re.search(r'__version__ = "([^"]+)"', f.read()).group(1)

binaries = []
if sys.platform.startswith('linux'):
    # PyInstaller assumes the host provides these two and leaves them out, but
    # Tk and tkdnd can't load without them and not every system has them. Tk
    # doesn't use the GPU drivers that reason for leaving out libxcb applies to.
    from PyInstaller.depend.bindepend import resolve_library_path

    for lib in ('libxcb.so.1', 'libXcursor.so.1'):
        path = resolve_library_path(lib)
        if path is None:
            raise SystemExit(f'{lib} not found -- see build_linux_container.sh')
        binaries.append((path, '.'))

# tkinterdnd2's native tkdnd library is collected by the hook that ships
# with pyinstaller-hooks-contrib, so it needs no entry here.
a = Analysis(
    [os.path.join(SPECPATH, 'entry_gui.py')],
    pathex=[ROOT],
    binaries=binaries,
    datas=[(ASSETS, 'terminalmk_downloader/assets')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure, a.zipped_data)

if IS_MACOS:
    # An .app has to be a onedir build. argv_emulation stays off because Tk
    # receives the open-URL/open-file Apple Events itself (see gui.py).
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='terminal.mk-dl-gui',
        console=False,
        upx=False,
        argv_emulation=False,
    )
    coll = COLLECT(exe, a.binaries, a.datas, name='terminal.mk-dl-gui', upx=False)
    app = BUNDLE(
        coll,
        name='terminal.mk-dl.app',
        icon=os.path.join(ASSETS, 'icon.icns'),
        bundle_identifier='mk.terminal.downloader',
        version=VERSION,
        info_plist={
            'CFBundleName': 'Terminal MK - Downloader',
            'CFBundleDisplayName': 'Terminal MK - Downloader',
            'NSHighResolutionCapable': True,
            'CFBundleURLTypes': [{
                'CFBundleURLName': 'mk.terminal.downloader',
                'CFBundleURLSchemes': ['terminal.mk-dl'],
            }],
            'CFBundleDocumentTypes': [{
                'CFBundleTypeName': 'CSV document',
                'CFBundleTypeExtensions': ['csv'],
                'CFBundleTypeRole': 'Viewer',
                'LSHandlerRank': 'Alternate',
            }],
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='terminal.mk-dl-gui',
        console=False,
        upx=False,
        # Windows exe icon. Tk's own title-bar/taskbar icon is set separately
        # at runtime from the bundled PNG (see gui.py).
        icon=os.path.join(ASSETS, 'icon.ico'),
    )
