#!/usr/bin/env bash
# Run on a macOS machine (PyInstaller cannot cross-compile from Linux/Windows),
# with a python.org Python so Tk 8.6 is available. Builds for the machine's
# own architecture, into dist/:
#   terminal.mk-dl.app                  (GUI; registers terminal.mk-dl://)
#   terminal.mk-dl                      (CLI)
#   release/terminal.mk-dl-macos-<arch>.zip      (the .app, zipped)
#   release/terminal.mk-dl-cli-macos-<arch>.tar.gz
set -euo pipefail
cd "$(dirname "$0")/.."

"${PYTHON:-python3}" -m venv .venv-build
# shellcheck disable=SC1091
source .venv-build/bin/activate
pip install --upgrade pip
pip install -r build_scripts/requirements-build.txt

export PYTHONDONTWRITEBYTECODE=1
pyinstaller build_scripts/terminal.mk-dl-cli.spec --distpath dist --workpath build/pyinstaller --noconfirm
pyinstaller build_scripts/terminal.mk-dl-gui.spec --distpath dist --workpath build/pyinstaller --noconfirm
deactivate

ARCH="$(uname -m)"
mkdir -p dist/release
# ditto rather than zip: it keeps the symlinks and signature an .app relies on.
ditto -c -k --sequesterRsrc --keepParent dist/terminal.mk-dl.app "dist/release/terminal.mk-dl-macos-${ARCH}.zip"
tar -C dist -czf "dist/release/terminal.mk-dl-cli-macos-${ARCH}.tar.gz" terminal.mk-dl

echo "Built: dist/release/terminal.mk-dl-macos-${ARCH}.zip, dist/release/terminal.mk-dl-cli-macos-${ARCH}.tar.gz"
