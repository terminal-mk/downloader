#!/usr/bin/env bash
# Usage: build_deb.sh <path-to-cli-binary> <path-to-gui-binary>
# Assembles packaging/debian into a full package tree and runs dpkg-deb.
set -euo pipefail

BIN_PATH="${1:?Usage: build_deb.sh <path-to-cli-binary> <path-to-gui-binary>}"
GUI_BIN_PATH="${2:?Usage: build_deb.sh <path-to-cli-binary> <path-to-gui-binary>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/.."          # packaging/
PKG_SRC="$ROOT/debian"   # packaging/debian (control, postinst live here)
OUT_DIR="$ROOT/out"
STAGE="$ROOT/.stage-deb"

rm -rf "$STAGE"
mkdir -p "$STAGE/DEBIAN" "$STAGE/usr/bin" "$STAGE/usr/share/icons/hicolor/256x256/apps" "$OUT_DIR"

cp "$PKG_SRC/DEBIAN/control" "$STAGE/DEBIAN/control"
cp "$PKG_SRC/DEBIAN/postinst" "$STAGE/DEBIAN/postinst"
cp "$PKG_SRC/DEBIAN/prerm" "$STAGE/DEBIAN/prerm"
chmod 755 "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/prerm"

cp "$BIN_PATH" "$STAGE/usr/bin/terminal.mk-dl"
chmod 755 "$STAGE/usr/bin/terminal.mk-dl"
cp "$GUI_BIN_PATH" "$STAGE/usr/bin/terminal.mk-dl-gui"
chmod 755 "$STAGE/usr/bin/terminal.mk-dl-gui"

cp "$PKG_SRC/icons/terminal.mk-dl.png" "$STAGE/usr/share/icons/hicolor/256x256/apps/terminal.mk-dl.png"

VERSION="$(grep '^Version:' "$PKG_SRC/DEBIAN/control" | awk '{print $2}')"
OUT_FILE="$OUT_DIR/terminal.mk-dl_${VERSION}_amd64.deb"

# xz: newer dpkg-deb defaults to zstd on some distros, which Debian 11 can't read.
dpkg-deb --build -Zxz --root-owner-group "$STAGE" "$OUT_FILE"
echo "Built: $OUT_FILE"
