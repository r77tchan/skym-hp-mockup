# skym-hp-mockup

skym.co.jpの改修案をWordPressへ反映する前に検討するためのモック。
親のskym-hp-wpとは独立したgitリポジトリです。

- 公開一覧：https://r77tchan.github.io/skym-hp-mockup/
- GitHub：r77tchan/skym-hp-mockup
- mainへのpushでGitHub Pagesへ公開。反映完了は実際のページで確認する。
- 公開物のため機密情報・管理画面情報・バックアップを置かない。noindex／robots.txtはアクセス制限ではない。

## 版の意味

| パス | 意味 | 編集 |
|---|---|---|
| <page>/current/ | 初回取得当時の現状再現。名前に反して最新本番ではない | 不可 |
| <page>/draftN/ | 検討・修正中の案 | 可 |
| <page>/vNN/ | 承認や共有の節目で固定した版 | 不可 |
| <page>/source/ | 取得時点の原本・参照資料 | 原本を上書きしない |
| <page>/lab/ | 部品等の試作 | 可 |
| assets/ | モック用フォント等の共有資産 | 凍結版への影響を確認 |

- 新しい案・別基準から作る場合は、そのページの次の空きdraft番号を使う。同じ案の手直しは同じdraftでよい。
- 凍結するときは承認済みdraftを未使用のvNNへコピーし、versions.jsに元版・日付・説明を登録する。既存vNNの再生成・上書きは禁止。
- 2026-09-21時点：作業40の12ページはv01を元に本番反映・ユーザー表示確認済み。v01は移植元であって、導線整理後の本番と完全同一ではない。
- 本番に合わせた新draft→v02は今後の提案であり、未作成・実施GO待ち。既存currentを最新本番に差し替えない。
- 凍結版にも本番CSS/JS/画像や共有assetsへの参照がある。フォルダの凍結は、依存先を含む完全アーカイブを意味しない。

## 表示する

以下は親skym-hp-wpのルートで実行する。

```sh
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8765/
python3 -m http.server 8765 --directory mockup --bind 127.0.0.1
```

最初の確認で200なら、既存サーバーを使い二重起動しない。起動が必要な場合だけ2行目を実行する。

- 一覧：http://127.0.0.1:8765/
- 版の直リンク：/<page>/<版>/
- 並列比較：/preview.html?a=top/v01/&b=top/current/&w=390
- previewの縦長iframeは目視補助。vhやパララックスの条件が変わるため、厳密な比較には通常のviewportを使う。
- versions.jsが一覧の表示データ。本文や設定の正本ではない。

## draftを作る

以下の生成コマンドはmockup/で実行する。実行前に出力先が編集対象draftであることを確認する。

1. <page>/draftN/block.htmlに本文のstyleとルートHTMLを置く。
2. ルートのdata属性で外枠・タイトル帯等を指定する。
3. `python3 tools/build-draft.py <page> draftN`でindex.htmlを生成する。
4. 画像・書体・PC/SP・リンクを確認し、versions.jsへ版と説明を登録する。
5. 対象ファイルだけコミット・pushし、公開結果を確認する。

| 属性 | 用途 |
|---|---|
| data-row-class | VC行のクラス |
| data-base-page | 別ページのcurrentを骨格として使用 |
| data-page-title / data-page-subtitle | タイトル・副題 |
| data-page-parent | パンくずの親。例：採用情報\|https://skym.co.jp/recruit |
| data-page-titlebar | タイトル帯画像 |
| data-page-overlay | オーバーレイ不透明度 |
| data-keep-tail | 元本文末尾の行を保持。トップは1 |

現在のbuild-draft.pyは過去のcurrentを骨格として使うため、生成しただけで最新本番のヘッダー・フッターになるわけではない。
今後の本番対応版では生成方法も検討する。index.htmlだけを手修正して再生成で失う運用は避ける。

## リンク・書体・素材

- tools/mock-links.jsonが、本番URLからモック版へのリンク対応とメニュー生成を管理する。変更の影響先を確認し、既存凍結版を再ビルドしない。
- tools/site.jsonのfontをbuild-draft.pyが反映する。現在はZen Kaku Gothic New。block.htmlに重複したフォント読込を追加しない。
- 子テーマのfont-weight:300!importantの影響があるため、承認版の継承・個別ウェイト指定を保持する。
- ページ間のデザイン統一は必須ではない。古いtop/draft3等の型を新しい案へ強制しない。
- モック素材は版から参照できる場所に置き、本番用には承認後にWPメディアへ登録する。相対参照先も凍結時に確認する。
- tools/sync-style.pyは複数draftのCSS同期用。凍結版へ適用しない。
- tools/make-current.pyは未作成ページの初回スナップショット用。既存currentを更新するコマンドとして使わない。取得データの公開可否も確認する。

## WP向け生成

```sh
python3 tools/build-wp.py --all
```

現在の--allは12ページのv01を入力とする。自動で「最新draft」や「本番対応版」を選ばない。
新しい入力版への切替は別途承認とツール確認が必要。

| 出力 | 用途 |
|---|---|
| tools/wp/<page>.post.txt | VC外枠込みの貼り付け用本文 |
| tools/wp/<page>.html | 外枠なしの中間成果物 |
| tools/wp/<page>.settings.json | 元版・ヘッダー等の設定・生成本文ハッシュ |
| tools/wp/manifest.json | 素材対応表 |

.post.txtは単一カスタムHTMLブロックで保存する。
外枠は `[vc_row height="auto" columns_type="none" width="full" ...][vc_column]`。
vc_column_textを追加するとテーマのSP余白が増えるため使わない。
トップのdata-keep-tail="1"は既存青帯の保全指定であり、生成本文だけで全体を置換しない。
WP上のページ設定・メニュー・転送は生成本文とは別に保存・確認する。

## 視覚検証

- 同じOS・ブラウザ・viewport・DPR・スクロール位置・読込状態で比較する。
- 基本幅は375/400/820/1280/1455px。innerWidthとclientWidthを測り、スクロールバーも条件に含める。
- tools/qa-v01.jsはPlaywrightのpageを受け取る関数。第2引数はpageId／livePath／root／outputDir。出力先を事前作成する。
- 独立した非ログインcontextで5幅のPNGを保存し、{result,raw}を返す。動画・アニメーション停止はその検証context内だけ。実再生は別途確認する。
- ページ別の返り値を `{"it-solution": {...}, ...}` 形式のfinal-metrics.jsonに保存する。
- `python3 tools/compare-v01.py <outputDir>`で画素差を集計する（Pillow使用）。比較はフッター前までで、フッターは別途検証する。
- 閾値だけで合格とせず、差の場所・寸法・スタイル・描画条件を確認する。全景撮影の端数差は同じスクロール位置のviewport撮影でも調べる。
- 検証画像・JSONは親のgit管理外backup/等へ置き、公開リポジトリに混ぜない。

本番の承認範囲・現状・復旧資料は、親リポジトリのサイト情報・反映手順・作業記録40を参照する。
