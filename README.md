# Terminal MK - Downloader

Companion desktop app for **terminal.mk**'s CF (Corporate Filings) view.

The `Download All` button on `/view/CF` can't reliably batch-download
dozens/hundreds of attachments from inside a browser (popup caps, no
resumability, at least one host with no CORS forcing double-downloads).
Instead, it hands the batch off to this app:

1. **Direct handoff (preferred):** the page tries to open a
   `terminalmk-dl://download?d=<payload>` link. This app registers
   itself as the OS handler for that scheme and, once launched, decodes
   the payload and downloads every file.
2. **Fallback:** if nothing answers the custom scheme (app not
   installed), the page saves a small CSV (`FilingID, Form, Date,
   AttachmentIndex, Link`) to Downloads instead. Opening that CSV with
   this app does the same download.

Repo: https://github.com/terminal-mk/downloader

> The `terminalmk-dl://` scheme itself is a fixed contract with the
> website's JS and isn't renamed here — only the app's own display name
> (**Terminal MK - Downloader**) and executable names changed.

## Install

### From a package (once built for your OS — see "Packaging" below)
- **Linux (.deb):** `sudo dpkg -i terminal.mk-dl_1.0.0_all.deb`
- **Linux (.rpm):** `sudo rpm -i terminal.mk-dl-1.0.0-1.x86_64.rpm`
- **Windows (.exe):** run the onefile binary, then `terminal.mk-dl.exe register` once to claim `terminalmk-dl://` links.
- **macOS:** ships with the GUI `.app` (registers the protocol via `Info.plist`); a standalone CLI binary also works for `csv`/`uri` commands without registration.

### From source (any OS with Python 3.9+)
```bash
pip install -e .
terminal.mk-dl register        # claim terminalmk-dl:// links for this user (CLI-only installs)
terminal.mk-dl-gui             # launch the GUI (self-registers on first run)
```

## Usage

```bash
# Auto-detect a CSV file or a terminalmk-dl:// URI
terminal.mk-dl open MK_KMB_..._CF.csv
terminal.mk-dl open "terminalmk-dl://download?d=eyJuIjoi..."

# Explicit subcommands (same thing, useful for scripting)
terminal.mk-dl csv path/to/filings.csv -o ~/Downloads/"Terminal MK" -j 8
terminal.mk-dl uri "terminalmk-dl://download?d=..."

# Register/re-register this app as the terminalmk-dl:// handler
terminal.mk-dl register
```

Options:
- `-o, --output DIR` — where to save files (default `~/Downloads/Terminal MK`); a subfolder named after the batch is created inside it.
- `-j, --concurrency N` — parallel downloads (default 6).
- `--no-color` — plain text output (auto-disabled anyway when not attached to a terminal).

Each file is named `<FilingID>_<AttachmentIndex>.<ext>`, with the
extension detected from the response (`Content-Disposition` / URL /
`Content-Type`, falling back to `.pdf` since that's what terminal.mk
filings almost always are).

Exit codes: `0` all files downloaded, `2` one or more failed (details
printed, nothing else in the batch is aborted), `1` couldn't read the
input at all.

## GUI

`terminal.mk-dl-gui` (or just double-click the installed app):

- **Launched with a link or CSV** (protocol handoff, or "Open with" on a CSV) → goes straight to a review screen: a flat list, one row per attachment, each with a checkbox (click a row to toggle it). `Select all` / `Select none`, pick a destination folder, `Download selected`. A **← Back** button returns to the home screen without downloading anything.
- **Launched with nothing** (plain double-click) → a blank home screen to paste a `terminalmk-dl://` link or browse for a CSV.
- Progress screen while downloading, with a **Cancel** button — any file mid-download is stopped and discarded, anything not yet started is skipped, and you land on a summary showing what did and didn't make it.
- Summary screen with an `Open folder` button and **Back to start**.
- Registers itself as the `terminalmk-dl://` handler automatically the first time it runs (no prompt) — `Re-register app` on the home screen redoes it manually if needed (e.g. after another app steals the association, or after the Chrome/Chromium fix below).

It shares `core.py`, `theme.py`, and `protocol.py` with the CLI — same parsing, same download engine, same colours.

**macOS note:** launching via a `terminalmk-dl://` link (as opposed to opening a CSV or double-clicking the app) arrives as a Cocoa "open URL" Apple Event, which plain Tkinter doesn't see. The CSV/browse/paste paths work today; wiring up that event needs a small platform hook (e.g. via `pyobjc`) at `.app`-bundling time — noted in `gui.py` and left for the macOS packaging pass.

