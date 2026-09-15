#!/usr/bin/env python3
"""<page>/<draft>/block.html(WP に貼る本文 = <style> + HTML)を current の骨格に差し込んで <page>/<draft>/index.html を作る。

使い方: python3 tools/build-draft.py recruit draft1
current の MOCK:CONTENT START〜END を、block.html を Zephyr/VC の全幅行(width_full, columns_type=none)で包んだものに置き換える。
WP 側では [vc_row columns_type="none" width="full" el_class="<block 冒頭の rc-wrap 等>"] の中に block.html をそのまま貼る想定。
tools/mock-links.json があれば、生成後にモック内リンクへの置換とメニューの差し替えを行う(index.html だけ。詳細はファイル末尾のコメント)。
block.html のルートに data-base-page="ses" があれば、自ページの current ではなく ses/current/index.html を骨格に使う
(WP にまだ無い新規ページのモック用。例: 事業内容の個別ページ it-solution は既存サブページ /service/ses の骨格 = タイトル帯 + パンくず「ホーム › 事業内容 › …」を借り、data-page-title で題名を差し替える)。
"""
import json, pathlib, re, sys
page, draft = sys.argv[1], sys.argv[2]
block = pathlib.Path(page, draft, 'block.html').read_text(encoding='utf-8')
base = re.search(r'data-base-page="([^"]+)"', block)
base_page = base.group(1) if base else page
cur = pathlib.Path(base_page, 'current', 'index.html').read_text(encoding='utf-8')
if base: print(f'骨格: {base_page}/current/index.html(新規ページのため別ページの current を借用)')
wrap_class = re.search(r'data-row-class="([^"]+)"', block)
wrap_class = wrap_class.group(1) if wrap_class else ''
a = cur.index('<!-- MOCK:CONTENT START'); b = cur.index('<!-- MOCK:CONTENT END -->') + len('<!-- MOCK:CONTENT END -->')
# block.html のルートに data-keep-tail="N" があれば、current の本文の末尾 N 行(<section class="l-section …)をそのまま後ろに残す
# (例: トップの青いパートナー募集の帯 = テーマの us_cta 行。WP では既存の行を消さずに、その上の行だけ差し替える想定)
kt = re.search(r'data-keep-tail="(\d+)"', block)
tail = ''
if kt:
    c = cur[a:b]; i = len(c)
    for _ in range(int(kt.group(1))): i = c.rindex('<section class="l-section', 0, i)
    tail = c[i:].rstrip() + '\n'
    print(f'current の末尾 {kt.group(1)} 行をそのまま残す({len(tail)} 文字)')
new = (f'<!-- MOCK:CONTENT START ({draft}: 本文 = block.html。WP では [vc_row columns_type="none" width="full" el_class="{wrap_class}"] の中に生 HTML として貼る。ヘッダー/フッターはテーマ生成) -->\n'
       f'<section class="l-section wpb_row height_auto width_full vc_row-fluid {wrap_class}"><div class="l-section-h g-html i-cf"><div class="g-cols offset_none"><div class=" full-width">\n'
       f'{block}\n</div></div></div></section>\n{tail}<!-- MOCK:CONTENT END -->')
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
# block.html のルートに data-page-titlebar="<画像 URL>" があれば、テーマ生成のタイトル帯の背景画像(.l-titlebar-img の background-image)を差し替える
# (WP 側ではページ編集画面の Zephyr タイトル帯設定で背景画像を変える想定。URL は index.html からの相対でも絶対でも可)
ptb = re.search(r'data-page-titlebar="([^"]+)"', block)
if ptb:
    out, n = re.subn(r'(class="l-titlebar-img" style="background-image: url\()[^)]*(\))', lambda m: m.group(1) + ptb.group(1) + m.group(2), out, count=1)
    assert n == 1, 'titlebar img not found'
    print(f'タイトル帯の背景画像: {ptb.group(1)}')
# block.html のルートに data-page-overlay="0.55" があれば、テーマ生成のタイトル帯の黒オーバーレイの不透明度(.l-titlebar-overlay の opacity)を差し替える
# (WP 側ではページ編集画面の Zephyr タイトル帯設定で変える想定。写真が賑やかで白文字が負けるときに 0.4 → 0.55 など)
pov = re.search(r'data-page-overlay="([0-9.]+)"', block)
if pov:
    out, n = re.subn(r'(class="l-titlebar-overlay" style="background-color:#[0-9a-fA-F]{3,6};opacity:)[0-9.]+(")', lambda m: m.group(1) + pov.group(1) + m.group(2), out, count=1)
    assert n == 1, 'titlebar overlay not found'
    print(f'タイトル帯のオーバーレイ: {pov.group(1)}')
