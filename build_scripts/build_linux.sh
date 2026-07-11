#!/usr/bin/env bash
# Run on a Linux machine (or CI runner) to produce:
#   - dist/terminalmk-downloader                (onefile binary)
#   - packaging/out/terminalmk-downloader_*.deb
#   - packaging/out/terminalmk-downloader-*.rpm  (if rpmbuild is installed)
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv-build
source .venv-build/bin/activate
pip install --upgrade pip
pip install -e .
pip install pyinstaller

pyinstaller build_scripts/terminalmk-downloader-cli.spec --distpath dist --workpath build/pyinstaller --noconfirm
pyinstaller build_scripts/terminalmk-downloader-gui.spec --distpath dist --workpath build/pyinstaller --noconfirm

echo "Binaries: dist/terminalmk-downloader, dist/terminalmk-downloader-gui"

# ---- .deb -------------------------------------------------------------
bash packaging/debian/build_deb.sh dist/terminalmk-downloader

# ---- .rpm (optional, needs rpmbuild) -----------------------------------
if command -v rpmbuild >/dev/null 2>&1; then
  bash packaging/rpm/build_rpm.sh dist/terminalmk-downloader
else
  echo "rpmbuild not found -- skipping .rpm build. Install rpm-build (Fedora/RHEL: sudo dnf install rpm-build) and rerun, or build on an RPM-based distro using packaging/rpm/terminalmk-downloader.spec"
fi

deactivate
