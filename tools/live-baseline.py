#!/usr/bin/env python3
"""Capture public HTML privately, create editable live-based drafts, freeze new vNN.

Run from any cwd. Never writes WordPress or existing current/vNN directories.
Capture files contain public HTML but are kept OUTSIDE this public repository.
The published base.html is a sanitized template, not an authenticated backup.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import shutil
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'tools/live-baseline.json').read_text())
PAGES = CONFIG['pages']
SLOT = '<!-- LIVE-BASELINE:BODY -->'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def capture_assets(directory):
    directory = directory.resolve()
    assert ROOT not in directory.parents and directory != ROOT
    assert (directory / 'manifest.json').is_file(), 'capture HTML first'
    assets = directory / 'assets'
    assets.mkdir(exist_ok=False)
    sources = json.loads((ROOT / 'tools/wp/manifest.json').read_text())
    def download(item):
        url = item['url']
        assert url.startswith('https://skym.co.jp/wp20150417/wp-content/uploads/')
        name = item['upload_name']
        assert pathlib.Path(name).name == name
        with urllib.request.urlopen(url, timeout=45) as response:
            data = response.read()
        (assets / name).write_bytes(data)
        return {'url': url, 'file': name, 'bytes': len(data), 'sha256': digest(data),
                'matches_v01': hashlib.md5(data).hexdigest() == item['md5']}
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(download, sources))
    json_write(directory / 'assets-manifest.json', {'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'assets': results})
    print('saved assets:', len(results), 'matches_v01:', sum(x['matches_v01'] for x in results))


def capture(directory):
    directory = directory.resolve()
    assert ROOT not in directory.parents and directory != ROOT, 'private capture must be outside mockup'
    directory.mkdir(parents=True, exist_ok=False)
    manifest = {'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pages': {}}
    for page, cfg in PAGES.items():
        url = 'https://skym.co.jp' + cfg['path']
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
            assert response.status == 200 and response.url.rstrip('/') == url.rstrip('/'), url
        html = data.decode('utf-8')
        assert 'id="' + cfg['root'] + '"' in html and 'id="wpadminbar"' not in html
        (directory / (page + '.html')).write_bytes(data)
        manifest['pages'][page] = {'url': url, 'sha256': digest(data), 'bytes': len(data)}
        json_write(directory / 'manifest.json', manifest)
        print('captured', page, len(data))


class RootSpan(HTMLParser):
    """Find the exact source span without reserializing/normalizing HTML."""
    def __init__(self, source, target):
        super().__init__(convert_charrefs=False)
        self.source, self.target = source, target
        self.lines = [0]
        for match in re.finditer('\n', source):
            self.lines.append(match.end())
        self.start = self.end = None
        self.depth = 0
        self.feed(source)
        assert self.start is not None and self.end is not None, target

    def source_offset(self):
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag != 'div':
            return
        if dict(attrs).get('id') == self.target:
            assert self.start is None, 'duplicate root'
            self.start = self.source_offset()
            self.depth = 1
        elif self.depth:
            self.depth += 1

    def handle_endtag(self, tag):
        if tag == 'div' and self.depth:
            self.depth -= 1
            if not self.depth:
                self.end = self.source.index('>', self.source_offset()) + 1


def sanitize(source):
    assert 'id="wpadminbar"' not in source
    source, n = re.subn(
        r'<script src="http://zipaddr\.googlecode\.com/svn/trunk/zipaddr7\.js".*?set_script\(cid\);\s*// -->\s*</script>',
        '<!-- MOCK: tracking and obsolete zipaddr scripts removed -->', source, flags=re.S)
    assert n == 1, 'tracking block changed; inspect before publishing'
    source, n = re.subn(
        r"href='https://skym\.co\.jp/wp20150417/wp-content/(themes/Zephyr/css/font-awesome\.css|themes/Zephyr/css/font-mdfi\.css|plugins/Ultimate_VC_Addons/assets/min-css/ultimate\.min\.css|uploads/smile_fonts/Defaults/Defaults\.css)\?ver=[^']*'",
        r"href='../../assets/wp-content/\1'", source)
    assert n == 4, 'font CSS mapping changed'
    # Attributes rooted on the live origin need an absolute URL on localhost/Pages.
    source = re.sub(r'''\b(src|href|poster)=(['"])(/[^/'"][^'"]*|/)\2''',
                    lambda m: m[1] + '=' + m[2] + 'https://skym.co.jp' + m[3] + m[2], source)
    source = re.sub(r'<meta\b[^>]*name=[\'"]robots[\'"][^>]*>', '', source, flags=re.I)
    source = source.replace('</head>', '<meta name="robots" content="noindex, nofollow">\n</head>', 1)
    assert not re.search(r'zipaddr7\.js|_gaq|yahoo_retargeting|google_conversion|set_script|analyzer1\.apps', source)
    return source


def initialize(page, directory):
    cfg = PAGES[page]
    target = ROOT / page / cfg['draft']
    assert not target.exists(), 'draft exists; refusing reinitialization'
    raw = (directory / (page + '.html')).read_bytes()
    captured = json.loads((directory / 'manifest.json').read_text())
    assert digest(raw) == captured['pages'][page]['sha256']
    html = sanitize(raw.decode('utf-8'))
    span = RootSpan(html, cfg['root'])
    block = html[span.start:span.end]
    base = html[:span.start] + SLOT + html[span.end:]
    assert base.count(SLOT) == 1
    target.mkdir()
    (target / 'base.html').write_text(base)
    (target / 'block.html').write_text(block)
    # Retain original page-setting metadata for future WP payload conversion.
    settings = json.loads((ROOT / 'tools/wp' / (page + '.settings.json')).read_text())
    settings.update({'source': 'public-live', 'captured_at': captured['captured_at'],
                     'live_url': captured['pages'][page]['url'], 'raw_sha256': digest(raw),
                     'builder': 'tools/live-baseline.py',
                     'limitations': 'External CSS/JS/media remain live dependencies; not a complete WordPress backup.'})
    settings.pop('post_sha256', None)
    json_write(target / 'baseline.json', settings)
    build(page, cfg['draft'], 'draft')


def rendered(page, directory, links):
    assert links == 'draft' or re.fullmatch(r'v[0-9]{2,}', links), 'invalid link version'
    base = (directory / 'base.html').read_text()
    assert base.count(SLOT) == 1
    html = base.replace(SLOT, (directory / 'block.html').read_text())
    by_path = {v['path'].rstrip('/'): k for k, v in PAGES.items()}
    def replace(match):
        parsed = urllib.parse.urlsplit(match[2])
        dest = by_path.get(parsed.path.rstrip('/'))
        if parsed.hostname != 'skym.co.jp' or dest is None or parsed.query:
            return match[0]
        version = PAGES[dest]['draft'] if links == 'draft' else links
        return 'href=' + match[1] + '../../' + dest + '/' + version + '/' + ('#' + parsed.fragment if parsed.fragment else '') + match[1]
    html = re.sub(r'''href=(['"])(https?://skym\.co\.jp[^'"]*)\1''', replace, html)
    return html


def build(page, draft, links):
    assert re.fullmatch(r'draft[1-9][0-9]*', draft), 'only draft may be rebuilt'
    directory = ROOT / page / draft
    (directory / 'index.html').write_text(rendered(page, directory, links))
    print('built', page, draft, 'links=' + links)


def freeze(page, version):
    assert re.fullmatch(r'v[0-9]{2,}', version)
    source = ROOT / page / PAGES[page]['draft']
    target = ROOT / page / version
    assert not target.exists(), 'frozen destination already exists'
    target.mkdir()
    for name in ['base.html', 'block.html', 'baseline.json']:
        shutil.copyfile(source / name, target / name)
    (target / 'index.html').write_text(rendered(page, target, version))
    print('frozen', page, version)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('capture'); p.add_argument('directory', type=pathlib.Path)
    p = sub.add_parser('assets'); p.add_argument('directory', type=pathlib.Path)
    p = sub.add_parser('init'); p.add_argument('page', choices=PAGES); p.add_argument('directory', type=pathlib.Path)
    p = sub.add_parser('build'); p.add_argument('page', choices=PAGES); p.add_argument('draft'); p.add_argument('--links', default='draft')
    p = sub.add_parser('freeze'); p.add_argument('page', choices=PAGES); p.add_argument('version')
    args = parser.parse_args()
    if args.command == 'capture': capture(args.directory)
    elif args.command == 'assets': capture_assets(args.directory)
    elif args.command == 'init': initialize(args.page, args.directory)
    elif args.command == 'build': build(args.page, args.draft, args.links)
    else: freeze(args.page, args.version)
