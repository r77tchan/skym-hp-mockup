# skym-hp-mockup — サイト改修の検討用モック

株式会社スカイム コーポレートサイト(skym.co.jp)の改修案を、WP に反映する前に HTML で検討するためのモック置き場。
`skym-hp-wp` リポジトリの `mockup/` に置く**独立した git リポジトリ**(親からは `.gitignore` で無視される)。経緯・決定事項は `skym-hp-wp/doc/作業記録/`(15: トップページ改修、18: この公開環境の構築)にある。

- 公開 URL: **https://r77tchan.github.io/skym-hp-mockup/** (GitHub Pages、`main` ブランチのルートを配信。push すると約 1 分で反映)
- リポジトリ: https://github.com/r77tchan/skym-hp-mockup
- **URL を知る人は誰でも見られる**(GitHub Pages はアクセス制限不可)。機密情報・未公開の社内情報は置かない。検索避けとして全ページに `noindex` メタ、`robots.txt` で全拒否

## 構成と URL

```
/                         index.html   一覧(ページ × 版の表。versions.js から生成)
/preview.html                          幅指定・並列比較(?a=top/v01/&b=top/current/&w=390)
/versions.js                           一覧データ(ページ・版・メモ)。凍結時にここへ 1 行足す
/assets/                               Web フォントと、それを宣言する CSS のミラー(全ページ・全版で共有)
/top/current/             index.html   トップページの現状再現(凍結。触らない)
/top/draft1/, /top/draft2/ … index.html 検討中の案(案ごとに番号。編集するのはここだけ)
/top/v01/, /top/v02/ …    index.html   節目で draftN を凍結したコピー(以後変更しない。共有用の固定 URL)
/top/source/                           参照用の原本(公開ページの無加工スナップショット、WP 本文の VC ショートコード全文)
/<page>/…                              別ページも同じ型(current / draftN / vNN / source)
```

「このページのこの版」= `https://r77tchan.github.io/skym-hp-mockup/<page>/<版>/` で直接開ける。

## 版のルール

- `current/` と `vNN/` は**凍結**(変更しない)。編集するのは `draftN/` だけ。番号は「案」の単位(案 1 = `draft1`、別方向の案 2 = `draft2`)。同じ案の手直しは同じディレクトリで上書きする(履歴は git)
- 共有用に固定 URL が欲しいとき(節目)は凍結する: `cp -r top/draft1 top/v01` → `versions.js` の該当ページに `{ id: 'v01', date: '…', note: 'draft1 の YYYY-MM-DD 時点' }` を足す → commit → push
- 案を作るとき: `cp -r top/current top/draft1` → `versions.js` に `{ id: 'draft1', date: '', note: '案1: 何を狙った案か' }` を足す
- 何を変えた版かの詳細は `skym-hp-wp/doc/作業記録/` に書く(versions.js の note は一行の要約)

## 表示方法

ローカル(`skym-hp-wp` のルートで実行):

```
python3 -m http.server 8765 --directory mockup --bind 127.0.0.1
```

- 一覧: http://127.0.0.1:8765/
- 現状: http://127.0.0.1:8765/top/current/
- 幅指定・比較: http://127.0.0.1:8765/preview.html?a=top/draft1/&b=top/current/&w=390 (ヘッダーで幅・表示を切替。`b` には URL も指定可)

公開側も同じパス(`https://r77tchan.github.io/skym-hp-mockup/` 以下)。

## 編集ルール(モック → WP に戻せる書き方に限る)

- ヘッダー・フッター(`l-header`, `l-footer`)はテーマが生成する部分なので触らない(WP に戻せない)
- 本文は `<!-- MOCK:CONTENT START -->` 〜 `<!-- MOCK:CONTENT END -->` の内側だけを編集する
- 本文は VC で再現できる書き方に留める: 行 = `<section class="l-section ...">`、中身は既存部品の HTML(w-btn, w-iconbox, uvc-heading など)か素の HTML(`vc_column_text` に直書きする前提)
- 新規画像はここに置かず、本番 uploads にアップロードしてから絶対 URL で参照する(モック段階は仮画像可)
- ブラウザ MCP の `resize_window` は効かないので、スマホ幅の確認は `preview.html` を使う

## ファイルの由来(top。service / recruit も同じ加工を tools/make-current.py で実施)

| ファイル | 内容 |
|---|---|
| `top/source/live-2026-09-01.html` | 公開トップページ https://skym.co.jp/ の無加工スナップショット(curl、非ログイン) |
| `top/current/index.html` | 上記を元にした現状再現版。CSS/JS/画像は本番を参照(要ネット接続)。計測タグ除去・相対パス絶対化・フォント CSS 4 本を `../../assets/` に変更・`noindex` 追加・`MOCK:CONTENT START/END` マーカー挿入 |
| `assets/` | Web フォント(mdfonticon / FontAwesome / ult-silk / smile_fonts)と、それを宣言する CSS 4 本のミラー。**CORS 制約で別オリジンのフォントは読めないため**ローカルに置く。パス構造は本番と同じ |
| `top/source/home-6155-raw.txt` | WP 固定ページ「ホーム」(ID 6155)の本文 = VC ショートコード全文(5778 文字、チェックサム 930333684)。ロールバック・書き戻しの参照用 |

## 別ページを追加するとき

1. `python3 tools/make-current.py <page> <url> <WP のページ ID>`(例: `python3 tools/make-current.py service https://skym.co.jp/service 6170`)。無加工スナップショットを `<page>/source/live-YYYY-MM-DD.html` に取得し、`<page>/current/index.html` を生成する。加工内容: 計測・広告タグ除去 / 相対パスを絶対 URL 化 / フォント CSS 4 本を `../../assets/...` に差し替え / `noindex` メタ / title に `[snapshot]` / 本文の前後に `MOCK:CONTENT START/END` マーカー。件数が想定と違うと assert で止まる(テーマ側の構造が変わったときは手で確認)
2. `versions.js` の `pages` にページ(id・name・live・versions: current)を足す
3. ローカルで表示確認(`preview.html?a=<page>/current/&b=<本物の URL>&w=390`)→ commit → push

作成済み: `top`(2026-09-01、手作業。上の加工を先に手で行ったもの)/ `service`(事業内容、ID 6170、2026-09-04)/ `recruit`(採用情報、ID 6177、2026-09-04)。URL は末尾スラッシュ無し(`/service/` は `/service` へ 301)
