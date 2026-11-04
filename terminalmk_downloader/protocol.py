"""
Registers this app as the OS handler for terminal.mk-dl:// links, so the
"Download All" button on terminal.mk/view/CF can hand batches straight
to it (see CF.js's tryLaunchDownloader / PROTOCOL_SCHEME).

The protocol scheme itself is a fixed contract with the website's JS
(see CF.js's PROTOCOL_SCHEME) and now matches the app's display name:
terminal.mk-dl. It was previously terminalmk-dl (no dot) -- both the
scheme and the app's display/executable names were renamed together,
so anyone with the old build still registered will need to re-run
`register()` (or reinstall) to pick up the new scheme.

Each OS does this differently:
  - Linux:   a .desktop file with MimeType=x-scheme-handler/terminal.mk-dl,
             registered via xdg-mime *and* written directly into
             mimeapps.list (see note in register_linux below -- some
             browsers, notably Chrome/Chromium, don't reliably pick up
             xdg-mime's own writes).
  - Windows: a registry key under HKCU\\Software\\Classes\\terminal.mk-dl.
  - macOS:   CFBundleURLTypes in the .app's Info.plist (set at build
             time when the .app bundle is created -- there is nothing
             to register at runtime, so `register()` is a no-op there
             and this is handled in the GUI packaging step instead).
"""

from __future__ import annotations

import configparser
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from .core import PROTOCOL_SCHEME

APP_NAME = "terminal.mk-dl"
GUI_APP_NAME = "terminal.mk-dl-gui"
DISPLAY_NAME = "Terminal MK - Downloader"
DESKTOP_FILE_NAME = f"{APP_NAME}.desktop"
MIME_TYPE = f"x-scheme-handler/{PROTOCOL_SCHEME}"

# Populated by icon.py / packaging at install/build time. On a from-source
# install this points at the PNG shipped in the repo; packaged builds
# install it under the icon theme and pass that path instead.
ICON_PATH = str(Path(__file__).resolve().parent / "assets" / "icon_256.png")


def is_frozen() -> bool:
    """True when running from a PyInstaller build rather than from source."""
    return bool(getattr(sys, "frozen", False))


def external_env() -> dict[str, str]:
    """Environment for launching system tools (xdg-open, xdg-mime, ...).

    PyInstaller points LD_LIBRARY_PATH at the libraries it bundled, which
    are older than the host's and break host binaries that inherit them.
    It keeps the original value in LD_LIBRARY_PATH_ORIG."""
    env = dict(os.environ)
    if is_frozen():
        original = env.pop("LD_LIBRARY_PATH_ORIG", None)
        if original is None:
            env.pop("LD_LIBRARY_PATH", None)
        else:
            env["LD_LIBRARY_PATH"] = original
    return env


def _linux_icon_value() -> str:
    """Icon= value for the .desktop file. A onefile build unpacks ICON_PATH
    into a temp dir that disappears on exit, so a frozen build copies it
    into the user's icon theme and refers to it by name instead."""
    if not is_frozen():
        return ICON_PATH
    icon_dir = Path.home() / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps"
    icon_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ICON_PATH, icon_dir / f"{APP_NAME}.png")
    return APP_NAME


def _linux_desktop_entry(exec_path: str, for_gui: bool) -> str:
    exec_line = f'"{exec_path}" %u' if for_gui else f'"{exec_path}" open %u'
    no_display = "false" if for_gui else "true"
    return textwrap.dedent(f"""\
        [Desktop Entry]
        Type=Application
        Name={DISPLAY_NAME}
        Comment=Batch-downloads filing attachments handed off from terminal.mk
        Exec={exec_line}
        Terminal=false
        NoDisplay={no_display}
        Categories=Network;FileTransfer;Utility;
        StartupNotify=false
        Icon={_linux_icon_value()}
        MimeType={MIME_TYPE};
        """)


