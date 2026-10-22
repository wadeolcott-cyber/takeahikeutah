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
        self.assertIn('photo-credits.html#photo-test', html)
        self.assertNotIn('Modifications:', html)
        self.assertIn('https://example.org/permission', build.photo_credits())
        self.assertIn('Converted to WebP', build.photo_credits())

    def test_reject_incomplete_unapproved_external_and_oversized(self):
        for field, value in [('approved', False), ('photographer', ''), ('rights_evidence', ''), ('src', 'https://example.org/a.webp'), ('src', 'assets/photos/../test.webp'), ('license_url', 'javascript:alert(1)')]:
            photo = copy.deepcopy(self.photo); photo[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(AssertionError):
                build.validate_photo(photo)
        image = build.ROOT / self.photo['src']
        image.write_bytes(image.read_bytes() + bytes(400_001))
        with self.assertRaises(AssertionError): build.validate_photo(self.photo)

    def test_gallery_credits_and_card_photo(self):
        h = dict(slug='test', title='Test hike', photo=self.photo, additional_photos=[dict(self.photo, title='Second view')])
        build.HIKES = [h]
        self.assertEqual(build.hike_photo(h).count('<figure'), 2)
        self.assertIn('Second view', build.photo_credits())
        h.update(experience='first-steps', landscapes=[], seasons=[], terrain=[], distance_miles=None, elevation_gain_feet=None, status='reviewed', subtitle='Location', description='Guide', art='lake')
        html = build.card(h, 1)
        self.assertIn('class="card-photo"', html)
        self.assertNotIn('Illustration · photo placeholder', html)

    def test_compact_sharealike_credit(self):
        self.photo.update(license='CC BY-SA 4.0', license_url='https://creativecommons.org/licenses/by-sa/4.0/')
        html = build.hike_photo(dict(photo=self.photo))
        self.assertIn('https://creativecommons.org/licenses/by-sa/4.0/', html)
        self.assertIn('https://example.org/photo', html)
        self.assertIn('WebP conversion', html)
        self.assertIn('photo-credits.html#photo-test', html)

    def test_sharealike_2_and_regional_card_label(self):
        self.photo.update(license='CC BY-SA 2.0 — original and derivative', license_url='https://creativecommons.org/licenses/by-sa/2.0/', card_note='Park view · not trail-specific')
        html = build.compact_photo_credit(self.photo)
        self.assertIn('CC BY-SA 2.0</a>', html)
        self.assertIn('A &amp; B', html)
        h = dict(slug='park', title='Park', photo=self.photo, experience='first-steps', landscapes=[], seasons=[], terrain=[], distance_miles=None, elevation_gain_feet=None, status='reviewed', subtitle='Location', description='Guide', art='lake')
        self.assertIn('Park view · not trail-specific', build.card(h, 1))

    def test_placeholder_and_empty_credits(self):
        build.HIKES = []
        self.assertIn('No trail photographs', build.photo_credits())
        self.assertIn('not a photograph', build.hike_photo(dict(photo=None, art='lake')))

if __name__ == '__main__': unittest.main()
