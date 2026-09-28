import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('updater', ROOT / 'scripts/update.py')
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class UpdateTests(unittest.TestCase):
    def fixture(self, variant='bin', version='1.2.15'):
        text = (ROOT / 'PKGBUILD').read_text()
        import re
        text = re.sub(r'^pkgname=.*$', f'pkgname=pen-dev-{variant}', text, flags=re.M)
        text = re.sub(r'^pkgver=.*$', 'pkgver=1.2.14', text, flags=re.M)
        text = re.sub(r'^pkgrel=.*$', 'pkgrel=3', text, flags=re.M)
        extension = 'tar.gz' if variant == 'bin' else 'AppImage'
        assets = []
        for arch in ('x64' if variant == 'bin' else 'x86_64', 'arm64'):
            name = f'Pen-{version}-linux-{arch}.{extension}'
            assets.append({'name': name, 'digest': 'sha256:' + 'a' * 64,
                           'browser_download_url': f'https://github.com/highagency/pen-desktop-releases/releases/download/v{version}/{name}'})
        return text, {'tag_name': f'v{version}', 'draft': False, 'prerelease': False, 'assets': assets}

    def test_both_variants_update_both_architectures(self):
        for variant in ('bin', 'appimage'):
            with self.subTest(variant=variant):
                text, release = self.fixture(variant)
                result = updater.updated_pkgbuild(text, release)
                self.assertIn('pkgver=1.2.15\npkgrel=1\n', result)
                self.assertEqual(result.count("=('" + 'a' * 64 + "')"), 2)
                self.assertEqual(updater.updated_pkgbuild(result, release), result)

    def test_missing_arm_asset_rejected(self):
        text, release = self.fixture()
        release['assets'].pop()
        with self.assertRaises(KeyError):
            updater.updated_pkgbuild(text, release)

    def test_missing_digest_rejected(self):
        text, release = self.fixture()
        release['assets'][0]['digest'] = None
        with self.assertRaises((ValueError, TypeError)):
            updater.updated_pkgbuild(text, release)

    def test_unexpected_download_host_rejected(self):
        text, release = self.fixture()
        release['assets'][0]['browser_download_url'] = 'https://example.com/file'
        with self.assertRaises(ValueError):
            updater.updated_pkgbuild(text, release)

    def test_downgrade_rejected(self):
        text, release = self.fixture(version='1.2.13')
        with self.assertRaises(ValueError):
            updater.updated_pkgbuild(text, release)

    def test_unstable_release_rejected(self):
        text, release = self.fixture()
        release['prerelease'] = True
        with self.assertRaises(ValueError):
            updater.updated_pkgbuild(text, release)

    def test_rebuilt_release_bumps_revision_once(self):
        text, release = self.fixture(version='1.2.14')
        result = updater.updated_pkgbuild(text, release)
        self.assertIn('pkgver=1.2.14\npkgrel=4\n', result)
        self.assertEqual(updater.updated_pkgbuild(result, release), result)


if __name__ == '__main__':
    unittest.main()
