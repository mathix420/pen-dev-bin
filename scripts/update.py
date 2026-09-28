#!/usr/bin/env python3
"""Update PKGBUILD from the official stable release; never source remote code."""
import json
import os
from pathlib import Path
import re
import urllib.request


def updated_pkgbuild(text, release):
    if release.get('draft') or release.get('prerelease'):
        raise ValueError('Expected a stable release')
    match = re.fullmatch(r'v(\d+\.\d+\.\d+)', release['tag_name'])
    if not match:
        raise ValueError('Unexpected upstream version')
    version = match[1]
    current = re.search(r'^pkgver=(\d+\.\d+\.\d+)$', text, re.M)[1]
    if tuple(map(int, version.split('.'))) < tuple(map(int, current.split('.'))):
        raise ValueError('Refusing an upstream version downgrade')
    variant = re.search(r'^pkgname=pen-dev-(bin|appimage)$', text, re.M)[1]
    extension = 'tar.gz' if variant == 'bin' else 'AppImage'
    architectures = {'x86_64': 'x64' if variant == 'bin' else 'x86_64', 'aarch64': 'arm64'}
    assets = {a['name']: a for a in release['assets']}
    result = text
    for arch, upstream in architectures.items():
        filename = f'Pen-{version}-linux-{upstream}.{extension}'
        asset = assets[filename]  # Fail before writing if either architecture is missing.
        expected = f'https://github.com/highagency/pen-desktop-releases/releases/download/v{version}/{filename}'
        if asset['browser_download_url'] != expected:
            raise ValueError(f'Unexpected download URL for {filename}')
        digest = asset.get('digest') or ''
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
            raise ValueError(f'Missing SHA-256 digest for {filename}')
        result, count = re.subn(rf"^sha256sums_{arch}=\('[0-9a-f]{{64}}'\)$",
                                f"sha256sums_{arch}=('{digest[7:]}')", result, flags=re.M)
        if count != 1:
            raise ValueError(f'Expected one checksum for {arch}')
    if version != current:
        result = re.sub(r'^pkgver=.*$', f'pkgver={version}', result, flags=re.M)
        result = re.sub(r'^pkgrel=.*$', 'pkgrel=1', result, flags=re.M)
    elif result != text:
        revision = int(re.search(r'^pkgrel=(\d+)$', text, re.M)[1]) + 1
        result = re.sub(r'^pkgrel=.*$', f'pkgrel={revision}', result, flags=re.M)
    return result


def main():
    path = Path(__file__).resolve().parents[1] / 'PKGBUILD'
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'pen-dev-aur-updater'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    request = urllib.request.Request(
        'https://api.github.com/repos/highagency/pen-desktop-releases/releases/latest', headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        release = json.load(response)
    old = path.read_text()
    new = updated_pkgbuild(old, release)
    if new != old:
        path.write_text(new)
    print('Updated PKGBUILD' if new != old else 'Already up to date')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write(f'changed={str(new != old).lower()}\n')


if __name__ == '__main__':
    main()
