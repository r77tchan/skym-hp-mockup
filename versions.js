// モック一覧のデータ。index.html(一覧)と preview.html(比較)が読む。
// 版を凍結したら該当ページの versions に 1 行足す。id はディレクトリ名(<page>/<id>/index.html)。
window.MOCK = {
  pages: [
    {
      id: 'top',
      name: 'トップページ',
      live: 'https://skym.co.jp/',
      versions: [
        { id: 'current', date: '2026-09-01', note: '現状再現(公開ページのスナップショット。CSS/JS/画像は本番を参照)' },
      ],
    },
    {
      id: 'service',
      name: '事業内容',
      live: 'https://skym.co.jp/service',
      versions: [
        { id: 'current', date: '2026-09-04', note: '現状再現(ID 6170。タイトル帯あり)' },
        { id: 'draft1', date: '', note: '案1: 現行からオーダーメイド・スキル行を削除し、問合せ+パートナー募集ボックス2連を追加(VC構造のまま)' },
      ],
    },
    {
      id: 'recruit',
      name: '採用情報',
      live: 'https://skym.co.jp/recruit',
      versions: [
        { id: 'current', date: '2026-09-04', note: '現状再現(ID 6177。タイトル帯なし)' },
        { id: 'draft1', date: '2026-09-04', note: '案1: メッセージ中心に再構成。事業内容は写真カード(C 案)・平易な名称。写真は撮影指示付きプレースホルダー。本文は block.html' },
        { id: 'draft2', date: '', note: '案2: draft1 から EC 事例ブロックを削除。事業カード01〜03に画像を採用' },
        { id: 'draft3', date: '', note: '案3: draft2 複製。締めをヒーローと対の濃紺写真帯に(英語ラベル削除・見出し短縮・重複文削除)' },
        { id: 'draft4', date: '', note: '案4: draft3 複製。事業内容を 6 枚(英語名主役+日本語キャッチ 1 行・抽象表現)に。写真は WP メディアライブラリの既存画像を 3:2 に切り出して 6 枚すべてに使用(差し替え可)' },
        { id: 'draft5', date: '', note: '案5: draft4 複製。採用案内をカードから編集リスト(英語ラベル/見出し/対象1文+具体1文/募集要項を見る)の 3 行に。写真なし。ラベルは EXPERIENCED / CAREER CHANGE' },
        { id: 'draft6', date: '', note: '案6: draft5 複製。全文チェックを反映(AI節末尾の「つくる」連打を1文に、カギ括弧を減らす、「仕事を動かせる人」、AI節1段落目の論理、きっかけの受け直し、インタビュー氏名を日本語+ローマ字)。メッセージ節の右カラム位置とカギ括弧のぶら下げ' },
      ],
    },
    {
      id: 'career',
      name: '中途採用',
      live: 'https://skym.co.jp/recruit/career',
      versions: [
        { id: 'current', date: '2026-09-07', note: '現状再現(ID 7807。タイトル帯あり。2015 年の内容: 第5期メンバー募集・5 職種タブ・SORAJUKU)' },
      ],
    },
    {
      id: 'newbie',
      name: '未経験採用',
      live: 'https://skym.co.jp/recruit/newbie',
      versions: [
        { id: 'current', date: '2026-09-07', note: '現状再現(ID 8464。タイトル帯あり。2015 年の内容: SORAJUKU・初任給 18 万円)' },
      ],
    },
    {
      id: 'graduate-pre',
      name: '新卒採用',
      live: 'https://skym.co.jp/graduate-pre',
      versions: [
        { id: 'current', date: '2026-09-07', note: '現状再現(ID 8577。タイトル帯あり。2026-08-25 作成の「未経験ITエンジニア採用」本文、VC の項目行 14 行)' },
      ],
    },
  ],
};