out = out.replace('-->\n<html', f'  {draft}: 本文を {page}/{draft}/block.html に差し替えた改修案(tools/build-draft.py で生成。current 側の変更は再生成で追従)' + (f'。骨格は {base_page}/current(WP に無い新規ページのため借用)' if base else '') + '\n-->\n<html', 1)
# tools/mock-links.json があれば、モックが存在するページへの本番リンク(ヘッダー・フッター・パンくず・本文)を Pages 上のモックに向ける
# (2026-09-15 ユーザー依頼。index.html だけの加工で、WP に貼る block.html は本番 URL のまま。メニューの中身も WP 実装後の想定に差し替える:
#  ヘッダーとフッターの「事業内容」= 新しい 6 事業、ヘッダーの「採用情報」= 新卒・未経験 / 中途(未経験の項目は統合)。無いページは本番 URL のまま)
import json
lm_path = pathlib.Path('tools', 'mock-links.json')
if lm_path.exists():
    lm = json.loads(lm_path.read_text(encoding='utf-8'))
    a_ = out.index('<!-- MOCK:CONTENT START'); b_ = out.index('<!-- MOCK:CONTENT END')
    head, body_, foot = out[:a_], out[a_:b_], out[b_:]
    # ヘッダー: 事業内容ドロップダウン
    items = ''.join(f'<li class="menu-item menu-item-type-post_type menu-item-object-page w-nav-item level_2"><a class="w-nav-anchor level_2" href="../../{pth}/"><span class="w-nav-title">{lab}</span><span class="w-nav-arrow"></span></a></li>' for lab, pth in lm['service_menu'])
    head, n1 = re.subn(r'(<span class="w-nav-title">事業内容</span><span class="w-nav-arrow"></span></a>\s*<ul class="w-nav-list level_2">).*?(</ul>)', lambda m: m.group(1) + items + m.group(2), head, count=1, flags=re.S)
    # ヘッダー: 採用情報ドロップダウン(新卒 / 中途 / 未経験 の 3 項目を recruit_menu に。応募フォーム等は残す)
    ritems = ''.join(f'<li class="menu-item menu-item-type-post_type menu-item-object-page w-nav-item level_2"><a class="w-nav-anchor level_2" href="../../{pth}/"><span class="w-nav-title">{lab}</span><span class="w-nav-arrow"></span></a></li>' for lab, pth in lm['recruit_menu'])
    def _rec(m):
        inner = re.sub(r'<li[^>]*>\s*<a[^>]+href="https?://skym\.co\.jp/(?:graduate-pre|recruit/career|recruit/newbie)"[^>]*>.*?</li>\s*', '', m.group(2), flags=re.S)
        return m.group(1) + ritems + inner + m.group(3)
    head, n2 = re.subn(r'(<span class="w-nav-title">採用情報</span><span class="w-nav-arrow"></span></a>\s*<ul class="w-nav-list level_2">)(.*?)(</ul>)', _rec, head, count=1, flags=re.S)
    # フッター: 事業内容の列(nav_menu ウィジェット。SES / 受託・委託開発 / デザイン… → 6 事業)
    fitems = ''.join(f'<li class="menu-item menu-item-type-post_type menu-item-object-page"><a href="../../{pth}/">{lab}</a></li> ' for lab, pth in lm['service_menu'])
    foot, n3 = re.subn(r'(<ul id="menu-[^"]*" class="menu">)(?:(?!</ul>).)*?href="https?://skym\.co\.jp/service/ses"(?:(?!</ul>).)*?(</ul>)', lambda m: m.group(1) + fitems + m.group(2), foot, count=1, flags=re.S)
    # 残りの本番リンク(ヘッダー・フッター・パンくず・本文)をモックへ
    def _map(m):
        pth = (m.group(1) or '').strip('/'); anc = m.group(2) or ''
        return f'href="../../{lm["links"][pth]}/{anc}"' if pth in lm['links'] else m.group(0)
    pat = re.compile(r'href="https?://skym\.co\.jp(/[^"#]*)?(#[^"]*)?"')
    head, c1 = pat.subn(_map, head); body_, c2 = pat.subn(_map, body_); foot, c3 = pat.subn(_map, foot)
    out = head + body_ + foot
    print(f'モック内リンク: ヘッダー事業内容メニュー {n1} / 採用情報メニュー {n2} / フッター事業内容 {n3} / 本番→モック置換 ヘッダー {c1}・本文 {c2}・フッター {c3}')
# tools/site.json の font があれば、head の末尾(子テーマ style.css の後)に Google Fonts の <link> と、子テーマと同じ形の * ルールを差し込んでサイト全体の書体を差し替える
# (2026-09-15 ユーザー決定: サイト全体を Zen Kaku Gothic New に統一。本番では子テーマ style.css の * ルールの font-family を書き換え、head の旧 Noto の <link> を差し替える想定。
#  font-weight は子テーマの * { font-weight: 300 !important } のまま。index.html だけの加工で block.html は触らない。preview.html の ?f= はこの後に足されるので上書きできる)
site_path = pathlib.Path('tools', 'site.json')
if site_path.exists():
    site = json.loads(site_path.read_text(encoding='utf-8'))
    ft = site.get('font')
    if ft:
        assert out.count('</head>') == 1, '</head> が 1 つでない'
        inj = (f'<!-- MOCK:SITE-FONT {ft["label"]}(tools/site.json。本番では子テーマ style.css の * ルールの font-family と head の旧 Noto の link を差し替える想定) -->\n'
               f'<link rel="stylesheet" href="{ft["css"]}">\n'
               f"<style id=\"mock-site-font\">* {{ font-family: {ft['family']}, 'mdfonticon', -apple-system, 'Helvetica Neue', 'Hiragino Kaku Gothic ProN', '游ゴシック Medium', 'メイリオ', meiryo, sans-serif !important; }}</style>\n")
        out = out.replace('</head>', inj + '</head>', 1)
        print(f'サイト共通の書体: {ft["label"]}(head に link と * ルールを差し込み)')
pathlib.Path(page, draft, 'index.html').write_text(out, encoding='utf-8')
print(f'{page}/{draft}/index.html: {len(out)} 文字(block {len(block)} 文字, 行クラス "{wrap_class}")')
