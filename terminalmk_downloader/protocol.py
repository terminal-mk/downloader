"""
Registers this app as the OS handler for terminalmk-dl:// links, so the
"Download All" button on terminal.mk/view/CF can hand batches straight
to it (see CF.js's tryLaunchDownloader / PROTOCOL_SCHEME).

Each OS does this differently:
  - Linux:   a .desktop file with MimeType=x-scheme-handler/terminalmk-dl,
             registered via xdg-mime.
  - Windows: a registry key under HKCU\\Software\\Classes\\terminalmk-dl.
  - macOS:   CFBundleURLTypes in the .app's Info.plist (set at build
             time when the .app bundle is created -- there is nothing
             to register at runtime, so `register()` is a no-op there
             and this is handled in the GUI packaging step instead).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from .core import PROTOCOL_SCHEME

APP_NAME = "terminalmk-downloader"
GUI_APP_NAME = "terminalmk-downloader-gui"
DESKTOP_FILE_NAME = f"{APP_NAME}.desktop"


def _linux_desktop_entry(exec_path: str, for_gui: bool) -> str:
    exec_line = f"{exec_path} %u" if for_gui else f"{exec_path} open %u"
    no_display = "false" if for_gui else "true"
    return textwrap.dedent(f"""\
        [Desktop Entry]
        Type=Application
        Name=terminal.mk Downloader
        Comment=Batch-downloads filing attachments handed off from terminal.mk
        Exec={exec_line}
        Terminal=false
        NoDisplay={no_display}
        MimeType=x-scheme-handler/{PROTOCOL_SCHEME};
        """)


def register_linux(exec_path: str | None = None, for_gui: bool = True) -> Path:
    default_name = GUI_APP_NAME if for_gui else APP_NAME
    exec_path = exec_path or shutil.which(default_name) or shutil.which(APP_NAME) or sys.argv[0]
    apps_dir = Path.home() / ".local" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)
    desktop_path = apps_dir / DESKTOP_FILE_NAME
    desktop_path.write_text(_linux_desktop_entry(exec_path, for_gui), encoding="utf-8")
    desktop_path.chmod(0o755)

    if shutil.which("xdg-mime"):
        subprocess.run(
            ["xdg-mime", "default", DESKTOP_FILE_NAME, f"x-scheme-handler/{PROTOCOL_SCHEME}"],
            check=False,
        )
    if shutil.which("update-desktop-database"):
        subprocess.run(["update-desktop-database", str(apps_dir)], check=False)

    return desktop_path


def _windows_reg_script(exec_path: str, for_gui: bool) -> str:
    # Written as a .reg file rather than touching the registry directly
    # from Python by default -- keeps this auditable/opt-in, since it's
    # editing HKEY_CURRENT_USER\Software\Classes.
    escaped = exec_path.replace("\\", "\\\\")
    command = f'\\"{escaped}\\" \\"%1\\"' if for_gui else f'\\"{escaped}\\" open \\"%1\\"'
    return textwrap.dedent(f"""\
        Windows Registry Editor Version 5.00

        [HKEY_CURRENT_USER\\Software\\Classes\\{PROTOCOL_SCHEME}]
        @="URL:terminal.mk Downloader Protocol"
        "URL Protocol"=""

        [HKEY_CURRENT_USER\\Software\\Classes\\{PROTOCOL_SCHEME}\\DefaultIcon]
        @="\\"{escaped}\\",0"

        [HKEY_CURRENT_USER\\Software\\Classes\\{PROTOCOL_SCHEME}\\shell]

        [HKEY_CURRENT_USER\\Software\\Classes\\{PROTOCOL_SCHEME}\\shell\\open]

        [HKEY_CURRENT_USER\\Software\\Classes\\{PROTOCOL_SCHEME}\\shell\\open\\command]
        @="{command}"
        """)


def register_windows(exec_path: str | None = None, for_gui: bool = True) -> Path:
    """Writes a .reg file next to the executable and imports it via reg.exe.
    Only does anything meaningful on Windows; safe to call elsewhere."""
    exec_path = exec_path or sys.argv[0]
    reg_path = Path(exec_path).with_name(f"{APP_NAME}.reg")
    reg_path.write_text(_windows_reg_script(exec_path, for_gui), encoding="utf-8")

    if sys.platform.startswith("win") and shutil.which("reg"):
        subprocess.run(["reg", "import", str(reg_path)], check=False)

    return reg_path


def register(for_gui: bool = True) -> str:
    """Best-effort protocol registration for the current OS. Returns a
    human-readable message describing what happened. Registers the GUI
    as the handler by default, since that's what a double-click / a
    browser-triggered terminalmk-dl:// link should open."""
    default_name = GUI_APP_NAME if for_gui else APP_NAME
    exec_path = shutil.which(default_name) or shutil.which(APP_NAME) or sys.argv[0]

    if sys.platform.startswith("linux"):
        path = register_linux(exec_path, for_gui=for_gui)
        return f"Registered {PROTOCOL_SCHEME}:// via {path}"
    if sys.platform.startswith("win"):
        path = register_windows(exec_path, for_gui=for_gui)
        return f"Registered {PROTOCOL_SCHEME}:// via {path} (imported into HKCU)"
    if sys.platform == "darwin":
        return (
            "On macOS the terminalmk-dl:// handler is registered when the .app "
            "bundle is installed (CFBundleURLTypes in Info.plist), not at runtime. "
            "Nothing to do here for the CLI build."
        )
    return f"Protocol registration is not implemented for platform: {sys.platform}"
