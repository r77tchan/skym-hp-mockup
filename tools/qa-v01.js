async (page, options = {}) => {
  const { pageId = 'it-solution', livePath = '/service/it-solution', root = '#skym-svsub', outputDir = '/tmp/skym-v01-qa' } = options;
  const ctx = await page.context().browser().newContext({deviceScaleFactor: 1});
  const out = [];
  try {
    const p = await ctx.newPage();
    for (const width of [375, 400, 820, 1280, 1455]) {
      await p.setViewportSize({width, height: 900});
      for (const [name, url] of [['v01', 'http://127.0.0.1:8765/' + pageId + '/v01/'], ['live', 'https://skym.co.jp' + livePath]]) {
        await p.goto(url);
        await p.evaluate(async () => {
          // Full-page QA must also load below-fold lazy images before comparing.
          document.querySelectorAll('img[loading="lazy"]').forEach(i => i.loading = 'eager');
          await document.fonts.ready;
          await Promise.race([
            Promise.all([...document.images].map(i => i.decode().catch(() => {}))),
            new Promise(resolve => setTimeout(resolve, 15000))
          ]);
        });
        await p.waitForTimeout(1200);
        await p.evaluate(async()=>{
          document.querySelectorAll('*').forEach(e=>e.getAnimations().forEach(a=>{a.pause();a.currentTime=0}));
          for(const v of document.querySelectorAll('video')){v.pause();v.currentTime=0;await Promise.race([new Promise(r=>v.addEventListener('seeked',r,{once:true})),new Promise(r=>setTimeout(r,1500))]);}
        });
        const data = await p.evaluate((root) => {
          const selectors = ['.l-header', '.l-titlebar', '.l-main', root, root + ' > section', root + ' h2', root + ' p', '.l-footer'];
          const nodes = selectors.flatMap(s => [...document.querySelectorAll(s)].map((e, i) => {
            const r = e.getBoundingClientRect(), c = getComputedStyle(e);
            return {s: s + ':' + i, x: r.x, y: r.y, w: r.width, h: r.height, color: c.color, bg: c.backgroundColor, weight: c.fontWeight, size: c.fontSize, line: c.lineHeight};
          }));
          return {width: innerWidth, client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth, nodes,
            brokenImages: [...document.images].filter(i => !i.complete || !i.naturalWidth).map(i => i.src),
            badStyle: [...document.querySelectorAll(root + ' style')].some(s => /<\/?p[ >]/.test(s.textContent))};
        }, root);
        await p.screenshot({path: outputDir + '/final-' + pageId + '-' + name + '-' + width + '.png', fullPage: true});
        out.push({name, ...data});
      }
    }
    const result = [];
    for (let i = 0; i < out.length; i += 2) {
      const a = out[i], b = out[i + 1];
      result.push({width: a.width, client: b.client, overflow: b.scroll > b.client, brokenImages: b.brokenImages, badStyle: b.badStyle,
        differences: a.nodes.flatMap((n,j) => JSON.stringify(n) === JSON.stringify(b.nodes[j]) ? [] : [{reference:n,live:b.nodes[j]}])});
    }
    return {result,raw:out};
  } finally { await ctx.close(); }
}
