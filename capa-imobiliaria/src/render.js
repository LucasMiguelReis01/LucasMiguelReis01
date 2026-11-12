const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const base = 'file://' + path.resolve('src/capa.html');
  const jobs = [['retrato', 1240, 1754, 'capa-reis-imoveis-retrato.png'], ['banner', 1640, 624, 'capa-reis-imoveis-banner.png']];
  for (const [v, w, h, out] of jobs) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
    await p.goto(base + '?v=' + v);
    await p.waitForSelector('body[data-ready="1"]'); await p.waitForTimeout(300);
    await p.screenshot({ path: out, clip: { x: 0, y: 0, width: w, height: h } });
    if (v === 'retrato') await p.pdf({ path: 'capa-reis-imoveis-retrato.pdf', width: w + 'px', height: h + 'px', printBackground: true, pageRanges: '1' });
  }
  await b.close();
})();
