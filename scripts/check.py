#!/usr/bin/env python3
"""Check reproducibility and links without third-party dependencies."""
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.links = []
        self.headings = 0
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1':
            self.headings += 1
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        for name in ('href', 'src'):
            if name in attrs:
                self.links.append(attrs[name])

before = {p: p.read_bytes() for p in ROOT.glob('*.html')}
subprocess.run([sys.executable, str(ROOT / 'scripts/build.py')], check=True)
assert before == {p: p.read_bytes() for p in ROOT.glob('*.html')}, 'Generated HTML is stale; regenerate and review it'
pages = {p: Page(p.read_text()) for p in ROOT.glob('*.html')}
for path, page in pages.items():
    assert page.headings == 1, f'{path.name}: expected one main heading'
    assert len(page.ids) == len(set(page.ids)), f'{path.name}: duplicate IDs'
    for link in page.links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        target = path.parent / unquote(url.path) if url.path else path
        assert target.is_file(), f'{path.name}: missing {link}'
        if url.fragment and target in pages:
            assert unquote(url.fragment) in pages[target].ids, f'{path.name}: missing anchor {link}'
print(f'PASS: {len(pages)} pages, internal links and anchors, unique IDs, and reproducible generation.')
