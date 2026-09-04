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
  ],
};
