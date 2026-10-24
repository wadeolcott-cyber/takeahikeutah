#!/usr/bin/env python3
"""Test discovery, exclusions, dates, and the actual sitemap's file targets."""
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import sitemap


class SitemapTests(unittest.TestCase):
    def test_discovery(self):
        original = sitemap.ROOT
        with tempfile.TemporaryDirectory() as directory:
            sitemap.ROOT = Path(directory)
            try:
                fixtures = {
                    'index.html': '<h1>Home</h1>',
                    'new-hike.html': '<meta name="date-modified" content="2026-01-02">',
                    'draft.html': '<meta name="robots" content="noindex, follow">',
                    'redirect.html': '<meta http-equiv="refresh" content="0;url=/">',
                    'duplicate.html': '<link rel="canonical" href="https://takeahikeutah.org/">',
                    'templates/page.html': '<h1>Template</h1>',
                    '404.html': '<h1>Missing</h1>',
                    'guides/index.html': '<h1>Guides</h1>',
                }
                for name, content in fixtures.items():
                    path = sitemap.ROOT / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content)
                sitemap.generate()
                self.assertEqual(sitemap.entries(), {
                    sitemap.DOMAIN + '/': None,
                    sitemap.DOMAIN + '/new-hike': '2026-01-02',
                    sitemap.DOMAIN + '/guides/': None,
                })
                first = (sitemap.ROOT / 'sitemap.xml').read_bytes()
                sitemap.generate()
                self.assertEqual(first, (sitemap.ROOT / 'sitemap.xml').read_bytes())
                self.assertEqual((sitemap.ROOT / 'robots.txt').read_text().count('Sitemap:'), 1)
            finally:
                sitemap.ROOT = original

    def test_generated_xml_and_targets(self):
        root = ET.parse(sitemap.ROOT / 'sitemap.xml').getroot()
        self.assertEqual(root.tag, '{' + sitemap.NS + '}urlset')
        urls = [node.text for node in root.findall('{*}url/{*}loc')]
        self.assertEqual(set(urls), set(sitemap.entries()))
        self.assertEqual(len(urls), len(set(urls)))
        for url in urls:
            parsed = urlsplit(url)
            self.assertEqual(parsed.scheme + '://' + parsed.netloc, sitemap.DOMAIN)
            self.assertFalse(parsed.query or parsed.fragment)
            relative = unquote(parsed.path).lstrip('/')
            # Cloudflare Pages serves extensionless HTML and directory indexes.
            target = relative + 'index.html' if not relative or relative.endswith('/') else relative + '.html'
            self.assertTrue((sitemap.ROOT / target).is_file(), url)
        self.assertIn('Sitemap: ' + sitemap.DOMAIN + '/sitemap.xml', (sitemap.ROOT / 'robots.txt').read_text())


if __name__ == '__main__':
    unittest.main()
