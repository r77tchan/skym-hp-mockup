#!/usr/bin/env python3
"""<page>/<draft>/block.html(WP に貼る本文 = <style> + HTML)を current の骨格に差し込んで <page>/<draft>/index.html を作る。

使い方: python3 tools/build-draft.py recruit draft1
current の MOCK:CONTENT START〜END を、block.html を Zephyr/VC の全幅行(width_full, columns_type=none)で包んだものに置き換える。
WP 側では [vc_row columns_type="none" width="full" el_class="<block 冒頭の rc-wrap 等>"] の中に block.html をそのまま貼る想定。
"""
import pathlib, re, sys
page, draft = sys.argv[1], sys.argv[2]
cur = pathlib.Path(page, 'current', 'index.html').read_text(encoding='utf-8')
block = pathlib.Path(page, draft, 'block.html').read_text(encoding='utf-8')
wrap_class = re.search(r'data-row-class="([^"]+)"', block)
wrap_class = wrap_class.group(1) if wrap_class else ''
a = cur.index('<!-- MOCK:CONTENT START'); b = cur.index('<!-- MOCK:CONTENT END -->') + len('<!-- MOCK:CONTENT END -->')
new = (f'<!-- MOCK:CONTENT START ({draft}: 本文 = block.html。WP では [vc_row columns_type="none" width="full" el_class="{wrap_class}"] の中に生 HTML として貼る。ヘッダー/フッターはテーマ生成) -->\n'
       f'<section class="l-section wpb_row height_auto width_full vc_row-fluid {wrap_class}"><div class="l-section-h g-html i-cf"><div class="g-cols offset_none"><div class=" full-width">\n'
       f'{block}\n</div></div></div></section>\n<!-- MOCK:CONTENT END -->')
out = cur[:a] + new + cur[b:]
out = re.sub(r'\[snapshot [0-9-]+\]', f'[{draft}]', out, count=1)
# block.html のルートに data-page-title / data-page-subtitle / data-page-parent="親タイトル|親URL" があれば、テーマ生成のタイトル帯(h1・サブタイトル・パンくず末尾)と <title> の該当語を差し替える
# (WP 側ではページタイトルと Zephyr のタイトル帯サブタイトルを変える想定。メニューのラベルは別途)
pt = re.search(r'data-page-title="([^"]+)"', block); ps = re.search(r'data-page-subtitle="([^"]+)"', block)
if pt:
    ta = out.index('class="l-titlebar '); tb_ = out.index('<div class="l-main">', ta); tb = out[ta:tb_]
    h1 = re.search(r'<h1>(.*?)</h1>', tb); old_title = h1.group(1)
    tb = tb.replace(f'<h1>{old_title}</h1>', f'<h1>{pt.group(1)}</h1>', 1)
    tb = tb.replace(f'<span class="g-breadcrumbs-item">{old_title}<', f'<span class="g-breadcrumbs-item">{pt.group(1)}<', 1)
    if ps:
        tb, n = re.subn(r'(</h1>\s*<p>)(.*?)(</p>)', lambda m: m.group(1) + ps.group(1) + m.group(3), tb, count=1); assert n == 1, 'subtitle <p> not found'
    pp = re.search(r'data-page-parent="([^"|]+)\|([^"]+)"', block)
    if pp:
        last = tb.rindex('<span class="g-breadcrumbs-item">')
        tb = tb[:last] + f'<span typeof="v:Breadcrumb"><a class="g-breadcrumbs-item" rel="v:url" property="v:title" href="{pp.group(2)}">{pp.group(1)}</a></span> <span class="g-breadcrumbs-separator"></span> ' + tb[last:]
        print(f'パンくず: 親「{pp.group(1)}」({pp.group(2)})を挿入')
    out = out[:ta] + tb + out[tb_:]
    out = out.replace(f'<title>{old_title} |', f'<title>{pt.group(1)} |', 1)
    print(f'タイトル帯: 「{old_title}」→「{pt.group(1)}」' + (f' / サブタイトル「{ps.group(1)}」' if ps else ''))
out = out.replace('-->\n<html', f'  {draft}: 本文を {page}/{draft}/block.html に差し替えた改修案(tools/build-draft.py で生成。current 側の変更は再生成で追従)\n-->\n<html', 1)
pathlib.Path(page, draft, 'index.html').write_text(out, encoding='utf-8')
print(f'{page}/{draft}/index.html: {len(out)} 文字(block {len(block)} 文字, 行クラス "{wrap_class}")')
