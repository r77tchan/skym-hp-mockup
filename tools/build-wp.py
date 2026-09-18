#!/usr/bin/env python3
"""block.html(WP に貼る本文)を WP 貼り付け用に変換する(段階0の成果物。サイトには触らない)。

使い方(mockup/ で実行):
  python3 tools/build-wp.py <page> <draft>   # tools/wp/<page>.html を作り、手作業設定を表示
  python3 tools/build-wp.py --all            # 採用版 12 件を全部変換 + tools/wp/manifest.json(画像一覧)

変換内容:
  1. HTML コメント(<!-- ... -->)を除去(検討時のメモなので WP には貼らない)
  2. ルート要素の build 用 data-* 属性を除去(id/class/style は残す)。
     除去した値は貼り方の設定として標準出力に表示する(vc_row の el_class、
     ページタイトル・サブタイトル・親・タイトル帯画像・オーバーレイ、末尾残し)
  3. 画像・動画の相対パス( bare の hero-card1.jpg / poster / ../../service/draft7/card1-ses.jpg )
     → https://skym.co.jp/wp20150417/wp-content/uploads/<接頭辞>-<元名> の絶対パスへ。
     内容が重複するファイル(top と service の card6 枚、recruit と graduate-pre の tb-newbie)は
     1 つにまとめる(中身が同じなので別名で二重アップロードしない)
  4. モック内リンク(../../it-solution/draft1/ 等)→ 本番 URL(https://skym.co.jp/service/it-solution)。
     本番 URL・tel:・# はそのまま
出力の tools/wp/<page>.html が、カスタム HTML ブロックの中に貼る本文そのもの。
画像は manifest の upload_name で uploads へ上げてある前提(URL は先に確定させる方式)。
"""
import hashlib
import json
import pathlib
import re
import sys

UPLOADS = "https://skym.co.jp/wp20150417/wp-content/uploads"
OUTDIR = pathlib.Path("tools", "wp")

# ページごとの画像ファイル名の接頭辞(uploads 上での衝突回避)
PREFIX = {
    "top": "top", "service": "service", "recruit": "recruit", "career": "career",
    "graduate-pre": "grad", "company": "company", "it-solution": "itsol",
    "ai-digital": "ai", "ec-product": "ec", "event": "event",
    "education": "edu", "sakura": "sakura",
}

# 採用版 12 件: (ページ, 版, 本番 URL)
ADOPTED = [
    ("top", "draft20", "https://skym.co.jp/"),
    ("service", "draft7", "https://skym.co.jp/service"),
    ("recruit", "draft9", "https://skym.co.jp/recruit"),
    ("career", "draft5", "https://skym.co.jp/recruit/career"),
    ("graduate-pre", "draft5", "https://skym.co.jp/recruit/newbie"),
    ("company", "draft4", "https://skym.co.jp/company"),
    ("it-solution", "draft1", "https://skym.co.jp/service/it-solution"),
    ("ai-digital", "draft3", "https://skym.co.jp/service/ai-digital"),
    ("ec-product", "draft2", "https://skym.co.jp/service/ec-product"),
    ("event", "draft2", "https://skym.co.jp/service/event"),
    ("education", "draft4", "https://skym.co.jp/service/education"),
    ("sakura", "draft9", "https://skym.co.jp/service/sakura"),
]

# モックの版パス → 本番 URL(draft と v01 の両方を受ける)
MOCK2LIVE = {}
for _pg, _dr, _live in ADOPTED:
    MOCK2LIVE[f"{_pg}/{_dr}/"] = _live
    MOCK2LIVE[f"{_pg}/v01/"] = _live

MEDIA_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov")


def collect_media():
    """採用版 12 件が参照する画像・動画を集め、内容ハッシュで重複をまとめる。

    戻り値: (manifest, key2url)
      manifest: [{upload_name, url, size, md5, sources:[repo 内パス...], used_by:[ページ...]}]
      key2url: 参照解決用 {(page, filename)->url, filename->url}
    参照の形は 3 種: 自版内の bare 名 / ../../他版/名 / data-page-titlebar の bare 名。
    """
    by_hash = {}   # md5 -> entry
    key2url = {}   # (page, filename) / (filename,) -> url
    order = [pg for pg, _, _ in ADOPTED]
    for page, draft, _live in ADOPTED:
        d = pathlib.Path(page, draft)
        block = (d / "block.html").read_text(encoding="utf-8")
        cands = set()
        for m in re.findall(r'(?:src|href|poster)="([^"]+)"', block):
            if m.startswith(("http", "#", "mailto:", "tel:")):
                continue
            if m.startswith("../../"):
                if m.split("#")[0].lower().endswith(MEDIA_EXT):
                    cands.add(("cross", m))  # 他版の画像だけ。ページリンクは対象外
            elif "/" not in m and m.lower().endswith(MEDIA_EXT):
                cands.add(("bare", m))
        mtb = re.search(r'data-page-titlebar="([^"]+)"', block)
        if mtb and "/" not in mtb.group(1) and mtb.group(1).lower().endswith(MEDIA_EXT):
            cands.add(("bare", mtb.group(1)))
        for kind, ref in sorted(cands):
            if kind == "bare":
                f = d / ref
            else:
                parts = ref.split("/")
                f = pathlib.Path(parts[2], parts[3], parts[4])
            assert f.exists(), f"{page}/{draft}: {ref} → {f} が無い"
            if f.name.startswith("TMP-"):
                continue
            digest = hashlib.md5(f.read_bytes()).hexdigest()
            if digest in by_hash:
                e = by_hash[digest]
                if str(f) not in e["sources"]:
                    e["sources"].append(str(f))
                if page not in e["used_by"]:
                    e["used_by"].append(page)
                url = e["url"]
            else:
                name = f"{PREFIX[page]}-{f.name}"
                url = f"{UPLOADS}/{name}"
                by_hash[digest] = {
                    "upload_name": name, "url": url, "size": f.stat().st_size,
                    "md5": digest, "sources": [str(f)], "used_by": [page],
                }
            key2url[(page, f.name)] = url
            key2url.setdefault((f.name,), url)
    manifest = [by_hash[k] for k in by_hash]
    manifest.sort(key=lambda e: e["upload_name"])
    return manifest, key2url


