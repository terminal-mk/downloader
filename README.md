# Terminal MK - Downloader

Companion desktop app for **terminal.mk**'s CF (Corporate Filings) view.

The `Download All` button on `/view/CF` can't reliably batch-download
dozens/hundreds of attachments from inside a browser (popup caps, no
resumability, at least one host with no CORS forcing double-downloads).
Instead, it hands the batch off to this app:

1. **Direct handoff (preferred):** the page tries to open a
   `terminal.mk-dl://download?d=<payload>` link. This app registers
   itself as the OS handler for that scheme and, once launched, decodes
   the payload and downloads every file.
2. **Fallback:** if nothing answers the custom scheme (app not
   installed), the page saves a small CSV (`FilingID, Form, Date,
   AttachmentIndex, Link`) to Downloads instead. Opening that CSV with
   this app does the same download.

Repo: https://github.com/terminal-mk/downloader

> The `terminal.mk-dl://` scheme itself is a fixed contract with the
> website's JS and isn't renamed here — only the app's own display name
> (**Terminal MK - Downloader**) and executable names changed.

## Download

Grab the package for your OS from the [Releases page](https://github.com/terminal-mk/downloader/releases). Each release attaches these assets — the links below always resolve to whichever release is currently marked "Latest":

| OS | File | Link |
|---|---|---|
| Linux (.deb, pure-Python, no build step) | `terminal.mk-dl_1.1.1_all.deb` | [Download](https://github.com/terminal-mk/downloader/releases/latest/download/terminal.mk-dl_1.1.1_all.deb) |
| Linux (.rpm) | `terminal.mk-dl-1.1.1-1.x86_64.rpm` | [Download](https://github.com/terminal-mk/downloader/releases/latest/download/terminal.mk-dl-1.1.1-1.x86_64.rpm) |
| Windows (.exe) | `terminal.mk-dl-gui.exe` | [Download](https://github.com/terminal-mk/downloader/releases/latest/download/terminal.mk-dl-gui.exe) |
| macOS (.app, zipped) | `terminal.mk-dl.app.zip` | [Download](https://github.com/terminal-mk/downloader/releases/latest/download/terminal.mk-dl.app.zip) |

Older versions (e.g. to pin a specific release) are listed on the [tags/releases page](https://github.com/terminal-mk/downloader/tags) — direct links follow the pattern `https://github.com/terminal-mk/downloader/releases/download/v<version>/<filename>`, e.g. [v1.1.1 `.deb`](https://github.com/terminal-mk/downloader/releases/download/v1.1.1/terminal.mk-dl_1.1.1_all.deb).

> **v1.1.1** fixes `terminal.mk-dl://` links not launching the app on a fresh Linux install (see "Known issue" below) — if you installed an earlier `.deb`/`.rpm` and only the CSV fallback has been working, update to this version.

## Install

### From a package (once built for your OS — see "Packaging" below)
- **Linux (.deb):** `sudo dpkg -i terminal.mk-dl_1.1.1_all.deb`
- **Linux (.rpm):** `sudo rpm -i terminal.mk-dl-1.1.1-1.x86_64.rpm`
- **Windows (.exe):** run the onefile binary, then `terminal.mk-dl.exe register` once to claim `terminal.mk-dl://` links.
- **macOS:** ships with the GUI `.app` (registers the protocol via `Info.plist`); a standalone CLI binary also works for `csv`/`uri` commands without registration.

### From source (any OS with Python 3.9+)
```bash
pip install -e .
terminal.mk-dl register        # claim terminal.mk-dl:// links for this user (CLI-only installs)
terminal.mk-dl-gui             # launch the GUI (self-registers on first run)
```

## Usage

```bash
# Auto-detect a CSV file or a terminal.mk-dl:// URI
terminal.mk-dl open MK_KMB_..._CF.csv
terminal.mk-dl open "terminal.mk-dl://download?d=eyJuIjoi..."

# Explicit subcommands (same thing, useful for scripting)
terminal.mk-dl csv path/to/filings.csv -o ~/Downloads/"Terminal MK" -j 8
terminal.mk-dl uri "terminal.mk-dl://download?d=..."

# Register/re-register this app as the terminal.mk-dl:// handler
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
- **Launched with nothing** (plain double-click) → a blank home screen to paste a `terminal.mk-dl://` link or browse for a CSV.
- Progress screen while downloading, with a **Cancel** button — any file mid-download is stopped and discarded, anything not yet started is skipped, and you land on a summary showing what did and didn't make it.
- Summary screen with an `Open folder` button and **Back to start**.
- Registers itself as the `terminal.mk-dl://` handler automatically the first time it runs (no prompt) — `Re-register app` on the home screen redoes it manually if needed (e.g. after another app steals the association, or after the Chrome/Chromium fix below).

It shares `core.py`, `theme.py`, and `protocol.py` with the CLI — same parsing, same download engine, same colours.

**macOS note:** launching via a `terminal.mk-dl://` link (as opposed to opening a CSV or double-clicking the app) arrives as a Cocoa "open URL" Apple Event, which plain Tkinter doesn't see. The CSV/browse/paste paths work today; wiring up that event needs a small platform hook (e.g. via `pyobjc`) at `.app`-bundling time — noted in `gui.py` and left for the macOS packaging pass.

### Fixed in 1.1.1: `terminal.mk-dl://` links did nothing on a fresh `.deb`/`.rpm` install

Installing the package used to drop a `.desktop` file that only declared
the app *capable* of handling `terminal.mk-dl://` links, without making
it the *default* handler for that scheme. The app normally registers
itself as the default the first time it's actually launched (see
`protocol.py`), but that self-registration never got a chance to run:
the OS won't launch an app for a protocol link it has no default for in
the first place, and `postinst`/`%post` run as root during install with
no real user `$HOME` to write a per-user default into. The practical
symptom was exactly "the CSV fallback always works, the direct link
never does" on a machine where the app had never been opened manually.

Fixed by having `postinst`/`%post` write a **system-wide** default
into `/usr/share/applications/mimeapps.list` at install time (no
per-user home directory needed, no prior launch needed) — see the
comments in `packaging/debian-python/DEBIAN/postinst` and
`packaging/rpm/terminal.mk-dl.spec`. `prerm`/`%preun` remove that
default again on uninstall. If you're on an older `.deb`/`.rpm`,
updating to 1.1.1 (or running `terminal.mk-dl register` manually once)
picks up the fix.

### Known issue: Chrome / Chromium doesn't pick up the handoff on Linux

Some Linux setups didn't launch the app from the `terminal.mk-dl://` link
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
  core.py       # CSV + terminal.mk-dl:// parsing, threaded download engine (cancel-aware)
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
delivery at `packaging/out/terminal.mk-dl_1.1.1_all.deb` — it
runs on the system Python (`Depends: python3, python3-requests, python3-tk`)
rather than bundling a PyInstaller binary, so it doesn't require a build
step; install it directly with `sudo dpkg -i ...`. The PyInstaller-based
`.deb`/`.rpm` (self-contained, no Python dependency) are produced by
`build_scripts/build_linux.sh` once you run it on a Linux box with
network access.

### Troubleshooting: `dpkg-deb: bad permissions` when building

If you got this repo via GitHub's **Download ZIP** button rather than
`git clone`, every file loses its executable bit — GitHub's zip export
doesn't preserve Unix permissions, only `git clone`/`git archive` do.
Building `.deb`s (`packaging/debian-python`, `packaging/debian`) needs
`DEBIAN/postinst`/`DEBIAN/prerm` and the build scripts to be executable,
so `dpkg-deb --build` will fail with a permissions error until you
restore them:

```bash
chmod 755 packaging/debian-python/DEBIAN/postinst packaging/debian-python/DEBIAN/prerm \
           packaging/debian/DEBIAN/postinst packaging/debian/DEBIAN/prerm \
           packaging/debian-python/usr/bin/terminal.mk-dl packaging/debian-python/usr/bin/terminal.mk-dl-gui \
           build_scripts/*.sh packaging/debian/build_deb.sh packaging/rpm/build_rpm.sh
```

`git clone https://github.com/terminal-mk/downloader.git` avoids this
entirely and is the recommended way to get the source.

### Protocol registration reference
- **Linux:** a `.desktop` file with `MimeType=x-scheme-handler/terminal.mk-dl;`, registered via `xdg-mime` *and* written directly into `mimeapps.list` (see the Chrome/Chromium note above). The `.deb`'s `postinst` / the `.rpm`'s `%post` do this automatically at **system level** at install time (`prerm`/`%preun` undo it on removal) — see "Fixed in 1.1.1" above — and `terminal.mk-dl register` does the equivalent per-user for a manual/from-source install.
- **Windows:** an `HKEY_CURRENT_USER\Software\Classes\terminal.mk-dl` key (written as a `.reg` file by `protocol.py`, imported by `terminal.mk-dl register`).
- **macOS:** `CFBundleURLTypes` in the `.app`'s `Info.plist` — set at GUI build time, not at runtime.
