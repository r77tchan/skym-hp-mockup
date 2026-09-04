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
      ],
    },
  ],
};
