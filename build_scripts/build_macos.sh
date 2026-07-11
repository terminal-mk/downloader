#!/usr/bin/env bash
# Run on a macOS machine (PyInstaller cannot cross-compile from Linux/Windows).
# Produces dist/terminal.mk-dl (onefile CLI binary).
#
# NOTE: the terminalmk-dl:// protocol handler on macOS is registered via
# CFBundleURLTypes in an .app bundle's Info.plist, not at runtime -- that
# bundling happens in the GUI build (build_scripts/build_macos_gui.sh,
# added alongside the GUI). This script just gets the CLI binary built.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv-build
source .venv-build/bin/activate
pip install --upgrade pip
pip install -e .
pip install pyinstaller

pyinstaller build_scripts/terminal.mk-dl-cli.spec --distpath dist --workpath build/pyinstaller --noconfirm
pyinstaller build_scripts/terminal.mk-dl-gui.spec --distpath dist --workpath build/pyinstaller --noconfirm

echo "Binaries: dist/terminal.mk-dl, dist/terminal.mk-dl-gui"
deactivate