def _write_mimeapps_default(scheme_key: str, desktop_file: str) -> list[Path]:
    """Directly write the [Default Applications] entry into every
    mimeapps.list location a Linux desktop might read.

    Why this exists: `xdg-mime default` normally handles this on its
    own, but on several common setups (Chrome/Chromium in particular,
    since it queries via GIO rather than shelling out to xdg-mime) the
    write ends up in a location or format the browser doesn't check --
    e.g. only ~/.local/share/applications/mimeapps.list gets updated
    while GIO reads ~/.config/mimeapps.list, or vice versa depending on
    distro. Writing to both explicitly, in addition to running
    xdg-mime, is a belt-and-suspenders fix for that.
    """
    candidates = [
        Path.home() / ".config" / "mimeapps.list",
        Path.home() / ".local" / "share" / "applications" / "mimeapps.list",
    ]
    written: list[Path] = []
    for path in candidates:
        path.parent.mkdir(parents=True, exist_ok=True)
        parser = configparser.RawConfigParser()
        parser.optionxform = str  # preserve case
        if path.exists():
            try:
                parser.read(path, encoding="utf-8")
            except configparser.Error:
                pass  # corrupt/unreadable -- rewrite it cleanly below
        if not parser.has_section("Default Applications"):
            parser.add_section("Default Applications")
        parser.set("Default Applications", scheme_key, desktop_file)
        if not parser.has_section("Added Associations"):
            parser.add_section("Added Associations")
        existing = parser.get("Added Associations", scheme_key, fallback="")
        names = [n for n in existing.split(";") if n and n != desktop_file]
        names.append(desktop_file)
        parser.set("Added Associations", scheme_key, ";".join(names) + ";")
        with path.open("w", encoding="utf-8") as f:
            parser.write(f, space_around_delimiters=False)
        written.append(path)
    return written


def register_linux(exec_path: str | None = None, for_gui: bool = True) -> Path:
    default_name = GUI_APP_NAME if for_gui else APP_NAME
    exec_path = exec_path or shutil.which(default_name) or shutil.which(APP_NAME) or sys.argv[0]
    apps_dir = Path.home() / ".local" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)
    desktop_path = apps_dir / DESKTOP_FILE_NAME
    desktop_path.write_text(_linux_desktop_entry(exec_path, for_gui), encoding="utf-8")
    desktop_path.chmod(0o755)

    if shutil.which("desktop-file-validate"):
        subprocess.run(["desktop-file-validate", str(desktop_path)], check=False, env=external_env())

    if shutil.which("xdg-mime"):
        subprocess.run(
            ["xdg-mime", "default", DESKTOP_FILE_NAME, MIME_TYPE],
            check=False,
            env=external_env(),
        )
    # Belt-and-suspenders: write mimeapps.list directly too. This is the
    # actual fix for the "worked in Firefox, silently did nothing in
    # Chrome/Chromium" report -- Chrome reads mimeapps.list itself and
    # doesn't always agree with xdg-mime about which copy is canonical.
    _write_mimeapps_default(MIME_TYPE, DESKTOP_FILE_NAME)

    if shutil.which("update-desktop-database"):
        subprocess.run(["update-desktop-database", str(apps_dir)], check=False, env=external_env())

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
        @="URL:Terminal MK - Downloader Protocol"
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
        # CREATE_NO_WINDOW: the windowed GUI build has no console of its own,
        # so reg.exe would otherwise flash one up.
        subprocess.run(
            ["reg", "import", str(reg_path)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    return reg_path


def register(for_gui: bool = True) -> str:
    """Best-effort protocol registration for the current OS. Returns a
    human-readable message describing what happened. Registers the GUI
    as the handler by default, since that's what a double-click / a
    browser-triggered terminal.mk-dl:// link should open."""
    default_name = GUI_APP_NAME if for_gui else APP_NAME
    if is_frozen():
        # argv[0] can be relative, and PATH may hold a different copy.
        exec_path = str(Path(sys.executable).resolve())
    else:
        exec_path = shutil.which(default_name) or shutil.which(APP_NAME) or sys.argv[0]

    if sys.platform.startswith("linux"):
        path = register_linux(exec_path, for_gui=for_gui)
        return f"Registered {PROTOCOL_SCHEME}:// via {path}"
    if sys.platform.startswith("win"):
        path = register_windows(exec_path, for_gui=for_gui)
        return f"Registered {PROTOCOL_SCHEME}:// via {path} (imported into HKCU)"
    if sys.platform == "darwin":
        return (
            "On macOS the terminal.mk-dl:// handler is registered when the .app "
            "bundle is installed (CFBundleURLTypes in Info.plist), not at runtime. "
            "Nothing to do here for the CLI build."
        )
    return f"Protocol registration is not implemented for platform: {sys.platform}"
