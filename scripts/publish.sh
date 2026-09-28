#!/usr/bin/env bash
# Copy only AUR packaging files into its independent Git history.
set -euo pipefail
cd "$(dirname "$0")/.."
pkgname=$(sed -n 's/^pkgname=//p' PKGBUILD)
version=$(sed -n 's/^pkgver=//p' PKGBUILD)
revision=$(sed -n 's/^pkgrel=//p' PKGBUILD)
case "$pkgname" in pen-dev-bin|pen-dev-appimage) ;; *) exit 1 ;; esac
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
git clone "ssh://aur@aur.archlinux.org/$pkgname.git" "$work/aur"
files=(PKGBUILD .SRCINFO pen-dev.desktop pen-dev.png LICENSE)
if [[ $pkgname == pen-dev-appimage ]]; then files+=(extract-appimage.py); fi
cp "${files[@]}" "$work/aur/"
cd "$work/aur"
git config user.name "${COMMIT_NAME:-Arnaud Gissinger}"
git config user.email "${COMMIT_EMAIL:-agissing@student.42.fr}"
git add "${files[@]}"
if git diff --cached --quiet; then
  echo 'AUR already up to date.'
  exit 0
fi
git commit -m "Update $pkgname to $version-$revision"
git push origin HEAD:master
