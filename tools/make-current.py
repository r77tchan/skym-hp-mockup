#!/usr/bin/env python3
"""公開ページのスナップショットから <page>/current/index.html(現状再現版)を作る。

使い方: python3 tools/make-current.py <page> <url> <wp-page-id> [<source.html>]
  例:   python3 tools/make-current.py service https://skym.co.jp/service 6170
source を省略すると <page>/source/live-YYYY-MM-DD.html に取得する(既にあれば再利用)。
加工内容(top/current と同じ):
  ヘッダーコメント / noindex メタ / title に [snapshot] / フォント CSS 4 本を ../../assets/ に /
  計測・広告タグ(zipaddr, GA, Yahoo リタゲ, Google Ads, netowl analyzer)を除去 /
  相対パス(src="/…", href="/")を絶対 URL 化 / 本文の前後に MOCK:CONTENT START/END マーカー
"""
import datetime, pathlib, re, subprocess, sys

page, url, wp_id = sys.argv[1], sys.argv[2], sys.argv[3]
today = datetime.date.today().isoformat()
src_dir = pathlib.Path(page) / 'source'; src_dir.mkdir(parents=True, exist_ok=True)
src = pathlib.Path(sys.argv[4]) if len(sys.argv) > 4 else src_dir / f'live-{today}.html'
if not src.exists():
    subprocess.run(['curl', '-s', '-A', 'Mozilla/5.0', url, '-o', str(src)], check=True)
    print(f'取得: {src}')
html = src.read_text(encoding='utf-8')
snap_date = re.search(r'live-(\d{4}-\d{2}-\d{2})', src.name).group(1) if re.search(r'live-\d{4}-\d{2}-\d{2}', src.name) else today

def sub(pattern, repl, s, expect, flags=0):
    new, n = re.subn(pattern, repl, s, flags=flags)
    assert n == expect, f'{pattern[:50]!r}: {n} 件(期待 {expect})'
    return new

title = re.search(r'<title>(.*?)</title>', html).group(1)
header = f'''<!--
  スナップショット: {url} (固定ページ「{title.split(" | ")[0]}」ID {wp_id}) を {snap_date} に取得
  CSS/JS/画像は本番(skym.co.jp)を参照 → 表示にはインターネット接続が必要
  変更点: 相対パスを絶対URL化 / 計測・広告タグ(zipaddr, GA, Yahoo, Google Ads, netowl analyzer)を除去 / title に [snapshot] 付与 / noindex メタ / フォント CSS 4 本を ../../assets/ に変更 / MOCK:CONTENT マーカー挿入
  元ファイル: ../source/{src.name}(無加工)
  生成: tools/make-current.py
-->'''
html = sub(r'^(<!DOCTYPE HTML>)\n', lambda m: m.group(1) + '\n' + header + '\n', html, 1, re.I)
html = sub(r'(\t*)<title>(.*?)</title>', lambda m: f'{m.group(1)}<meta name="robots" content="noindex, nofollow">\n{m.group(1)}<title>{m.group(2)} [snapshot {snap_date}]</title>', html, 1)
html = sub(r"href='https://skym\.co\.jp/wp20150417/wp-content/(themes/Zephyr/css/font-awesome\.css|themes/Zephyr/css/font-mdfi\.css|plugins/Ultimate_VC_Addons/assets/min-css/ultimate\.min\.css|uploads/smile_fonts/Defaults/Defaults\.css)\?ver=[^']*'", r"href='../../assets/wp-content/\1'", html, 4)
html = sub(r'<script src="http://zipaddr\.googlecode\.com/svn/trunk/zipaddr7\.js".*?set_script\(cid\);\s*// -->\s*</script>', '<!-- MOCK: 計測・広告タグ(zipaddr / GA / Yahoo リタゲ / Google Ads / netowl analyzer)を除去 -->', html, 1, re.S)
html = sub(r'src="/wp20150417/', 'src="https://skym.co.jp/wp20150417/', html, 3)
html = sub(r'href="/"', 'href="https://skym.co.jp/"', html, 2)

# 本文マーカー: l-content 内の最初の <section から、フッター直前の最後の </section> まで
lc = html.index('<div class="l-content g-html">')
start = html.index('<section class="l-section', lc)
footer = html.index('l-footer', start)
end = html.rindex('</section>', start, footer) + len('</section>')
assert 'l-header' not in html[start:end], '本文範囲にヘッダーが含まれる'
html = (html[:start] + f'<!-- MOCK:CONTENT START (ここから下がページ本文 = WP の「{title.split(" | ")[0]}」本文に相当。ヘッダー/フッター/タイトル帯はテーマ生成なので触らない) -->\n'
        + html[start:end] + '\n<!-- MOCK:CONTENT END -->' + html[end:])

out = pathlib.Path(page) / 'current' / 'index.html'; out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html, encoding='utf-8')
left = re.findall(r'zipaddr7\.js|_gaq|yahoo_retargeting|google_conversion|set_script|analyzer1\.apps|src="/|href="/"', html)
print(f'出力: {out} ({len(html)} 文字) / 残存チェック: {left or "なし"} / http:// 参照: {len(re.findall(r"http://", html))} 件 / section 数: {html.count("<section class=")}')
