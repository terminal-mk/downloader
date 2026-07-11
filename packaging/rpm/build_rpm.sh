#!/usr/bin/env bash
# Usage: build_rpm.sh <path-to-pyinstaller-binary>
# Requires rpmbuild (Fedora/RHEL: sudo dnf install rpm-build).
set -euo pipefail

BIN_PATH="${1:?Usage: build_rpm.sh <path-to-pyinstaller-binary>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="$HERE/../out"
RPMBUILD_ROOT="$HOME/rpmbuild"

mkdir -p "$RPMBUILD_ROOT/SOURCES" "$RPMBUILD_ROOT/SPECS" "$OUT_DIR"
cp "$BIN_PATH" "$RPMBUILD_ROOT/SOURCES/terminalmk-downloader"
cp "$HERE/terminalmk-downloader.spec" "$RPMBUILD_ROOT/SPECS/"

rpmbuild -bb "$RPMBUILD_ROOT/SPECS/terminalmk-downloader.spec"

find "$RPMBUILD_ROOT/RPMS" -name "terminalmk-downloader-*.rpm" -exec cp {} "$OUT_DIR/" \;
echo "Built RPM(s) copied to: $OUT_DIR"
