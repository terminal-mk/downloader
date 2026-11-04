#!/bin/sh
# Installs the built package in a clean distro container and checks that both
# binaries start. Takes no network and no extra packages on purpose: anything
# the binaries are missing should fail here rather than on a user's machine.
#
#   docker run --rm --network none -e DISPLAY=:99 -v /tmp/.X11-unix:/tmp/.X11-unix \
#     -v "$PWD:/src:ro" <image> sh /src/build_scripts/test_in_distro.sh
set -eu
cd /src/packaging/out

. /etc/os-release
echo "== $PRETTY_NAME"

if command -v dpkg >/dev/null 2>&1; then
  dpkg -i terminal.mk-dl_*_amd64.deb
elif command -v rpm >/dev/null 2>&1 && [ "$ID" != arch ]; then
  # --nosignature: the package is unsigned, which newer rpm rejects by default.
  rpm -i --nosignature terminal.mk-dl-*.x86_64.rpm
else
  mkdir -p /tmp/extract
  tar -xzf terminal.mk-dl-*-linux-x86_64.tar.gz -C /tmp/extract
  cp /tmp/extract/*/terminal.mk-dl /tmp/extract/*/terminal.mk-dl-gui /usr/bin/
fi

terminal.mk-dl --help >/dev/null
terminal.mk-dl-gui --self-test
echo "OK: $PRETTY_NAME"
