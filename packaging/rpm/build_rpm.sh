#!/usr/bin/env bash
# Usage: build_rpm.sh <path-to-pyinstaller-binary>
# Requires rpmbuild (Fedora/RHEL: sudo dnf install rpm-build).
set -euo pipefail

BIN_PATH="${1:?Usage: build_rpm.sh <path-to-pyinstaller-binary>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="$HERE/../out"
RPMBUILD_ROOT="$HOME/rpmbuild"

mkdir -p "$RPMBUILD_ROOT/SOURCES" "$RPMBUILD_ROOT/SPECS" "$OUT_DIR"
cp "$BIN_PATH" "$RPMBUILD_ROOT/SOURCES/terminal.mk-dl"
cp "$HERE/icons/terminal.mk-dl.png" "$RPMBUILD_ROOT/SOURCES/terminal.mk-dl.png"
cp "$HERE/terminal.mk-dl.spec" "$RPMBUILD_ROOT/SPECS/"

rpmbuild -bb "$RPMBUILD_ROOT/SPECS/terminal.mk-dl.spec"

find "$RPMBUILD_ROOT/RPMS" -name "terminal.mk-dl-*.rpm" -exec cp {} "$OUT_DIR/" \;
echo "Built RPM(s) copied to: $OUT_DIR"
