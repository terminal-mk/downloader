# terminalmk-downloader

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

This first release is the **CLI**. A GUI (desktop app with the same
terminal.mk colour palette) is next; it will share the `core.py` engine
in this package.

## Install

### From a package (once built for your OS — see "Packaging" below)
- **Linux (.deb):** `sudo dpkg -i terminalmk-downloader_1.0.0_all.deb`
- **Linux (.rpm):** `sudo rpm -i terminalmk-downloader-1.0.0-1.x86_64.rpm`
- **Windows (.exe):** run the onefile binary, then `terminalmk-downloader.exe register` once to claim `terminalmk-dl://` links.
- **macOS:** ships with the GUI `.app` (registers the protocol via `Info.plist`); a standalone CLI binary also works for `csv`/`uri` commands without registration.

### From source (any OS with Python 3.9+)
```bash
pip install -e .
terminalmk-downloader register        # claim terminalmk-dl:// links for this user (CLI-only installs)
terminalmk-downloader-gui             # launch the GUI (self-registers on first run)
```

## Usage

```bash
# Auto-detect a CSV file or a terminalmk-dl:// URI
terminalmk-downloader open MK_KMB_..._CF.csv
terminalmk-downloader open "terminalmk-dl://download?d=eyJuIjoi..."

# Explicit subcommands (same thing, useful for scripting)
terminalmk-downloader csv path/to/filings.csv -o ~/Downloads/terminalmk -j 8
terminalmk-downloader uri "terminalmk-dl://download?d=..."

# Register/re-register this app as the terminalmk-dl:// handler
terminalmk-downloader register
```

Options:
- `-o, --output DIR` — where to save files (default `~/Downloads/terminalmk`); a subfolder named after the batch is created inside it.
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

`terminalmk-downloader-gui` (or just double-click the installed app):

- **Launched with a link or CSV** (protocol handoff, or "Open with" on a CSV) → goes straight to a review screen: a flat list, one row per attachment, each with a checkbox (click a row to toggle it). `Select all` / `Select none`, pick a destination folder, `Download selected`.
- **Launched with nothing** (plain double-click) → a blank screen to paste a `terminalmk-dl://` link or browse for a CSV.
- Progress screen while downloading, then a summary with an `Open folder` button.
- Registers itself as the `terminalmk-dl://` handler automatically the first time it runs (no prompt) — `Re-register app` on the blank screen redoes it manually if needed (e.g. after another app steals the association).

It shares `core.py`, `theme.py`, and `protocol.py` with the CLI — same parsing, same download engine, same colours.

**macOS note:** launching via a `terminalmk-dl://` link (as opposed to opening a CSV or double-clicking the app) arrives as a Cocoa "open URL" Apple Event, which plain Tkinter doesn't see. The CSV/browse/paste paths work today; wiring up that event needs a small platform hook (e.g. via `pyobjc`) at `.app`-bundling time — noted in `gui.py` and left for the macOS packaging pass.



```
terminalmk_downloader/
  core.py       # CSV + terminalmk-dl:// parsing, threaded download engine
  cli.py        # argparse CLI
  gui.py        # Tk GUI (blank/review/progress/summary screens)
  protocol.py   # OS protocol-handler registration (Linux .desktop, Windows .reg)
  config.py     # first-run marker + remembered output folder
  theme.py      # shared terminal.mk colour palette
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
| Linux | `build_scripts/build_linux.sh` | `dist/terminalmk-downloader` binary, plus `.deb`/`.rpm` in `packaging/out/` |
| Windows | `build_scripts\build_windows.bat` | `dist\terminalmk-downloader.exe` |
| macOS | `build_scripts/build_macos.sh` | `dist/terminalmk-downloader` binary (`.app` bundling comes with the GUI) |

A ready-to-install **pure-Python `.deb`** is already built in this
delivery at `packaging/out/terminalmk-downloader_1.0.0_all.deb` — it
runs on the system Python (`Depends: python3, python3-requests`) rather
than bundling a PyInstaller binary, so it doesn't require a build step;
install it directly with `sudo dpkg -i ...`. The PyInstaller-based
`.deb`/`.rpm` (self-contained, no Python dependency) are produced by
`build_scripts/build_linux.sh` once you run it on a Linux box with
network access (this sandbox has none, which is why that script wasn't
run here).

### Protocol registration reference
- **Linux:** a `.desktop` file with `MimeType=x-scheme-handler/terminalmk-dl;`, registered via `xdg-mime` (done automatically by the `.deb`'s `postinst`, or by `terminalmk-downloader register` for a manual/from-source install).
- **Windows:** an `HKEY_CURRENT_USER\Software\Classes\terminalmk-dl` key (written as a `.reg` file by `protocol.py`, imported by `terminalmk-downloader register`).
- **macOS:** `CFBundleURLTypes` in the `.app`'s `Info.plist` — set at GUI build time, not at runtime.

## Colour palette

- text: `#9fb3ca`
- background: `#2e3b4e`
- accents: wine `#a52a53`, teal `#26a69a`, orange `#ff8c00`

Defined once in `theme.py` and used by both the CLI's ANSI output and the GUI's `ttk` styling.

