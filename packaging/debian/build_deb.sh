#!/usr/bin/env bash
# Usage: build_deb.sh <path-to-pyinstaller-binary>
# Assembles packaging/debian into a full package tree and runs dpkg-deb.
set -euo pipefail

BIN_PATH="${1:?Usage: build_deb.sh <path-to-pyinstaller-binary>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/.."          # packaging/
PKG_SRC="$ROOT/debian"   # packaging/debian (control, postinst live here)
OUT_DIR="$ROOT/out"
STAGE="$ROOT/.stage-deb"

rm -rf "$STAGE"
mkdir -p "$STAGE/DEBIAN" "$STAGE/usr/bin" "$OUT_DIR"

cp "$PKG_SRC/DEBIAN/control" "$STAGE/DEBIAN/control"
cp "$PKG_SRC/DEBIAN/postinst" "$STAGE/DEBIAN/postinst"
chmod 755 "$STAGE/DEBIAN/postinst"

cp "$BIN_PATH" "$STAGE/usr/bin/terminalmk-downloader"
chmod 755 "$STAGE/usr/bin/terminalmk-downloader"

VERSION="$(grep '^Version:' "$PKG_SRC/DEBIAN/control" | awk '{print $2}')"
OUT_FILE="$OUT_DIR/terminalmk-downloader_${VERSION}_amd64.deb"

dpkg-deb --build --root-owner-group "$STAGE" "$OUT_FILE"
echo "Built: $OUT_FILE"