### Known issue: Chrome / Chromium doesn't pick up the handoff on Linux

Some Linux setups didn't launch the app from the `terminalmk-dl://` link
when clicked in Chrome or Chromium (Firefox worked fine, and the CSV
fallback always worked). The cause: `xdg-mime default` doesn't always
write to the same `mimeapps.list` copy that Chrome/Chromium reads —
Chrome queries the association through GIO rather than shelling out to
`xdg-mime`, and depending on the distro that can mean it's checking a
different file than the one `xdg-mime` updated.

`register()` (and the `Re-register app` button) now write the
`[Default Applications]` entry directly into **both**
`~/.config/mimeapps.list` and
`~/.local/share/applications/mimeapps.list`, on top of still running
`xdg-mime`, so both lookup paths agree. If a browser still doesn't
prompt after re-registering, that's most likely a sandboxed browser
install (e.g. Chromium via Snap) that can't see
`~/.local/share/applications` at all — in that case the CSV fallback is
the reliable path until the sandbox exposes it.

## Colour palette & icon

- text: `#9fb3ca`
- background: `#2e3b4e`
- accents: wine `#a52a53`, teal `#26a69a`, orange `#ff8c00`

Defined once in `theme.py` and used by both the CLI's ANSI output and the GUI's `ttk` styling.

The app icon (`terminalmk_downloader/assets/`) is the download glyph on
a `#cee5fe` background, exported as SVG plus PNG/ICO/ICNS for the
window icon, `.desktop` icon, and Windows/macOS packaged builds.

```
terminalmk_downloader/
  core.py       # CSV + terminalmk-dl:// parsing, threaded download engine (cancel-aware)
  cli.py        # argparse CLI (terminal.mk-dl)
  gui.py        # Tk GUI (home/review/progress/summary screens, terminal.mk-dl-gui)
  protocol.py   # OS protocol-handler registration (Linux .desktop + mimeapps.list, Windows .reg)
  config.py     # first-run marker + remembered output folder
  theme.py      # shared terminal.mk colour palette
  assets/       # app icon: icon.svg, icon_*.png, icon.ico, icon.icns
```

`core.py`, `protocol.py`, and `theme.py` have no CLI- or GUI-specific code
in them on purpose — both front ends import them directly rather than
duplicating the download engine, registration logic, or colour palette.

**Linux dependency note:** the GUI needs Tk, which on Debian/Ubuntu is a
separate system package (`python3-tk`) rather than something `pip`
installs — the `.deb` already lists it as a dependency, and it's called
out in `requirements.txt`'s comments for from-source installs.

## Packaging

PyInstaller doesn't cross-compile, so each binary has to be built *on*
its target OS.

| OS | Script | Output |
|---|---|---|
| Linux | `build_scripts/build_linux.sh` | `dist/terminal.mk-dl`, `dist/terminal.mk-dl-gui`, plus `.deb`/`.rpm` in `packaging/out/` |
| Windows | `build_scripts\build_windows.bat` | `dist\terminal.mk-dl.exe`, `dist\terminal.mk-dl-gui.exe` |
| macOS | `build_scripts/build_macos.sh` | `dist/terminal.mk-dl`, `dist/terminal.mk-dl-gui` (`.app` bundling comes with the GUI) |

A ready-to-install **pure-Python `.deb`** is already built in this
delivery at `packaging/out/terminal.mk-dl_1.0.0_all.deb` — it
runs on the system Python (`Depends: python3, python3-requests, python3-tk`)
rather than bundling a PyInstaller binary, so it doesn't require a build
step; install it directly with `sudo dpkg -i ...`. The PyInstaller-based
`.deb`/`.rpm` (self-contained, no Python dependency) are produced by
`build_scripts/build_linux.sh` once you run it on a Linux box with
network access.

### Protocol registration reference
- **Linux:** a `.desktop` file with `MimeType=x-scheme-handler/terminalmk-dl;`, registered via `xdg-mime` *and* written directly into `mimeapps.list` (see the Chrome/Chromium note above), done automatically by the `.deb`'s `postinst`, or by `terminal.mk-dl register` for a manual/from-source install.
- **Windows:** an `HKEY_CURRENT_USER\Software\Classes\terminalmk-dl` key (written as a `.reg` file by `protocol.py`, imported by `terminal.mk-dl register`).
- **macOS:** `CFBundleURLTypes` in the `.app`'s `Info.plist` — set at GUI build time, not at runtime.