def convert(page, draft, key2url):
    """block.html → WP 貼り付け用 HTML と手作業設定の辞書を返す。"""
    block = pathlib.Path(page, draft, "block.html").read_text(encoding="utf-8")
    m = re.search(r"<div[^>]*id=\"skym-[^\"]*\"[^>]*>", block)
    assert m, "ルート div(id=skym-*)が無い"
    settings = dict(re.findall(r'(data-[a-z-]+)="([^"]*)"', m.group(0)))

    out = re.sub(r"<!--.*?-->", "", block, flags=re.S)  # 検討メモの除去
    # build 用 data-* だけ除去(data-icon 等のデザイン用は残す)
    out = re.sub(r'\sdata-(row-class|keep-tail|base-page|page-title|page-subtitle|page-parent|page-titlebar|page-overlay)="[^"]*"', "", out)
    leftover = re.findall(r'\sdata-(row-class|keep-tail|base-page|page-title|page-subtitle|page-parent|page-titlebar|page-overlay)="', out)
    assert not leftover, f"build 用 data-* が残っている: {leftover}"
    assert "<!--" not in out, "コメントが残っている"

    def _media(fname, pg):
        url = key2url.get((pg, fname)) or key2url.get((fname,))
        assert url, f"{pg}: 画像 {fname} の対応 URL が無い(manifest 未登録)"
        return url

    def _sub_attr(mo):
        attr, val = mo.group(1), mo.group(2)
        if val.startswith(("http", "#", "mailto:", "tel:")):
            return mo.group(0)
        if val.startswith("../../"):
            parts = val.split("/")
            if len(parts) >= 4 and parts[4].lower().endswith(MEDIA_EXT):
                return f'{attr}="{_media(parts[4], parts[2])}"'  # 他版の画像
            key = f"{parts[2]}/{parts[3]}/"
            assert key in MOCK2LIVE, f"{page}: モック内リンク {val} の本番 URL が無い"
            anchor = ""
            if "#" in val:
                anchor = val[val.index("#"):]
            return f'{attr}="{MOCK2LIVE[key]}{anchor}"'
        if "/" not in val and val.lower().endswith(MEDIA_EXT):
            return f'{attr}="{_media(val, page)}"'  # 自版の画像・動画・poster
        return mo.group(0)

    out = re.sub(r'(src|href|poster)="([^"]+)"', _sub_attr, out)
    assert "../" not in out, "相対パスが残っている"
    return out.strip() + "\n", settings


def report(page, draft, live, settings, html, key2url):
    print(f"=== {page} ({draft} → {live}) ===")
    print(f"貼り方: カスタム HTML ブロックに tools/wp/{page}.html を貼る "
          f"([vc_row columns_type=\"none\" width=\"full\" el_class=\"{settings.get('data-row-class', '')}\"] の中)")
    if settings.get("data-keep-tail"):
        print(f"注意: 既存行の末尾 {settings['data-keep-tail']} 行(青いパートナー募集の帯)は消さずに残す")
    if settings.get("data-page-title"):
        print(f"手作業: ページタイトル「{settings['data-page-title']}」"
              + (f" / サブタイトル「{settings.get('data-page-subtitle', '')}」" if settings.get("data-page-subtitle") else ""))
    if settings.get("data-page-parent"):
        print(f"手作業: 親ページ「{settings['data-page-parent']}」")
    if settings.get("data-page-titlebar"):
        tb = settings["data-page-titlebar"]
        if "/" not in tb and not tb.startswith("http"):
            tb = f"{key2url.get((page, tb), tb)}(元 {settings['data-page-titlebar']})"
        print(f"手作業: タイトル帯の背景「{tb}」"
              + (f" / オーバーレイ {settings.get('data-page-overlay', '')}" if settings.get("data-page-overlay") else ""))
    n_img = len(re.findall(r'(?:src|poster)="https?://', html))
    print(f"本文: {len(html)} 文字 / 画像 {n_img} 件(すべて uploads 絶対パス)")


def main():
    args = sys.argv[1:]
    OUTDIR.mkdir(exist_ok=True)
    manifest, key2url = collect_media()
    if args == ["--all"]:
        targets = ADOPTED
    else:
        page, draft = args
        live = next((l for p, _d, l in ADOPTED if p == page), "")
        targets = [(page, draft, live)]
    for page, draft, live in targets:
        html, settings = convert(page, draft, key2url)
        (OUTDIR / f"{page}.html").write_text(html, encoding="utf-8")
        report(page, draft, live, settings, html, key2url)
    if args == ["--all"]:
        (OUTDIR / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        total = sum(e["size"] for e in manifest)
        print(f"---\n画像・動画: {len(manifest)} ファイル {total / 1024 / 1024:.1f}MB"
              f"(tools/wp/manifest.json に一覧。重複内容は1つにまとめ済み)")


if __name__ == "__main__":
    main()
