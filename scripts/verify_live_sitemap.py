#!/usr/bin/env python3
"""Verify deployed SEO files and every listed URL, without following redirects."""
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET
from sitemap import DOMAIN, ROOT, NS


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


opener = build_opener(NoRedirect)
def fetch(url):
    with opener.open(Request(url, headers={'User-Agent': 'TakeAHikeUtah-SitemapCheck/1.0'}), timeout=30) as response:
        assert response.status == 200, f'{url}: {response.status}'
        return response.read()


live = fetch(DOMAIN + '/sitemap.xml')
root = ET.fromstring(live)
assert root.tag == '{' + NS + '}urlset', 'Invalid sitemap namespace'
assert live == (ROOT / 'sitemap.xml').read_bytes(), 'Deployed sitemap differs from local build'
assert ('Sitemap: ' + DOMAIN + '/sitemap.xml') in fetch(DOMAIN + '/robots.txt').decode()
urls = [loc.text for loc in root.findall('{*}url/{*}loc')]
assert len(urls) == len(set(urls)), 'Duplicate URLs'
for url in urls:
    assert url.startswith(DOMAIN + '/'), f'Noncanonical URL: {url}'
    fetch(url)
    print('200', url)
print(f'PASS: {len(urls)} page URLs and both root SEO files; no redirects.')
