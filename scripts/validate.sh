#!/usr/bin/env bash
# Build in a fresh Arch container without installing the application on the host.
set -euo pipefail
cd "$(dirname "$0")/.."
docker run --rm -v "$PWD":/pkg:ro archlinux:base-devel bash -c '
  set -euo pipefail
  pacman -Syu --needed --noconfirm python squashfs-tools desktop-file-utils sudo >/dev/null
  useradd -m builder
  echo "builder ALL=(ALL) NOPASSWD: /usr/bin/pacman" > /etc/sudoers.d/builder
  cp -a /pkg /tmp/build
  chown -R builder:builder /tmp/build
  su builder -c "cd /tmp/build && desktop-file-validate pen-dev.desktop && makepkg --printsrcinfo > /tmp/generated.SRCINFO && diff -u .SRCINFO /tmp/generated.SRCINFO && makepkg --syncdeps --noconfirm --cleanbuild"
  cp /etc/makepkg.conf /tmp/makepkg-arm.conf
  echo "CARCH=aarch64" >> /tmp/makepkg-arm.conf
  # These packages only copy upstream binaries; no ARM code is executed.
  su builder -c "cd /tmp/build && makepkg --config /tmp/makepkg-arm.conf --nodeps --noconfirm --cleanbuild"
'
