#!/usr/bin/env bash
# Run on a Linux machine (or CI runner) to produce:
#   - dist/terminal.mk-dl                (onefile binary)
#   - packaging/out/terminal.mk-dl_*.deb
#   - packaging/out/terminal.mk-dl-*.rpm  (if rpmbuild is installed)
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

# ---- .deb -------------------------------------------------------------
bash packaging/debian/build_deb.sh dist/terminal.mk-dl

# ---- .rpm (optional, needs rpmbuild) -----------------------------------
if command -v rpmbuild >/dev/null 2>&1; then
  bash packaging/rpm/build_rpm.sh dist/terminal.mk-dl
else
  echo "rpmbuild not found -- skipping .rpm build. Install rpm-build (Fedora/RHEL: sudo dnf install rpm-build) and rerun, or build on an RPM-based distro using packaging/rpm/terminal.mk-dl.spec"
fi

deactivate
