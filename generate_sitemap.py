#!/usr/bin/env python3
"""Generate a sitemap from indexable HTML pages in a static GitHub Pages repo.

Run at the website repository root:
    python3 generate_sitemap.py

Optional:
    python3 generate_sitemap.py --root /path/to/repo

Notes:
* No network requests; validate published URLs with Search Console after deployment.
* <lastmod> is the file's last git commit date (today if it has uncommitted edits);
  it is omitted when the repo has no git history. Use --no-lastmod to disable.
* Include same-host pages maintained in other repos via seo-extra-urls.txt.
"""
import argparse
import csv
import datetime
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, urljoin
import xml.etree.ElementTree as ET

BASE = 'https://bhagyesh-chokhawala.github.io/'
SKIP_NAMES = {'404.html', 'navigation-blog-link.html', 'preview.html', 'pdf_viewer.html', 'active-inference-recommender-pdf-viewer.html'}
# 'dist' is intentionally not skipped: the Elastic Scaling Planner is served from dist/.
# 'tools' holds templates and unpublished build output; 'static' is an app asset folder.
SKIP_PARTS = {'.git', '.github', 'node_modules', 'vendor', 'build', '__pycache__', '.venv', 'tools', 'static'}

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ''
        self.description = ''
        self.robots = ''
        self.canonical = ''
        self.has_h1 = False
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title':
            self._in_title = True
        if tag == 'h1':
            self.has_h1 = True
        if tag == 'meta':
            name = (attrs.get('name') or '').lower()
            if name == 'description': self.description = attrs.get('content', '').strip()
            if name in ('robots', 'googlebot'):
                self.robots += ' ' + attrs.get('content', '').lower()
        if tag == 'link' and 'canonical' in (attrs.get('rel') or '').lower().split():
            self.canonical = (attrs.get('href') or '').strip()

    def handle_data(self, data):
        if self._in_title:
            self.title += data

    def handle_endtag(self, tag):
        if tag == 'title': self._in_title = False


def url_from_file(path, root):
    rel = path.relative_to(root).as_posix()
    if rel == 'index.html': return BASE
    if rel.endswith('/index.html'):
        return urljoin(BASE, rel[:-len('index.html')])
    return urljoin(BASE, rel)


def clean_site_url(url):
    parts = urlparse(url)
    base = urlparse(BASE)
    if parts.scheme != 'https' or parts.netloc.lower() != base.netloc.lower():
        return None
    if parts.query or parts.fragment or not parts.path.startswith('/'):
        return None
    return parts.geturl()


def git_lastmod(root, rel):
    try:
        status = subprocess.run(['git', 'status', '--porcelain', '--', rel], cwd=root, capture_output=True, text=True, check=True).stdout
        if status.strip():
            return datetime.date.today().isoformat()
        out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', rel], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        return out or None
    except (OSError, subprocess.CalledProcessError):
        return None


def collect(root):
    rows = []
    sources = {}
    discovered = set()
    for path in sorted(root.rglob('*.html')):
        rel = path.relative_to(root)
        if path.name in SKIP_NAMES or path.name.startswith('google') and path.name.endswith('.html') or any(p in SKIP_PARTS for p in rel.parts):
            continue
        if path.is_symlink():
            continue
        url = url_from_file(path, root)
        parser = MetaParser()
        try:
            parser.feed(path.read_text(encoding='utf-8'))
        except Exception as ex:
            rows.append([str(rel), 'PARSE_ERROR', '', '', '', str(ex)])
            continue
        canonical = urljoin(url, parser.canonical) if parser.canonical else ''
        problems = []
        if not parser.title.strip(): problems.append('missing title')
        if not parser.description: problems.append('missing meta description')
        if not parser.has_h1: problems.append('missing H1')
        if not parser.canonical: problems.append('missing canonical')
        if 'noindex' in parser.robots: problems.append('noindex')
        if canonical and canonical != url: problems.append('canonical points elsewhere')
        if canonical and clean_site_url(canonical) is None: problems.append('canonical outside site or noncanonical')
        if 'noindex' in parser.robots or (canonical and canonical != url):
            status = 'EXCLUDED'
        else:
            status = 'INCLUDED'
            discovered.add(url)
            sources[url] = rel.as_posix()
        rows.append([str(rel), status, url, canonical, parser.title.strip(), '; '.join(problems)])
    extra = root / 'seo-extra-urls.txt'
    if extra.exists():
        for line in extra.read_text(encoding='utf-8').splitlines():
            url = line.strip()
            if not url or url.startswith('#'): continue
            clean = clean_site_url(url)
            if clean:
                discovered.add(clean)
                rows.append(['seo-extra-urls.txt', 'INCLUDED_EXTERNAL_UNCHECKED', clean, '', '', 'Verify canonical, HTTP 200 and indexability after deployment'])
            else:
                rows.append(['seo-extra-urls.txt', 'REJECTED', url, '', '', 'Not an absolute same-host HTTPS URL'])
    return sorted(discovered, key=lambda u: (u != BASE, u.lower())), rows, sources


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-lastmod', action='store_true', help='Omit <lastmod>')
    ap.add_argument('--root', type=Path, default=Path('.'), help='Website repository root')
    args = ap.parse_args()
    root = args.root.resolve()
    urls, rows, sources = collect(root)
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', ns)
    urlset = ET.Element(f'{{{ns}}}urlset')
    for u in urls:
        item = ET.SubElement(urlset, f'{{{ns}}}url')
        ET.SubElement(item, f'{{{ns}}}loc').text = u
        lastmod = None if args.no_lastmod or u not in sources else git_lastmod(root, sources[u])
        if lastmod:
            ET.SubElement(item, f'{{{ns}}}lastmod').text = lastmod
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space='  ')
    tree.write(root / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    with (root / 'seo-validation.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['file', 'status', 'url', 'canonical', 'title', 'issues'])
        w.writerows(rows)
    print(f'Wrote {root / "sitemap.xml"}: {len(urls)} URLs')
    print(f'Wrote {root / "seo-validation.csv"}: {len(rows)} checks')
    print('Before publishing: review seo-validation.csv and verify HTTP 200, canonical and indexability.')

if __name__ == '__main__':
    main()
