#!/usr/bin/env python3
"""Discover public Cloudflare Pages HTML and generate SEO files (stdlib only)."""
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://takeahikeutah.org'
NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
PRIVATE = {'templates', 'docs', 'scripts', 'data', 'assets', 'tests', 'work', 'output'}


class Metadata(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.excluded = False
        self.canonical = None
        self.modified = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            name = attrs.get('name', '').lower()
            content = attrs.get('content', '')
            if name in {'robots', 'googlebot'} and {'noindex', 'none'} & set(content.lower().replace(',', ' ').split()):
                self.excluded = True
            if attrs.get('http-equiv', '').lower() == 'refresh':
                self.excluded = True
            if name == 'date-modified':
                # Explicit editorial date only; never file mtimes or build dates.
                self.modified = date.fromisoformat(content).isoformat()
        if tag == 'link' and 'canonical' in attrs.get('rel', '').lower().split():
            self.canonical = attrs.get('href')


def page_url(path):
    relative = path.relative_to(ROOT).as_posix()
    if relative == 'index.html':
        return DOMAIN + '/'
    if relative.endswith('/index.html'):
        relative = relative[:-10]
    else:
        relative = relative[:-5]
    return DOMAIN + '/' + quote(relative, safe='/')


def entries():
    result = {}
    for path in sorted(ROOT.rglob('*.html')):
        parts = path.relative_to(ROOT).parts
        if any(part.startswith(('.', '_')) or part in PRIVATE for part in parts[:-1]) or path.name in {'404.html', '500.html'}:
            continue
        meta = Metadata(path.read_text(encoding='utf-8'))
        url = page_url(path)
        if meta.excluded or (meta.canonical and meta.canonical != url):
            continue
        assert urlsplit(url).netloc == 'takeahikeutah.org'
        assert url not in result, f'Duplicate public URL: {url}'
        result[url] = meta.modified
    return result


def generate():
    ET.register_namespace('', NS)
    root = ET.Element(f'{{{NS}}}urlset')
    for url, modified in entries().items():
        node = ET.SubElement(root, f'{{{NS}}}url')
        ET.SubElement(node, f'{{{NS}}}loc').text = url
        if modified:
            ET.SubElement(node, f'{{{NS}}}lastmod').text = modified
    ET.indent(root, space='  ')
    ET.ElementTree(root).write(ROOT / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    with (ROOT / 'sitemap.xml').open('a') as target:
        target.write('\n')
    robots = ROOT / 'robots.txt'
    lines = robots.read_text().splitlines() if robots.exists() else ['User-agent: *', 'Allow: /', '']
    lines = [line for line in lines if not line.lower().startswith('sitemap:')]
    robots.write_text('\n'.join(lines).rstrip() + '\n\nSitemap: ' + DOMAIN + '/sitemap.xml\n')
    print(f'Generated sitemap.xml with {len(root)} indexable URLs and robots.txt.')


if __name__ == '__main__':
    generate()
