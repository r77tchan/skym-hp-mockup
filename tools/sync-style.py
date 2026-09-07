#!/usr/bin/env python3
"""共通テンプレートの <style> を、元の block.html から他ページの block.html にコピーする。

使い方: python3 tools/sync-style.py career/draft1 graduate-pre/draft1 [newbie/draft1 ...]
採用の個別ページ(中途・未経験・新卒)は同じ <style>(#skym-rsub)を持つ前提。CSS は最初の引数のページで直し、
このスクリプトで残りに配る。行頭の <style> から </style> までの 1 ブロックだけを置き換える(HTML 本文は触らない。コメント内の文字列には反応しない)。
"""
import pathlib, re, sys

src = pathlib.Path(sys.argv[1], 'block.html').read_text(encoding='utf-8')
style = re.search(r'^<style>.*?^</style>', src, re.S | re.M).group(0)
for dst in sys.argv[2:]:
    p = pathlib.Path(dst, 'block.html'); html = p.read_text(encoding='utf-8')
    new, n = re.subn(r'^<style>.*?</style>', lambda m: style, html, count=1, flags=re.S | re.M)
    assert n == 1, f'{p}: <style> が見つからない'
    p.write_text(new, encoding='utf-8')
    print(f'{p}: style {len(style)} 文字を同期({"変更あり" if new != html else "変更なし"})')
