#!/usr/bin/env bash
# Usage: build_linux.sh [all|binaries|packages]   (default: all)
#
#   binaries: dist/terminal.mk-dl, dist/terminal.mk-dl-gui
#   packages: from those binaries, into packaging/out/:
#               terminal.mk-dl-<version>-linux-x86_64.tar.gz
#               terminal.mk-dl_<version>_amd64.deb
#               terminal.mk-dl-<version>-1.x86_64.rpm  (if rpmbuild is installed)
#
# A PyInstaller binary only runs on systems with the glibc it was built
# against or newer, so builds meant for distribution should go through
# build_linux_container.sh instead of running "binaries" on a current distro.
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-all}"
VERSION="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' terminalmk_downloader/__init__.py)"

build_binaries() {
  "${PYTHON:-python3}" -m venv .venv-build
  # shellcheck disable=SC1091
  source .venv-build/bin/activate
  pip install --upgrade pip
  pip install -r build_scripts/requirements-build.txt

  export PYTHONDONTWRITEBYTECODE=1
  pyinstaller build_scripts/terminal.mk-dl-cli.spec --distpath dist --workpath build/pyinstaller --noconfirm
  pyinstaller build_scripts/terminal.mk-dl-gui.spec --distpath dist --workpath build/pyinstaller --noconfirm
  deactivate
  echo "Binaries: dist/terminal.mk-dl, dist/terminal.mk-dl-gui"
}

build_packages() {
  mkdir -p packaging/out

  # ---- .tar.gz (any distro, e.g. Arch) ----------------------------------
  local name="terminal.mk-dl-${VERSION}-linux-x86_64"
  local stage="build/${name}"
  rm -rf "$stage"
  mkdir -p "$stage"
  cp dist/terminal.mk-dl dist/terminal.mk-dl-gui "$stage/"
  tar -C build -czf "packaging/out/${name}.tar.gz" --owner=0 --group=0 "$name"
  echo "Built: packaging/out/${name}.tar.gz"

  # ---- .deb --------------------------------------------------------------
  bash packaging/debian/build_deb.sh dist/terminal.mk-dl dist/terminal.mk-dl-gui

  # ---- .rpm (optional, needs rpmbuild) -----------------------------------
  if command -v rpmbuild >/dev/null 2>&1; then
    bash packaging/rpm/build_rpm.sh dist/terminal.mk-dl dist/terminal.mk-dl-gui
  else
    echo "rpmbuild not found -- skipping .rpm build. Install it (Debian/Ubuntu: sudo apt install rpm, Fedora/RHEL: sudo dnf install rpm-build) and rerun."
  fi
}

case "$MODE" in
  all) build_binaries; build_packages ;;
  binaries) build_binaries ;;
  packages) build_packages ;;
  *) echo "Unknown mode: $MODE (expected all, binaries, or packages)" >&2; exit 2 ;;
esac
