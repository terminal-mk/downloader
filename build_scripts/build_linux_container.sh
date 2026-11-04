#!/usr/bin/env bash
# Builds the distributable Linux binaries on AlmaLinux 8, whose glibc 2.28 is
# older than every supported mainstream distro's. Run it inside the container:
#
#   docker run --rm -v "$PWD:/src" almalinux:8 bash /src/build_scripts/build_linux_container.sh
#
# then package the result on any machine: build_scripts/build_linux.sh packages
set -euo pipefail
cd "$(dirname "$0")/.."

# libXcursor: needed by the tkdnd native library, not pulled in by Tk itself.
dnf -y install python3.11 python3.11-pip python3.11-tkinter binutils libXcursor

PYTHON=python3.11 bash build_scripts/build_linux.sh binaries

# The container runs as root; hand the output back to whoever owns the checkout.
chown -R "$(stat -c '%u:%g' .)" dist build .venv-build
