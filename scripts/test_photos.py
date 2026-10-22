#!/usr/bin/env python3
"""Exercise photo approval, local paths, WebP checks, escaping, and credits."""
import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('build', Path(__file__).with_name('build.py'))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

class Photos(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.old_root, self.old_hikes = build.ROOT, build.HIKES
        self.addCleanup(self.restore)
        build.ROOT = Path(self.temp.name)
        image = build.ROOT / 'assets/photos/test.webp'
        image.parent.mkdir(parents=True)
        # Synthetic WebP header: no third-party photograph is used by these tests.
        image.write_bytes(b'RIFF'+(22).to_bytes(4,'little')+b'WEBPVP8X'+(10).to_bytes(4,'little')+bytes(10))
        self.photo = dict(src='assets/photos/test.webp', alt='View <test>', title='A & B', photographer='Creator <name>', source_url='https://example.org/photo', license='Written permission', license_url='https://example.org/permission', modifications='Converted to WebP', rights_evidence='Owner approval record', approved=True)

    def restore(self):
        build.ROOT, build.HIKES = self.old_root, self.old_hikes

    def test_credit_and_render(self):
        h = dict(slug='test', title='Test hike', photo=self.photo)
        build.HIKES = [h]
        html = build.hike_photo(h)
        self.assertIn('Creator &lt;name&gt;', html)
        self.assertIn('width="1" height="1"', html)
        self.assertIn('loading="lazy"', html)
        self.assertIn('https://example.org/permission', html)
        self.assertIn('Converted to WebP', build.photo_credits())

    def test_reject_incomplete_unapproved_external_and_oversized(self):
        for field, value in [('approved', False), ('photographer', ''), ('rights_evidence', ''), ('src', 'https://example.org/a.webp'), ('src', 'assets/photos/../test.webp'), ('license_url', 'javascript:alert(1)')]:
            photo = copy.deepcopy(self.photo); photo[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(AssertionError):
                build.validate_photo(photo)
        image = build.ROOT / self.photo['src']
        image.write_bytes(image.read_bytes() + bytes(400_001))
        with self.assertRaises(AssertionError): build.validate_photo(self.photo)

    def test_placeholder_and_empty_credits(self):
        build.HIKES = []
        self.assertIn('No trail photographs', build.photo_credits())
        self.assertIn('not a photograph', build.hike_photo(dict(photo=None, art='lake')))

if __name__ == '__main__': unittest.main()
